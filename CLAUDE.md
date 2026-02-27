# Dokploy Deploy Action

GitHub Action and CLI tool (`dokdeploy`) for deploying applications to Dokploy.

## Dokploy API

- **Swagger UI**: https://app.dokploy.com/swagger
- **OpenAPI spec** (JSON): `GET /api/settings.getOpenApiDocument` on any Dokploy instance (requires auth)
- **Base URL convention**: All API paths use **dot notation** (e.g. `/api/compose.deploy`, NOT `/api/compose/deploy`). Confirmed on v0.28.1.
- **Auth header**: `x-api-key: <token>`

## Testing against live API

Export `DOKPLOY_API_KEY` in your shell, then use curl:

```bash
# Fetch OpenAPI spec (use this to verify current path convention)
curl -s -H "accept: application/json" -H "x-api-key: $DOKPLOY_API_KEY" \
  "https://app.dokploy.com/api/settings.getOpenApiDocument"

# List compose deployments
curl -s -H "accept: application/json" -H "x-api-key: $DOKPLOY_API_KEY" \
  "https://app.dokploy.com/api/deployment.allByCompose?composeId=<COMPOSE_ID>"

# List application deployments
curl -s -H "accept: application/json" -H "x-api-key: $DOKPLOY_API_KEY" \
  "https://app.dokploy.com/api/deployment.all?applicationId=<APP_ID>"

# Get compose details
curl -s -H "accept: application/json" -H "x-api-key: $DOKPLOY_API_KEY" \
  "https://app.dokploy.com/api/compose.one?composeId=<COMPOSE_ID>"
```

For full local testing via the action, see `test_local.sh.template` (uses `INPUT_AUTH_TOKEN` env var).

## Project structure

```
src/
├── deploy.py              # Main entry point
├── dokploy_client.py      # API client (all Dokploy HTTP calls)
├── deployment_tracker.py  # Polling & verification
├── logger.py              # Logging setup
└── cli.py                 # CLI entrypoint (dokdeploy)
```

## Key files

- `action.yml` — GitHub Action definition
- `test_local.sh.template` — Template for local testing
- `DEVELOPMENT.md` — Full development guide
