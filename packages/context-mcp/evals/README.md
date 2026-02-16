# /discover Command Evaluation Framework

Pure Python evaluation framework for testing `/discover` efficacy using [DeepEval](https://deepeval.com/).

## What This Evaluates

The `/discover` command is a Claude Code slash command that:
1. Explores a codebase to understand task requirements
2. Curates a focused selection of relevant files/slices
3. Crafts a self-contained handoff prompt for implementation

This framework lets you:
- **Measure** how well /discover selects context (precision, recall)
- **Evaluate** handoff prompt quality using LLM-as-judge (G-Eval)
- **Track** performance (timing, tokens, API calls)
- **Compare** before/after when making changes to the /discover prompt

## Architecture

```
evals/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── pyproject.toml               # Python project config
├── test_cases/                  # Test case definitions (YAML)
│   ├── case_001_auth.yaml       # Auth feature task
│   ├── case_002_refactor.yaml   # Refactoring task
│   └── case_003_api_endpoint.yaml
├── fixtures/                    # Test codebases (optional)
│   └── sample_project/
├── discover_evals/
│   ├── __init__.py
│   ├── runner.py               # Runs /discover via Claude API
│   ├── metrics.py              # Custom G-Eval metrics
│   ├── test_discover.py        # DeepEval test suite
│   ├── report.py               # Generates comparison reports
│   └── cli.py                  # Command-line interface
└── results/                     # Stored evaluation results
    └── {case_id}_{run_id}.json
```

## Quick Start

```bash
cd packages/context-mcp/evals
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set API keys
export ANTHROPIC_API_KEY=your-key
export OPENAI_API_KEY=your-key  # For deepeval's LLM-as-judge

# List available test cases
python -m discover_evals.cli list-cases

# Run with mock tools (fast, for testing the framework)
python -m discover_evals.cli run case_001_auth --tag baseline --mock

# Run with real Claude API (slower, real evaluation)
python -m discover_evals.cli run case_001_auth --tag baseline

# Run all test cases
python -m discover_evals.cli run-all --tag baseline

# Compare two runs
python -m discover_evals.cli compare baseline experiment
```

### Using DeepEval Directly

```bash
# Run single test
deepeval test run discover_evals/test_discover.py -k "test_auth"

# Run all tests
deepeval test run discover_evals/test_discover.py

# View results in browser
deepeval view
```

## Evaluation Metrics

### 1. Context Selection Quality
- **File Recall**: % of ground truth files that were selected
- **File Precision**: % of selected files that are in ground truth
- **Slice Efficiency**: Token savings from using slices vs full files

### 2. Handoff Prompt Quality (G-Eval)
- **Architecture Clarity**: Accurate description of codebase structure
- **Relationship Mapping**: Dependencies and data flows explained
- **Task Actionability**: Could implementation proceed from this prompt?
- **Completeness**: All required sections present

### 3. Performance
- **Total Duration**: End-to-end time
- **API Calls**: Number of MCP tool calls made
- **Token Usage**: Input/output tokens consumed

## Test Case Format

```yaml
id: case_001_auth
name: Add JWT Authentication
task: |
  Add user authentication with JWT tokens to the API.
  Users should be able to login with email/password and receive a token.

fixture: sample_project

ground_truth:
  # Files that MUST be in the selection
  required_files:
    - src/routes/auth.ts
    - src/models/user.ts
    - src/middleware/auth.ts

  # Files that SHOULD be in the selection
  recommended_files:
    - src/config/jwt.ts
    - src/services/token.ts

  # Topics the architecture section must cover
  architecture_topics:
    - authentication flow
    - token validation
    - user model

  # Expected relationships in handoff
  expected_relationships:
    - "User → Token"
    - "AuthMiddleware → TokenService"

# Scoring thresholds
thresholds:
  file_recall: 0.8      # Must find 80% of required files
  architecture: 0.7      # G-Eval score threshold
  actionability: 0.7
```

## Comparing Runs

```bash
# Run baseline
python -m discover_evals.runner --tag baseline-v1

# Make changes to /discover command...

# Run comparison
python -m discover_evals.runner --tag experiment-v2

# Generate comparison report
python -m discover_evals.report baseline-v1 experiment-v2
```

## Typical Workflow

### 1. Establish Baseline

```bash
# Run all tests with current /discover prompt
python -m discover_evals.cli run-all --tag baseline-v1
```

### 2. Make Changes

Edit `.claude/commands/discover.md` to improve the prompt.

### 3. Run Experiment

```bash
# Run same tests with modified prompt
python -m discover_evals.cli run-all --tag experiment-v1
```

### 4. Compare Results

```bash
# See what improved/regressed
python -m discover_evals.cli compare baseline-v1 experiment-v1

# Or generate markdown report
python -m discover_evals.report baseline-v1 experiment-v1 --format markdown --output report.md
```

### 5. View History

```bash
# See all past runs
python -m discover_evals.cli history
```

## Custom Metrics

The framework uses these evaluation metrics:

### LLM-as-Judge (G-Eval)

| Metric | What It Evaluates |
|--------|-------------------|
| `ContextRelevanceMetric` | Are selected files/slices relevant to the task? |
| `ArchitectureClarityMetric` | Does architecture section clearly explain the codebase? |
| `RelationshipMappingMetric` | Are dependencies and data flows mapped correctly? |
| `TaskActionabilityMetric` | Could someone implement from this prompt? |
| `HandoffCompletenessMetric` | Are all required sections present? |

### Deterministic Metrics

| Metric | What It Evaluates |
|--------|-------------------|
| `FileRecallMetric` | What % of expected files were selected? |
| `FilePrecisionMetric` | What % of selected files were expected? |
| `MCPToolUsageMetric` | What % of tool calls used MCP tools vs default tools? |

### MCP Tool Usage Metric

The `MCPToolUsageMetric` measures whether /discover properly uses the context-helper-synapse MCP tools instead of falling back to default Claude Code tools.

**MCP tools (good):**
- `file_search` - FTS5/BM25 indexed search
- `get_file_tree` - Workspace structure
- `read_file` - MCP file reading
- `manage_selection` - Context curation
- `workspace_context` - Token counts and selection state
- `get_code_structure` - Tree-sitter analysis
- `semantic_search` - Embedding-based search

**Default tools (suboptimal):**
- `Read` - Basic file reading
- `Grep` - Regex search
- `Glob` - File pattern matching
- `Bash` - Especially with grep/find/cat commands

A score of 0.7+ (70% MCP usage) is considered passing.

## CI Integration

Add to GitHub Actions:

```yaml
- name: Setup Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.11'

- name: Run discover evals
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    DISCOVER_EVAL_MOCK: "false"  # Use real API
  run: |
    cd packages/context-mcp/evals
    pip install -r requirements.txt
    deepeval test run discover_evals/test_discover.py
```

## Adding New Test Cases

1. Create a YAML file in `test_cases/`:

```yaml
id: case_004_my_task
name: My New Test Case
description: What this tests

task: |
  The task description that will be sent to /discover

fixture: sample_project  # or 'synapse' for this repo

ground_truth:
  required_files:
    - path/to/required.ts
  recommended_files:
    - path/to/nice-to-have.ts
  architecture_topics:
    - key concept
  expected_relationships:
    - "A -> B"

thresholds:
  file_recall: 0.8
  context_relevance: 0.7
```

2. Add a test in `test_discover.py`:

```python
@pytest.mark.parametrize("case_id", ["case_004_my_task"])
def test_my_task_discovery(self, runner, case_id):
    # ... same pattern as other tests
```

## Debugging

### View Raw Results

```bash
# Results are JSON files
cat results/case_001_auth_*.json | python -m json.tool
```

### Check Handoff Prompt

```python
from discover_evals.runner import run_discovery

result = run_discovery(
    task="Add authentication",
    test_case_id="debug",
    mock_tools=False,
)
print(result.handoff_prompt)
```

### Run with Verbose Output

```bash
deepeval test run discover_evals/test_discover.py -v --capture=no
```
