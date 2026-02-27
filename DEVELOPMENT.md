# Local Development Guide

This project can be used in two ways:
1. **GitHub Action** - Automated deployments in CI/CD
2. **CLI Tool (dokdeploy)** - Deploy from your local machine

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Or with pip
pip install uv
```

---

# Using the CLI Tool (dokdeploy)

The `dokdeploy` CLI lets you deploy applications to Dokploy from your local machine or any CI system.

## Quick Start

### 1. Install Dependencies

```bash
# Clone and navigate to repo
cd dokploy-deploy-action

# Sync dependencies with uv (creates .venv and installs packages)
uv sync
```

### 2. Initialize Configuration

```bash
# Create config file (using uv run to use the virtual environment)
uv run uv run ./dokdeploy init

# This creates ~/.dokploy/deploy.yaml
# Edit it with your settings:
vim ~/.dokploy/deploy.yaml
```

**Note**: Use `uv run uv run ./dokdeploy` to run commands with the virtual environment, or activate it first:

```bash
# Option 1: Use uv run (recommended)
uv run uv run ./dokdeploy <command>

# Option 2: Activate venv manually
source .venv/bin/activate  # or: .venv\Scripts\activate on Windows
uv run ./dokdeploy <command>
```

Or copy the template:

```bash
cp deploy.yaml.template ~/.dokploy/deploy.yaml
vim ~/.dokploy/deploy.yaml
```

### 3. Configure Your Apps

Edit `~/.dokploy/deploy.yaml`:

```yaml
dokploy:
  url: https://app.dokploy.com
  auth_token: $DOKPLOY_AUTH_TOKEN  # or paste token directly

defaults:
  wait_for_completion: true
  restart: false

apps:
  api:
    id: 7YIYBwVKk_V3lUJKp37Va
    name: qaforme-api-gp9he8

  worker:
    id: rfDCKRDJMlfCxX_nZ2qIq
    name: qaforme-worker-wwmm7o
```

### 4. Deploy!

```bash
# List your apps
uv run uv run ./dokdeploy list

# Deploy one app
uv run uv run ./dokdeploy deploy api

# Deploy multiple apps
uv run uv run ./dokdeploy deploy api worker

# Deploy all apps (like GitHub matrix!)
uv run uv run ./dokdeploy deploy --all

# Check status
uv run uv run ./dokdeploy status api

# View deployment history
uv run uv run ./dokdeploy history api
```

## CLI Commands

### `dokdeploy init`

Create configuration file template.

```bash
uv run uv run ./dokdeploy init                    # Create ~/.dokploy/deploy.yaml
uv run uv run ./dokdeploy init -f                 # Force overwrite existing
uv run uv run ./dokdeploy -c custom.yaml init     # Custom path
```

### `dokdeploy list`

List all configured applications.

```bash
uv run uv run ./dokdeploy list

# Output:
# Dokploy URL: https://app.dokploy.com
# Config file: /Users/you/.dokploy/deploy.yaml
#
# Configured applications (3):
#
#   api
#     ID:      7YIYBwVKk_V3lUJKp37Va
#     Name:    qaforme-api-gp9he8
#     Wait:    True
#     Restart: False
```

### `dokdeploy deploy`

Deploy one or more applications.

```bash
# Deploy specific apps
uv run uv run ./dokdeploy deploy api
uv run uv run ./dokdeploy deploy api worker frontend

# Deploy all configured apps
uv run uv run ./dokdeploy deploy --all

# Override settings
uv run uv run ./dokdeploy deploy api --wait       # Force wait for completion
uv run uv run ./dokdeploy deploy api --no-wait    # Fire and forget
uv run uv run ./dokdeploy deploy api --restart    # Restart after deploy
uv run uv run ./dokdeploy deploy api --debug      # Enable debug logging

# Examples matching your GitHub workflow:
uv run uv run ./dokdeploy deploy --all --restart  # Deploy all with restart (like your matrix)
```

### `dokdeploy status`

Show current application status.

```bash
uv run ./dokdeploy status api
uv run ./dokdeploy status api worker

# Output:
# api (qaforme-api-gp9he8):
#   ID: 7YIYBwVKk_V3lUJKp37Va
#   Status: done
#   Latest deployment:
#     ID:       abc123xyz
#     Status:   done
#     Created:  2025-10-30T12:40:03.127Z
#     Finished: 2025-10-30T12:40:45.735Z
```

### `dokdeploy history`

Show deployment history for an app.

```bash
uv run ./dokdeploy history api
uv run ./dokdeploy history api -n 20       # Show last 20 deployments

# Output:
# Deployment history for api (qaforme-api-gp9he8):
#
#   [1] FRBrr23WR9cvkYXH62PHw
#       Status:   done
#       Created:  2025-10-30T12:40:03.127Z
#       Started:  2025-10-30T12:40:03.127Z
#       Finished: 2025-10-30T12:40:45.735Z
```

### `dokdeploy config`

Configuration operations.

```bash
# Show current configuration
uv run ./dokdeploy config show

# Validate configuration
uv run ./dokdeploy config validate

# Use custom config file
uv run ./dokdeploy -c staging.yaml config show
uv run ./dokdeploy -c staging.yaml deploy --all
```

## Advanced Usage

### Multiple Environments

Create separate config files for different environments:

```bash
# Production
~/.dokploy/deploy.yaml

# Staging
~/.dokploy/deploy.staging.yaml

# Use staging config
uv run ./dokdeploy -c ~/.dokploy/deploy.staging.yaml deploy --all
```

### Environment Variable Token

Keep your API token secure using environment variables:

```yaml
# In deploy.yaml
dokploy:
  auth_token: $DOKPLOY_AUTH_TOKEN
```

```bash
# Set in your shell
export DOKPLOY_AUTH_TOKEN="your-token-here"

# Or use .env file (add to .gitignore!)
echo "export DOKPLOY_AUTH_TOKEN=your-token" >> ~/.dokploy/.env
source ~/.dokploy/.env

uv run ./dokdeploy deploy api
```

### Scripting Deployments

```bash
#!/bin/bash
# deploy-all.sh

set -e  # Exit on error

echo "Deploying all applications..."

uv run ./dokdeploy deploy --all --wait

if [ $? -eq 0 ]; then
    echo "✅ All deployments successful"
    # Run tests
    npm run test:e2e
else
    echo "❌ Deployment failed"
    exit 1
fi
```

### Install Globally (Optional)

Make `dokdeploy` available system-wide:

```bash
# Install as a tool with uv
uv tool install .

# Now use it anywhere
dokdeploy list
dokdeploy deploy api

# Or add to PATH
echo 'export PATH="$PATH:/path/to/dokploy-deploy-action"' >> ~/.zshrc
source ~/.zshrc
```

## CLI Development Workflow

When working on the CLI:

```bash
# Make changes to src/cli.py, src/config.py, etc.

# Test locally
uv run ./dokdeploy deploy api --debug

# Check syntax
python3 -m py_compile src/*.py

# Test all commands
uv run ./dokdeploy list
uv run ./dokdeploy status api
uv run ./dokdeploy history api
```

---

# Testing the GitHub Action Locally

## Setup

### 1. Install Dependencies

```bash
# Install dependencies using uv
uv pip install -r requirements.txt

# Or create a virtual environment with uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### 2. Get Your Dokploy Credentials

You need:
- **Dokploy URL**: Your Dokploy instance URL (e.g., `https://app.dokploy.com`)
- **API Token**: Generate from Dokploy dashboard → Settings → API Tokens
- **Application ID**: Find in Dokploy dashboard → Your App → URL or settings
- **Application Name**: The name of your application

### 3. Create Test Script

Create a file `test_local.sh` (already in .gitignore):

```bash
#!/bin/bash

# Dokploy Configuration
export INPUT_DOKPLOY_URL="https://app.dokploy.com"
export INPUT_AUTH_TOKEN="your-api-token-here"
export INPUT_APPLICATION_ID="your-app-id-here"
export INPUT_APPLICATION_NAME="your-app-name"

# Action Configuration
export INPUT_WAIT_FOR_COMPLETION="true"
export INPUT_RESTART="false"
export INPUT_SKIP_DEPLOY="false"
export INPUT_DEBUG="true"  # Enable debug logging

# Run the script
cd src
python3 deploy.py
```

Make it executable:
```bash
chmod +x test_local.sh
```

### 4. Run Locally

```bash
# Option 1: Using the test script
./test_local.sh

# Option 2: Export variables and run directly
export INPUT_DOKPLOY_URL="https://app.dokploy.com"
export INPUT_AUTH_TOKEN="your-token"
export INPUT_APPLICATION_ID="abc123"
export INPUT_APPLICATION_NAME="my-app"
export INPUT_WAIT_FOR_COMPLETION="true"
export INPUT_DEBUG="true"

cd src && python3 deploy.py
```

## Testing Different Scenarios

### Test 1: Fire and Forget (No Wait)

```bash
export INPUT_WAIT_FOR_COMPLETION="false"
export INPUT_RESTART="false"
cd src && python3 deploy.py
```

Expected: Triggers deployment, exits immediately with warning.

### Test 2: Wait for Completion

```bash
export INPUT_WAIT_FOR_COMPLETION="true"
export INPUT_RESTART="false"
cd src && python3 deploy.py
```

Expected: Triggers deployment, tracks progress, waits until done.

### Test 3: Wait + Restart

```bash
export INPUT_WAIT_FOR_COMPLETION="true"
export INPUT_RESTART="true"
cd src && python3 deploy.py
```

Expected: Deploys, waits for completion, then restarts application.

### Test 4: Skip Deploy (Test Restart Only)

```bash
export INPUT_WAIT_FOR_COMPLETION="false"
export INPUT_RESTART="true"
export INPUT_SKIP_DEPLOY="true"
cd src && python3 deploy.py
```

Expected: Skips deployment, just restarts the application.

### Test 5: Debug Mode

```bash
export INPUT_DEBUG="true"
export INPUT_WAIT_FOR_COMPLETION="true"
cd src && python3 deploy.py
```

Expected: Shows full API request/response details.

## Development Workflow

### 1. Make Changes

Edit files in `src/`:
- `logger.py` - Logging configuration
- `dokploy_client.py` - API client
- `deployment_tracker.py` - Deployment polling logic
- `deploy.py` - Main orchestration

### 2. Check Syntax

```bash
# Check for syntax errors
python3 -m py_compile src/*.py

# Or use ruff (fast Python linter)
uv pip install ruff
ruff check src/
```

### 3. Test Locally

```bash
# Test with a safe application (non-production)
export INPUT_APPLICATION_ID="test-app-id"
export INPUT_DEBUG="true"
./test_local.sh
```

### 4. Test in GitHub Actions

Push to a branch and reference it in your workflow:

```yaml
- uses: tarasyarema/dokploy-deploy-action@your-branch-name
  with:
    dokploy_url: ${{ secrets.DOKPLOY_URL }}
    # ... other inputs
```

## Debugging Tips

### Enable Full Debug Logging

```bash
export INPUT_DEBUG="true"
```

This shows:
- Full API request URLs
- Request bodies
- Response status codes
- Response bodies (truncated to 500 chars)
- State transitions

### Test API Endpoints Directly

```bash
# Test authentication
curl -X GET \
  "https://app.dokploy.com/api/application/one?applicationId=YOUR_APP_ID" \
  -H "x-api-key: YOUR_API_TOKEN"

# Test getting deployments
curl -X GET \
  "https://app.dokploy.com/api/deployment/all?applicationId=YOUR_APP_ID" \
  -H "x-api-key: YOUR_API_TOKEN"

# Trigger deployment
curl -X POST \
  "https://app.dokploy.com/api/application/deploy" \
  -H "x-api-key: YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"applicationId": "YOUR_APP_ID"}'
```

### Check Exit Codes

```bash
cd src && python3 deploy.py
echo "Exit code: $?"
# 0 = success
# 1 = error
# 130 = cancelled (Ctrl+C)
```

### Mock API Responses (Advanced)

For testing without hitting real Dokploy API, you can modify `dokploy_client.py` to use mock responses:

```python
# In dokploy_client.py, add:
if os.getenv('MOCK_API') == 'true':
    return self._mock_response(endpoint)
```

## Common Issues

### ImportError: No module named 'requests'

Solution:
```bash
uv pip install -r requirements.txt
```

### "Missing required environment variable"

Solution: Ensure all INPUT_* variables are set:
```bash
export INPUT_DOKPLOY_URL="..."
export INPUT_AUTH_TOKEN="..."
export INPUT_APPLICATION_ID="..."
export INPUT_APPLICATION_NAME="..."
```

### "Deployment not found"

Causes:
- Wrong application ID
- API token doesn't have access
- Dokploy is down

Debug:
```bash
export INPUT_DEBUG="true"
# Check the API response in logs
```

## Code Style

This project follows standard Python conventions:

```bash
# Install dev tools
uv pip install ruff black mypy

# Format code
black src/

# Lint
ruff check src/

# Type check (optional, no type hints yet)
mypy src/
```

## Project Structure

```
dokploy-deploy-action/
├── src/
│   ├── deploy.py              # Main entry point
│   ├── dokploy_client.py      # API client
│   ├── deployment_tracker.py  # Polling & verification
│   └── logger.py              # Logging setup
├── action.yml                 # GitHub Action definition
├── requirements.txt           # Python dependencies
├── DEVELOPMENT.md            # This file
└── readme.md                 # User documentation
```

## Testing Checklist

Before pushing changes:

- [ ] Syntax check: `python3 -m py_compile src/*.py`
- [ ] Test fire-and-forget: `INPUT_WAIT_FOR_COMPLETION=false`
- [ ] Test with wait: `INPUT_WAIT_FOR_COMPLETION=true`
- [ ] Test with restart: `INPUT_RESTART=true`
- [ ] Test debug mode: `INPUT_DEBUG=true`
- [ ] Test with invalid credentials (should fail gracefully)
- [ ] Test with invalid app ID (should fail gracefully)
- [ ] Update documentation if needed

## Performance Testing

Test with different scenarios:

```bash
# Fast deployment (pre-built image)
time ./test_local.sh  # Should complete in 30-60s

# Slow deployment (source build)
time ./test_local.sh  # Could take 2-5 minutes

# Multiple parallel deployments (simulate matrix)
./test_local.sh & ./test_local.sh & ./test_local.sh &
wait
```

## Need Help?

- Check the [main README](readme.md) for usage examples
- Enable `INPUT_DEBUG=true` for detailed logs
- Check [Dokploy API docs](https://app.dokploy.com/swagger)
- Open an issue on GitHub
