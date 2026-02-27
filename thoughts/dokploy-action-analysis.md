---
date: 2025-12-23T21:39:06+0000
researcher: Researcher
git_commit: N/A
branch: N/A
repository: dokploy-deploy-action (external)
topic: "Dokploy Deploy Action Repository Analysis"
tags: [research, dokploy, github-action, deployment, python, api-integration]
status: complete
last_updated: 2025-12-23
last_updated_by: Researcher
---

# Research: Dokploy Deploy Action Repository Analysis

**Date**: 2025-12-23T21:39:06+0000
**Researcher**: Researcher
**External Repository**: https://github.com/tarasyarema/dokploy-deploy-action
**Latest Commit**: 4d187f253a3a6c1b454f0983a64192d47f05ff98

## Research Question

Analyze the existing dokploy-deploy-action repository to understand:
1. Current functionality and implementation
2. Existing deployment types supported
3. Code structure and architecture
4. API integration patterns
5. Action inputs/outputs structure

## Summary

The dokploy-deploy-action is a dual-purpose deployment tool that operates both as a **GitHub Action** and a **standalone CLI tool (dokdeploy)**. Written in Python 3.11+, it integrates with the Dokploy platform to trigger and monitor application deployments. The v2.0 rewrite (from Bash to Python) specifically addresses critical race conditions that caused deployments to appear successful while still running, introducing deployment ID tracking, smart polling with exponential backoff, and comprehensive verification mechanisms.

**Key Features:**
- Deployment triggering with optional completion waiting
- Deployment ID-based tracking (fixes race conditions)
- Smart polling with exponential backoff (3s to 20s intervals)
- Application restart capabilities
- Comprehensive error handling and debug logging
- GitHub Actions log annotations support
- CLI tool for local deployments

## Detailed Findings

### 1. Current Functionality and Implementation

#### Core Deployment Flow

The deployment process follows a 4-phase approach implemented in `src/deploy.py`:

**Phase 1: Baseline Capture** (`deploy.py:68-83`)
- Retrieves current deployment state before triggering
- Captures timestamp of latest deployment
- Critical for identifying which deployment was triggered (prevents race conditions)

**Phase 2: Deployment Trigger** (`deploy.py:84-97`)
- Calls Dokploy API to initiate deployment
- Can exit immediately if `wait_for_completion=false`
- Issues warning when not waiting for verification

**Phase 3: Deployment Tracking** (`deploy.py:99-139`)
- Waits for new deployment to appear in API (up to 240 seconds)
- Tracks specific deployment by ID until completion
- Monitors state transitions: idle → running → done/error/cancelled
- Implements exponential backoff polling (3s, 5s, 10s, 15s, 20s intervals)
- Detects race conditions (instant "done" without "running" state)
- Default timeout: 10 minutes (suitable for source builds)

**Phase 4: Optional Restart** (`deploy.py:141-176`)
- Only executes if deployment succeeded and restart requested
- Stop → 5 second wait → Start → 10 second wait → verification
- Verifies application status is 'done' or 'running'

#### Race Condition Fix

The v2.0 rewrite specifically addresses the issue where checking `applicationStatus` would show "done" from a previous deployment. Implementation details in `src/deployment_tracker.py`:

**Baseline Timestamp Strategy** (`deployment_tracker.py:91-148`)
```python
def wait_for_new_deployment(self, application_id, baseline_timestamp, timeout=240):
    # Polls deployment.all API for deployments created after baseline
    # Identifies the triggered deployment by comparing timestamps
```

**Deployment ID Tracking** (`deployment_tracker.py:176-300`)
```python
def wait_for_completion(self, application_id, deployment_id, timeout=600):
    # Tracks specific deployment by ID
    # Detects instant "done" race condition (elapsed < 5s and not seen_running)
    # Monitors state transitions and warns on stuck states
```

**State Transition Detection** (`deployment_tracker.py:254-268`)
- Tracks if deployment ever entered "running" state
- Warns if deployment shows "done" within 5 seconds without running
- Prevents accepting stale status from previous deployments

#### CLI Tool Implementation

The `dokdeploy` CLI (`src/cli.py`) provides local deployment capabilities:

**Commands** (`cli.py:405-479`)
- `init`: Create configuration file template
- `list`: Display configured applications
- `deploy [apps] --all`: Deploy one or more applications
- `status [apps]`: Show application and deployment status
- `history [app]`: Display deployment history
- `config show|validate`: Configuration operations

**Configuration Management** (`src/config.py:41-196`)
- Loads settings from `~/.dokploy/deploy.yaml`
- Supports environment variable expansion (`$DOKPLOY_AUTH_TOKEN`)
- Per-app configuration with defaults inheritance
- Validation of all required fields

### 2. Existing Deployment Types Supported

The action supports deployment of Dokploy **applications** with the following characteristics:

#### Deployment Modes

**Fire-and-Forget Mode** (`wait_for_completion: false`)
- Triggers deployment and exits immediately
- No verification of success
- Use case: When verification isn't critical or done elsewhere
- Warning issued to user about lack of verification

**Verified Deployment Mode** (`wait_for_completion: true`) - **Recommended**
- Polls deployment status until completion
- Verifies triggered deployment actually started and completed
- Fails workflow if deployment errors, cancelled, or times out
- Timeout: 10 minutes (configurable)
- Use case: Ensure deployment succeeds before running tests or next steps

**Deployment with Restart** (`restart: true`)
- Only executes if deployment verification succeeds
- Sequence: Stop → Wait 5s → Start → Wait 10s → Verify running
- Use case: Applications that don't auto-restart after deployment
- Can be combined with verified deployment mode

#### Application Types

The action is application-type agnostic and works with any Dokploy application:
- Docker image deployments (pre-built)
- Source code builds (from git)
- Applications requiring restart after deployment
- Multiple applications (via GitHub matrix strategy or CLI `--all`)

**Matrix Strategy Support** (from `readme.md:133-157`)
```yaml
strategy:
  matrix:
    app:
      - { id: 'abc123', name: 'api' }
      - { id: 'def456', name: 'worker-1' }
```

### 3. Code Structure and Architecture

#### Directory Structure

```
dokploy-deploy-action/
├── src/                          # Python source code
│   ├── __init__.py               # Package marker
│   ├── cli.py                    # CLI commands (483 lines)
│   ├── config.py                 # Configuration management (196 lines)
│   ├── deploy.py                 # Main GitHub Action entry point (201 lines)
│   ├── deployment_tracker.py    # Deployment monitoring logic (347 lines)
│   ├── dokploy_client.py        # API client implementation (201 lines)
│   └── logger.py                 # Logging with GitHub Actions support (64 lines)
├── action.yml                    # GitHub Action definition
├── deploy.yaml.template          # CLI config template
├── dokdeploy                     # CLI executable script
├── requirements.txt              # Python dependencies (requests, pyyaml)
├── pyproject.toml                # Python project metadata
├── readme.md                     # User documentation
├── DEVELOPMENT.md                # Developer guide
├── test_local.sh.template        # Local testing template
└── .github/                      # GitHub workflows and funding
```

#### Module Responsibilities

**`deploy.py`** - Main Orchestrator
- Entry point for GitHub Action
- Environment variable parsing
- Phase orchestration (baseline, trigger, track, restart)
- Error handling and exit codes
- **Key Functions:**
  - `main()`: Orchestrates entire deployment process
  - `get_env()`: Environment variable helper
  - `str_to_bool()`: Boolean parsing

**`dokploy_client.py`** - API Client
- HTTP request handling with requests library
- Dokploy API endpoints abstraction
- Authentication via `x-api-key` header
- Error handling and response parsing
- **Key Methods:**
  - `deploy(application_id)`: Trigger deployment
  - `get_deployments(application_id)`: List deployments (newest first)
  - `get_application(application_id)`: Get app details
  - `stop/start(application_id)`: Control app state
  - `reload(application_id, app_name)`: Reload app

**`deployment_tracker.py`** - Monitoring Logic
- Race condition prevention
- Deployment ID identification
- Status polling with smart backoff
- State transition validation
- **Key Methods:**
  - `track_deployment()`: Complete tracking workflow
  - `wait_for_new_deployment()`: Find triggered deployment
  - `wait_for_completion()`: Poll until done/error/cancelled
  - `_find_deployment_after()`: Timestamp-based deployment lookup

**`config.py`** - Configuration Management
- YAML configuration loading
- Environment variable expansion
- Per-app settings with defaults
- Validation logic
- **Key Classes:**
  - `DokployConfig`: Main configuration container
  - `AppConfig`: Per-application settings

**`cli.py`** - CLI Interface
- Argparse-based command routing
- Multi-app deployment support
- Configuration operations
- Deployment history and status queries
- **Key Commands:**
  - `cmd_deploy()`: Deploy apps with CLI overrides
  - `cmd_status()`: Query app status
  - `cmd_history()`: Show deployment history
  - `cmd_config_*()`: Config operations

**`logger.py`** - Logging
- GitHub Actions annotations (`::error::`, `::warning::`, `::group::`)
- Debug mode support
- Structured logging (INFO, WARNING, ERROR, SUCCESS)
- Collapsible log groups

#### Error Handling

Custom exception hierarchy in `deployment_tracker.py`:
- `DeploymentNotFoundError`: Triggered deployment not found in API
- `DeploymentFailedError`: Deployment errored or cancelled
- `DeploymentTimeoutError`: Deployment exceeded timeout

API errors in `dokploy_client.py`:
- `DokployAPIError`: Wraps HTTP errors and network issues

Configuration errors in `config.py`:
- `ConfigError`: Invalid or missing configuration

### 4. API Integration Patterns

#### Dokploy API Endpoints Used

**Base URL Pattern**: `{dokploy_url}/api/{endpoint}`

**Authentication** (`dokploy_client.py:22-27`)
```python
self.session.headers.update({
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'x-api-key': api_key
})
```

**Endpoints** (`dokploy_client.py`):

1. **POST /api/application.deploy** (`dokploy_client.py:59-80`)
   - Triggers deployment
   - Body: `{"applicationId": "..."}`
   - Returns: 200 OK (no deployment ID in response)
   - Note: Must poll deployment.all to find new deployment

2. **GET /api/deployment.all?applicationId={id}** (`dokploy_client.py:82-112`)
   - Lists all deployments for application
   - Sorted by creation time (newest first)
   - Returns array of deployment objects:
     ```json
     {
       "deploymentId": "...",
       "status": "idle|running|done|error|cancelled",
       "createdAt": "ISO timestamp",
       "startedAt": "ISO timestamp",
       "finishedAt": "ISO timestamp",
       "errorMessage": "...",
       "logPath": "..."
     }
     ```

3. **GET /api/application.one?applicationId={id}** (`dokploy_client.py:114-136`)
   - Gets application details
   - Returns: `{"applicationStatus": "...", ...}`

4. **POST /api/application.stop** (`dokploy_client.py:162-180`)
   - Stops application
   - Body: `{"applicationId": "..."}`

5. **POST /api/application.start** (`dokploy_client.py:182-200`)
   - Starts application
   - Body: `{"applicationId": "..."}`

6. **POST /api/application.reload** (`dokploy_client.py:138-160`)
   - Reloads application
   - Body: `{"applicationId": "...", "appName": "..."}`

#### HTTP Request Pattern

**Request Flow** (`dokploy_client.py:29-57`)
```python
def _make_request(self, method, endpoint, **kwargs):
    # 1. Log request (debug mode)
    # 2. Make HTTP request via requests.Session
    # 3. Log response status and body (debug mode)
    # 4. Raise for HTTP errors (4xx, 5xx)
    # 5. Handle network exceptions
    # 6. Wrap errors in DokployAPIError
```

**Error Handling** (`dokploy_client.py:47-57`)
- HTTP errors: Includes response body in error message
- Network errors: Wraps connection/timeout issues
- All errors raised as `DokployAPIError`

#### Polling Strategy

**Exponential Backoff** (`deployment_tracker.py:212-222`)
```python
def get_poll_interval(count):
    if count < 2:   return 3   # 3s for first 2 polls
    elif count < 4: return 5   # 5s for polls 2-3
    elif count < 6: return 10  # 10s for polls 4-5
    elif count < 8: return 15  # 15s for polls 6-7
    else:           return 20  # 20s for subsequent polls
```

**Timeout Strategy**
- Wait for new deployment: 240 seconds (4 minutes)
- Wait for completion: 600 seconds (10 minutes) or remainder after finding deployment
- Total max: 10+ minutes for full deployment cycle

**Logging Frequency** (`deployment_tracker.py:129-138`)
- Debug log every 15 seconds with latest deployment info
- Info log on status changes
- Warning on stuck states (idle > 120s)

### 5. Action Inputs/Outputs Structure

#### GitHub Action Definition (`action.yml`)

**Metadata** (`action.yml:1-5`)
```yaml
name: 'Dokploy Deployment'
description: 'Trigger a Dokploy deployment'
branding:
  icon: 'upload-cloud'
  color: 'gray-dark'
```

**Inputs** (`action.yml:6-34`)

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `dokploy_url` | ✓ | - | Dokploy base URL (e.g., https://dokploy.example.com) |
| `auth_token` | ✓ | - | Dokploy authentication token (API key) |
| `application_id` | ✓ | - | Dokploy application ID |
| `application_name` | ✓ | - | Dokploy application name |
| `wait_for_completion` | ✗ | `false` | Wait for deployment to finish before completing action |
| `restart` | ✗ | `false` | Restart application after deployment completes |
| `debug` | ✗ | `false` | Enable debug logging (shows API requests/responses) |
| `skip_deploy` | ✗ | `false` | Skip deployment trigger (for testing) |

**Runtime** (`action.yml:35-64`)
```yaml
runs:
  using: "composite"
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'
        cache-dependency-path: ${{ github.action_path }}/requirements.txt

    - name: Install dependencies
      shell: bash
      run: pip install -q -r ${{ github.action_path }}/requirements.txt

    - name: Run Dokploy deployment
      shell: bash
      working-directory: ${{ github.action_path }}
      env:
        INPUT_DOKPLOY_URL: ${{ inputs.dokploy_url }}
        INPUT_AUTH_TOKEN: ${{ inputs.auth_token }}
        # ... other INPUT_* environment variables
        PYTHONUNBUFFERED: 1
      run: python3 -m src.deploy
```

**Environment Variable Mapping** (`deploy.py:46-52`)
- All GitHub Action inputs are exposed as `INPUT_<NAME>` environment variables
- Parsed by `get_env()` and `str_to_bool()` helpers
- Example: `wait_for_completion` input → `INPUT_WAIT_FOR_COMPLETION` env var

**Outputs**
- No explicit outputs defined
- Uses GitHub Actions exit codes:
  - `0`: Success
  - `1`: Deployment/API error
  - `130`: User cancelled (Ctrl+C)
- Logs deployment ID on success
- Annotates errors/warnings in GitHub Actions UI

#### CLI Configuration Structure

**Config File Format** (`deploy.yaml.template`, `config.py:125-162`)
```yaml
dokploy:
  url: https://app.dokploy.com
  auth_token: $DOKPLOY_AUTH_TOKEN  # or literal value

defaults:
  wait_for_completion: true
  restart: false
  debug: false

apps:
  my-app:
    id: your-app-id-here
    name: your-app-name-here
    # Optional overrides:
    # wait_for_completion: false
    # restart: true
    # debug: true
```

**CLI Arguments** (`cli.py:407-451`)
- Global: `-c/--config <path>` (default: `~/.dokploy/deploy.yaml`)
- Deploy: `deploy [apps...] --all --wait --no-wait --restart --debug`
- Status: `status [apps...] --debug`
- History: `history <app> -n/--limit <count> --debug`

**Configuration Loading** (`config.py:61-103`)
1. Parse YAML file
2. Expand environment variables in `auth_token` (if starts with `$`)
3. Load defaults
4. Load per-app configurations with defaults inheritance
5. Validate required fields
6. Raise `ConfigError` on validation failures

## Code References

### Core Implementation
- `src/deploy.py:38-197` - Main deployment orchestration
- `src/deployment_tracker.py:302-346` - Complete tracking workflow
- `src/dokploy_client.py:59-200` - API endpoints implementation
- `src/cli.py:69-261` - CLI deployment command
- `src/config.py:41-196` - Configuration management
- `src/logger.py:11-64` - Logging implementation

### Key Algorithms
- `src/deployment_tracker.py:91-148` - New deployment detection
- `src/deployment_tracker.py:176-300` - Deployment completion tracking
- `src/deployment_tracker.py:212-222` - Exponential backoff calculation
- `src/deployment_tracker.py:254-268` - Race condition detection
- `src/config.py:76-80` - Environment variable expansion

### GitHub Action Integration
- `action.yml:35-64` - Composite action definition
- `src/logger.py:27-43` - GitHub Actions annotations
- `src/logger.py:45-57` - Log group context manager

## Architecture Patterns

### Design Patterns Used

**1. Strategy Pattern** - Deployment Modes
- Different behaviors based on `wait_for_completion` flag
- Encapsulated in deployment tracker logic

**2. Template Method Pattern** - Deployment Flow
- `track_deployment()` defines algorithm structure
- Delegates to `wait_for_new_deployment()` and `wait_for_completion()`

**3. Builder Pattern** - Configuration
- `AppConfig` merges per-app settings with defaults
- Progressive validation during construction

**4. Singleton Pattern** - HTTP Session
- `requests.Session` in `DokployClient` reuses connections
- Headers configured once

**5. Context Manager Pattern** - Log Groups
- `LogGroup` class for GitHub Actions collapsible logs
- Automatic cleanup with `__exit__`

### Architecture Characteristics

**Separation of Concerns**
- API client doesn't know about deployment tracking
- Deployment tracker doesn't know about GitHub Actions
- Logger supports both CLI and GitHub Actions

**Defensive Programming**
- Comprehensive error handling at all levels
- Custom exceptions for specific failure modes
- Timestamp parsing with fallbacks
- Debug logging for troubleshooting

**Composability**
- CLI and GitHub Action share core logic
- Deployment tracker can be used standalone
- API client is generic and reusable

**Testability**
- Pure functions for timestamp parsing, boolean conversion
- Dependency injection (client to tracker, logger to all)
- Template script for local testing

## Dependencies

**Python Requirements** (`requirements.txt`, `pyproject.toml`)
```
requests>=2.31.0   # HTTP client
pyyaml>=6.0.0      # YAML config parsing
```

**Python Version**: 3.11+ (specified in `action.yml` and `pyproject.toml`)

**GitHub Actions Dependencies**
- `actions/setup-python@v5` - Python environment setup
- Pip caching via `cache: 'pip'`

## Notable Implementation Details

### Race Condition Prevention

The v2.0 rewrite's primary innovation is deployment ID tracking:

**Before (v1.x Bash)** (`readme.md:353-361`)
- Checked `applicationStatus` field (wrong field, race condition prone)
- 60-second initial wait (too long, missed state changes)
- No deployment ID tracking
- Instant "done" accepted as success

**After (v2.0 Python)** (`readme.md:362-370`)
- Tracks specific deployment by ID
- 3-second initial poll (catches deployment quickly)
- Detects race conditions with warning
- Smart polling with exponential backoff
- Restart only after verified deployment

### Debug Mode Capabilities

When `debug: true` is set (`logger.py:17-20`, `dokploy_client.py:32-42`):
- Full API request URLs logged
- Request bodies logged (JSON)
- Response status codes logged
- Response bodies logged (truncated to 500 chars)
- Detailed state transition logs
- Timestamp comparisons for deployment detection

### Error Messages

The implementation provides detailed, actionable error messages:

**Deployment Not Found** (`deploy.py:112-119`)
```
The deployment was triggered but never appeared in the deployment list.
This could indicate:
  1. The application doesn't exist or ID is wrong
  2. Dokploy is experiencing issues
  3. The deployment was queued but hasn't started
```

**Deployment Timeout** (`deploy.py:130-139`)
```
Deployment did not complete within the timeout period.
This could mean:
  1. The build is taking longer than expected (increase timeout)
  2. The deployment is stuck
  3. Dokploy is experiencing issues
```

**Race Condition Warning** (`deployment_tracker.py:263-267`)
```
Deployment marked 'done' after only {elapsed}s without entering 'running' state.
This might be a race condition.
```

## Open Questions

None - the research comprehensively covers all requested areas. The repository is well-documented with clear implementation patterns and thorough error handling.
