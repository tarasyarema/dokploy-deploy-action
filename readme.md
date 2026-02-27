# Dokploy Deployment Tool

Deploy **applications** and **Docker Compose services** to Dokploy from **GitHub Actions** or the **command line**.

This tool:
- 🎯 **GitHub Action** - Automated deployments in your CI/CD pipeline
- 💻 **CLI Tool (`dokdeploy`)** - Deploy from your local machine
- 📦 **Application & Compose Support** - Deploy both application and Docker Compose services
- ✅ **Proper verification** - Ensures deployments actually complete (no more race conditions!)

## What's New (v2.0)

This action has been completely rewritten in Python to fix critical race conditions that caused deployments to appear successful while the old version kept running. Key improvements:

- **Deployment tracking by ID**: Tracks the specific deployment triggered, not just application status
- **Race condition fixes**: Detects when deployment hasn't started yet (instant "done" bug)
- **Smart polling**: Exponential backoff and state transition detection
- **Better error messages**: Clear explanations when things go wrong
- **Debug mode**: See full API requests/responses for troubleshooting

## Inputs

### `dokploy_url`

**Required** Dokploy dashboard URL (this should have the Dokploy API accessible at /api) - no trailing slash.

Example: `https://server.example.com` or `https://app.dokploy.com`

### `auth_token`

**Required** The Dokploy authentication token (API key).

### `application_id`

**Required** The Dokploy application ID.

### `application_name`

**Required** The Dokploy application name.

### `deployment_type`

**Optional** The type of deployment: `application` or `compose`. Default: `application`.

When deploying a Docker Compose service, set this to `compose` and provide `compose_id` and `compose_name` instead of `application_id` and `application_name`.

### `compose_id`

**Optional** The Dokploy compose service ID. Required when `deployment_type` is `compose`.

### `compose_name`

**Optional** The Dokploy compose service name. Required when `deployment_type` is `compose`.

**Note**: For application deployments (the default), use `application_id` and `application_name` instead.

### `wait_for_completion`

**Optional** Wait for the deployment to finish before completing the action. Default: `false`.

When `true`:
- Polls deployment status every 3-20 seconds with smart backoff
- Verifies the triggered deployment actually started and completed
- Fails if deployment errors, is cancelled, or times out
- Timeout: 10 minutes (suitable for source builds)

**⚠️ Recommended: Set to `true`** to ensure deployments succeed before continuing your workflow (e.g., running tests).

### `restart`

**Optional** Restart the Dokploy application after deployment completes. Default: `false`.

When `true`:
- Only executes if deployment verification succeeds
- Stops the application, waits 5 seconds, then starts it
- Verifies application is running after restart

**Note**: Only needed if Dokploy doesn't automatically restart after deployment.

### `debug`

**Optional** Enable debug logging to see full API requests and responses. Default: `false`.

Useful for troubleshooting deployment issues.

## All Available Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `dokploy_url` | Yes | - | Dokploy dashboard URL |
| `auth_token` | Yes | - | Dokploy authentication token |
| `deployment_type` | No | `application` | Deployment type: `application` or `compose` |
| `application_id` | Conditional | - | Application ID (required for application deployments) |
| `application_name` | Conditional | - | Application name (required for application deployments) |
| `compose_id` | Conditional | - | Compose ID (required for compose deployments) |
| `compose_name` | Conditional | - | Compose name (required for compose deployments) |
| `wait_for_completion` | No | `false` | Wait for deployment to finish |
| `restart` | No | `false` | Restart after deployment |
| `debug` | No | `false` | Enable debug logging |
| `skip_deploy` | No | `false` | Skip deployment trigger (testing) |

## Usage

### Basic Usage (Fire and Forget)

Triggers deployment without waiting for completion:

```yaml
name: Deploy to Dokploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Dokploy deployment
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: ${{ secrets.DOKPLOY_APP_ID }}
          application_name: my-app
```

**⚠️ Warning**: Without `wait_for_completion: true`, the action exits immediately and **doesn't verify** the deployment succeeded. The old version might keep running.

### Recommended Usage (With Verification)

Wait for deployment to complete before continuing:

```yaml
      - name: Deploy to Dokploy
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: https://app.dokploy.com
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: abc123
          application_name: my-app
          wait_for_completion: true
```

This ensures:
- Deployment actually starts and completes
- Errors are caught and fail the workflow
- Next steps run against the new version

### With Restart (Force New Version)

For apps that need explicit restart:

```yaml
      - name: Deploy and restart
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: ${{ secrets.DOKPLOY_APP_ID }}
          application_name: my-app
          wait_for_completion: true
          restart: true
```

### Compose Service Deployment

Deploy a Docker Compose service:

```yaml
name: Deploy Compose to Dokploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Compose service
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          deployment_type: compose
          compose_id: ${{ secrets.DOKPLOY_COMPOSE_ID }}
          compose_name: my-compose-stack
          wait_for_completion: true
```

### Compose Service with Restart

```yaml
      - name: Deploy and restart compose
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          deployment_type: compose
          compose_id: ${{ secrets.DOKPLOY_COMPOSE_ID }}
          compose_name: my-compose-stack
          wait_for_completion: true
          restart: true
```

### Multiple Compose Services (Matrix)

Deploy multiple compose services in parallel:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        compose:
          - { id: 'abc123', name: 'backend-stack' }
          - { id: 'def456', name: 'frontend-stack' }
    steps:
      - name: Deploy ${{ matrix.compose.name }}
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          deployment_type: compose
          compose_id: ${{ matrix.compose.id }}
          compose_name: ${{ matrix.compose.name }}
          wait_for_completion: true
```

### Multiple Applications (Matrix Strategy)

Deploy multiple apps in parallel:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app:
          - { id: 'abc123', name: 'api' }
          - { id: 'def456', name: 'worker-1' }
          - { id: 'ghi789', name: 'worker-2' }
    steps:
      - name: Deploy ${{ matrix.app.name }}
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: https://app.dokploy.com
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: ${{ matrix.app.id }}
          application_name: ${{ matrix.app.name }}
          wait_for_completion: true
          restart: true
```

### With E2E Tests After Deployment

Ensure tests run against the new version:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy application
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: ${{ secrets.DOKPLOY_APP_ID }}
          application_name: my-app
          wait_for_completion: true  # Critical: wait before testing!

  test:
    needs: deploy
    runs-on: ubuntu-latest
    steps:
      - name: Run E2E tests
        run: npm run test:e2e
```

### Debug Mode

Enable detailed logging to troubleshoot issues:

```yaml
      - name: Deploy (with debug)
        uses: tarasyarema/dokploy-deploy-action@main
        with:
          dokploy_url: ${{ secrets.DOKPLOY_URL }}
          auth_token: ${{ secrets.DOKPLOY_TOKEN }}
          application_id: ${{ secrets.DOKPLOY_APP_ID }}
          application_name: my-app
          wait_for_completion: true
          debug: true
```

## How It Works

The action fixes the race condition bug for both application and compose deployments by:

1. **Capturing baseline**: Gets the timestamp of the latest deployment before triggering
2. **Triggering deployment**: Calls Dokploy API to start deployment
3. **Finding the new deployment**: Polls `/api/deployment/all` for a deployment created after baseline
4. **Tracking by ID**: Monitors that specific deployment's status until completion
5. **Verifying completion**: Ensures deployment actually entered "running" state before "done"

This prevents the bug where the action would check service status (already "done" from previous deployment) instead of tracking the triggered deployment.

**Supported Deployment Types:**
- **Application deployments**: Traditional Dokploy application deployments
- **Compose deployments**: Docker Compose stack deployments

## Troubleshooting

### "Deployment marked 'done' after only Xs without entering 'running' state"

This warning indicates a potential race condition. The deployment might not have started yet, or completed extremely quickly. If you see this consistently, enable `debug: true` to see detailed API responses.

### "No new deployment appeared within 30 seconds"

The deployment trigger succeeded but no deployment was created. Possible causes:
- Application ID is incorrect
- Dokploy is experiencing issues
- Deployment is queued but hasn't started

Check the Dokploy dashboard manually.

### "Deployment stuck in 'idle' state"

The deployment is queued behind other deployments. This is normal for busy Dokploy instances. The action will continue waiting up to the timeout (10 minutes).

### Enable Debug Logging

Set `debug: true` to see:
- Full API request URLs and bodies
- Complete API responses
- Detailed state transitions

```yaml
with:
  debug: true
```

---

# CLI Tool: Deploy from Your Machine

The `dokdeploy` CLI lets you deploy directly to Dokploy from your local machine or any CI system.

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Initialize config file
uv run ./dokdeploy init

# 3. Edit ~/.dokploy/deploy.yaml with your apps
vim ~/.dokploy/deploy.yaml

# 4. Deploy!
uv run ./dokdeploy deploy api
uv run ./dokdeploy deploy --all
```

## Example Config

`~/.dokploy/deploy.yaml`:
```yaml
dokploy:
  url: https://app.dokploy.com
  auth_token: $DOKPLOY_AUTH_TOKEN

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

## CLI Commands

```bash
# List configured apps
uv run ./dokdeploy list

# Deploy one or more apps
uv run ./dokdeploy deploy api
uv run ./dokdeploy deploy api worker frontend

# Deploy all apps (like your GitHub matrix!)
uv run ./dokdeploy deploy --all

# Check status
uv run ./dokdeploy status api

# View deployment history
uv run ./dokdeploy history api

# Validate config
uv run ./dokdeploy config validate
```

**See [DEVELOPMENT.md](DEVELOPMENT.md) for complete CLI documentation.**

---

# Testing Locally

You can test the deployment script locally without GitHub Actions.

**Quick start:**
```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy template and add your credentials
cp test_local.sh.template test_local.sh
# Edit test_local.sh with your Dokploy credentials

# Run it
./test_local.sh
```

**See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed local development guide.**

### Testing with a Different Branch

To test changes from a branch in your workflow:

```yaml
- uses: tarasyarema/dokploy-deploy-action@your-branch-name
```

Or reference your fork:

```yaml
- uses: your-username/dokploy-deploy-action@main
```

## What Was Fixed

**Before (v1.x - Bash version):**
- ❌ Checked `applicationStatus` (wrong field, race condition)
- ❌ 60-second initial wait (too long, missed state changes)
- ❌ No deployment ID tracking
- ❌ Instant "done" accepted as success
- ❌ Reload called without coordination
- ❌ Restart could start old version

**After (v2.0 - Python version):**
- ✅ Tracks specific deployment by ID
- ✅ 3-second initial poll (catches deployment quickly)
- ✅ Detects race conditions (instant "done" warning)
- ✅ Smart polling with exponential backoff
- ✅ Restart only after verified deployment
- ✅ Debug mode for troubleshooting
- ✅ Clear error messages

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any bugs or feature requests.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
