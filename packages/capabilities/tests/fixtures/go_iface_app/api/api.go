package api

import "github.com/example/ifacesvc/store"

// GetThing is the route handler; it dispatches through the interface.
func GetThing(repo store.Repo, id int) store.Thing {
	return repo.Fetch(id)
}

// Register mounts the route.
func Register() {
	handle("GET /things/{id}", GetThing)
}

func handle(pattern string, h func(store.Repo, int) store.Thing) {}
