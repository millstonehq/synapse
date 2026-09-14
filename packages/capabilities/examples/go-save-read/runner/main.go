package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

type plan struct {
	Scenarios []scenario `json:"scenarios"`
}
type scenario struct {
	ID    string `json:"id"`
	Steps []step `json:"steps"`
}
type step struct {
	Transition string    `json:"transition"`
	Commands   []command `json:"commands"`
}
type command struct {
	Op           string            `json:"op"`
	ID           string            `json:"id"`
	Mode         string            `json:"mode"`
	Method       string            `json:"method"`
	Path         string            `json:"path"`
	Text         string            `json:"text"`
	Form         map[string]string `json:"form"`
	ExpectStatus int               `json:"expect_status"`
}
type result struct {
	ID         string    `json:"id"`
	Status     string    `json:"status"`
	Assertions []string  `json:"assertions"`
	Requests   []request `json:"observed_requests"`
}
type request struct {
	Step    string `json:"step"`
	Surface string `json:"surface"`
}

func main() {
	planBytes, err := os.ReadFile(os.Getenv("CAPCOV_FLOW_PLAN"))
	must(err)
	var p plan
	must(json.Unmarshal(planBytes, &p))
	sum := sha256.Sum256(planBytes)
	buildDir, err := os.MkdirTemp("", "capcov-go-save-read-")
	must(err)
	defer os.RemoveAll(buildDir)
	server := buildDir + "/server"
	build := exec.Command("go", "build", "-o", server, ".")
	build.Dir = os.Getenv("CAPCOV_FIXTURE_ROOT")
	build.Stdout = os.Stderr
	build.Stderr = os.Stderr
	must(build.Run())
	results := make([]result, 0, len(p.Scenarios))
	allPassed := true
	for _, scenario := range p.Scenarios {
		r := runScenario(server, scenario)
		if r.Status != "passed" {
			allPassed = false
		}
		results = append(results, r)
	}
	status := "passed"
	if !allPassed {
		status = "failed"
	}
	out := map[string]any{"nonce": os.Getenv("CAPCOV_FLOW_NONCE"), "plan_sha256": hex.EncodeToString(sum[:]), "status": status, "execution_scope": "full", "mounted_surfaces": []string{"http:GET /notes", "http:POST /notes/create"}, "scenarios": results, "assurance": "real-go-http-subprocess"}
	b, err := json.Marshal(out)
	must(err)
	must(os.WriteFile(os.Getenv("CAPCOV_FLOW_OUT"), b, 0o600))
}

func runScenario(server string, s scenario) result {
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	must(err)
	port := listener.Addr().(*net.TCPAddr).Port
	must(listener.Close())
	cmd := exec.Command(server)
	cmd.Env = append(os.Environ(), "PORT="+strconv.Itoa(port))
	cmd.Stdout = os.Stderr
	cmd.Stderr = os.Stderr
	must(cmd.Start())
	defer func() { _ = cmd.Process.Kill(); _, _ = cmd.Process.Wait() }()
	base := "http://127.0.0.1:" + strconv.Itoa(port)
	ready := false
	for i := 0; i < 400; i++ {
		if resp, e := http.Get(base + "/notes"); e == nil {
			_ = resp.Body.Close()
			ready = true
			break
		}
		time.Sleep(25 * time.Millisecond)
	}
	r := result{ID: s.ID, Status: "passed", Assertions: []string{}, Requests: []request{}}
	if !ready {
		r.Status = "failed"
		return r
	}
	for i, st := range s.Steps {
		for _, c := range st.Commands {
			if c.Op != "assert" || c.Mode != "http" {
				r.Status = "failed"
				continue
			}
			var body io.Reader
			if c.Method == "POST" {
				vals := url.Values{}
				for k, v := range c.Form {
					vals.Set(k, v)
				}
				body = strings.NewReader(vals.Encode())
			}
			req, e := http.NewRequest(c.Method, base+c.Path, body)
			if e != nil {
				r.Status = "failed"
				continue
			}
			if c.Method == "POST" {
				req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
			}
			resp, e := http.DefaultClient.Do(req)
			if e != nil {
				r.Status = "failed"
				continue
			}
			data, _ := io.ReadAll(resp.Body)
			_ = resp.Body.Close()
			r.Requests = append(r.Requests, request{Step: fmt.Sprintf("%d:%s", i, st.Transition), Surface: "http:" + c.Method + " " + c.Path})
			if resp.StatusCode == c.ExpectStatus && bytes.Contains(data, []byte(c.Text)) {
				r.Assertions = append(r.Assertions, fmt.Sprintf("%d:%s:%s", i, st.Transition, c.ID))
			} else {
				r.Status = "failed"
			}
		}
	}
	return r
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
