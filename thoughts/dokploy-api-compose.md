---
date: 2025-12-23T21:50:07+00:00
researcher: Researcher
git_commit: N/A
branch: N/A
repository: N/A
topic: "Dokploy API Compose-Based Deployments"
tags: [research, dokploy, api, compose, docker-compose, deployment]
status: complete
last_updated: 2025-12-23
last_updated_by: Researcher
---

# Research: Dokploy API Compose-Based Deployments

**Date**: 2025-12-23T21:50:07+00:00
**Researcher**: Researcher
**Git Commit**: N/A
**Branch**: N/A
**Repository**: External Documentation Research

## Research Question

Research the Dokploy API at https://docs.dokploy.com/docs/api with focus on:
1. Compose-based deployment endpoints and methods
2. Required authentication and parameters
3. API request/response structure for compose deployments
4. Available options and configurations for compose services
5. Error handling and status checking

## Summary

The Dokploy API provides a comprehensive REST API built on tRPC for managing Docker Compose deployments. The API includes 25+ compose-specific endpoints covering the complete lifecycle of compose services, from creation to deployment, monitoring, and debugging. Authentication uses JWT tokens via the `x-api-key` header. The API follows a consistent request/response pattern with standardized error handling using tRPC error codes.

**Key Findings**:
- **Base URL**: `http://localhost:3000/api` (replace with your instance)
- **Authentication**: JWT tokens via `x-api-key` header
- **25+ Compose Endpoints**: Complete CRUD, deployment, lifecycle management
- **Configuration Options**: Environment variables, volumes, networks, git integration, auto-deploy
- **Status Checking**: Multiple deployment query endpoints and monitoring capabilities
- **Error Handling**: Standardized tRPC error codes with HTTP status mappings
- **Interactive Documentation**: Swagger UI at `your-vps-ip:3000/swagger`

---

## Detailed Findings

### 1. Compose-Based Deployment Endpoints and Methods

**Source**: [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose)

The Dokploy API provides 25+ endpoints for managing Docker Compose deployments. All endpoints follow the pattern `/api/compose.[operation]` and use either **POST** or **GET** HTTP methods.

#### Core CRUD Operations

**POST /api/compose.create**
- **Purpose**: Create a new compose configuration
- **HTTP Method**: POST
- **Required Parameters**:
  - `name` (string, length ≥ 1) - Service identifier
  - `environmentId` (string) - Target environment reference
- **Optional Parameters**:
  - `description` (string) - Service description
  - `composeType` ("docker-compose" | "stack") - Deployment type
  - `appName` (string) - DNS-compatible name (auto-generated if not provided)
  - `serverId` (string) - Target server
  - `composeFile` (string) - YAML content specification

**GET /api/compose.one**
- **Purpose**: Retrieve a specific compose configuration by ID
- **HTTP Method**: GET
- **Required Parameters**:
  - `composeId` (string, min length 1) - Unique identifier

**POST /api/compose.update**
- **Purpose**: Modify existing compose settings
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)
- **Optional Parameters** (20+ parameters including):
  - `name`, `appName`, `description`
  - `env` (environment variables)
  - `composeFile`, `composePath`
  - `sourceType`, `composeType`
  - Repository details (GitHub/GitLab/Bitbucket/Gitea)
  - Deployment settings
  - `autoDeploy` flag

**POST /api/compose.delete**
- **Purpose**: Remove compose application and optionally associated volumes
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)
  - `deleteVolumes` (boolean) - Whether to delete associated volumes

#### Deployment Operations

**POST /api/compose.deploy**
- **Purpose**: Deploy a compose application (initial deployment)
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)
- **Optional Parameters**:
  - `title` (string) - Deployment metadata
  - `description` (string) - Deployment metadata

**POST /api/compose.redeploy**
- **Purpose**: Redeploy an existing compose application
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)
- **Optional Parameters**:
  - `title` (string)
  - `description` (string)

**POST /api/compose.cancelDeployment**
- **Purpose**: Halt an active deployment process
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.isolatedDeployment**
- **Purpose**: Enable isolated deployment mode
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

#### Lifecycle Management

**POST /api/compose.start**
- **Purpose**: Initiate a stopped compose service
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.stop**
- **Purpose**: Terminate a running compose service
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

#### Service & Configuration Loading (GET Endpoints)

**GET /api/compose.loadServices**
- **Purpose**: List services from compose file
- **HTTP Method**: GET
- **Required Parameters**:
  - `composeId` (string, min length 1)
- **Optional Parameters**:
  - `type` (string, default: "cache") - Specifies whether to use cached or fresh data

**GET /api/compose.loadMountsByService**
- **Purpose**: Retrieve mount points for a specific service
- **HTTP Method**: GET
- **Required Parameters**:
  - `composeId` (string, min length 1)
  - `serviceName` (string, min length 1)

**GET /api/compose.getDefaultCommand**
- **Purpose**: Retrieve default execution command
- **HTTP Method**: GET
- **Required Parameters**:
  - `composeId` (string, min length 1)

**GET /api/compose.getConvertedCompose**
- **Purpose**: Retrieve converted compose file format
- **HTTP Method**: GET
- **Required Parameters**:
  - `composeId` (string, min length 1)

#### Source Control & Git Provider Operations

**POST /api/compose.fetchSourceType**
- **Purpose**: Retrieve source type information
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.disconnectGitProvider**
- **Purpose**: Disconnect git provider integration
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.refreshToken**
- **Purpose**: Refresh authentication token for git provider
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

#### Build & Queue Management

**POST /api/compose.cleanQueues**
- **Purpose**: Clear deployment queues
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.killBuild**
- **Purpose**: Terminate active build process
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

#### Template Management

**POST /api/compose.deployTemplate**
- **Purpose**: Deploy from template
- **HTTP Method**: POST
- **Required Parameters**: Template-specific parameters

**GET /api/compose.templates**
- **Purpose**: List available compose templates
- **HTTP Method**: GET
- **Optional Parameters**:
  - `baseUrl` (string) - Template repository URL

**GET /api/compose.getTags**
- **Purpose**: Retrieve available tags for templates
- **HTTP Method**: GET
- **Optional Parameters**:
  - `baseUrl` (string) - Template source URL

**POST /api/compose.processTemplate**
- **Purpose**: Process template variables
- **HTTP Method**: POST
- **Required Parameters**: Template processing parameters

**POST /api/compose.import**
- **Purpose**: Import compose configuration
- **HTTP Method**: POST
- **Required Parameters**: Import configuration data

#### Advanced Operations

**POST /api/compose.randomizeCompose**
- **Purpose**: Randomize compose naming
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)

**POST /api/compose.move**
- **Purpose**: Move compose to different environment
- **HTTP Method**: POST
- **Required Parameters**:
  - `composeId` (string, length ≥ 1)
  - Target environment parameters

#### Summary of HTTP Methods Used

- **GET**: Used for read operations (retrieving configurations, services, templates, commands)
  - 7 endpoints: `compose.one`, `compose.loadServices`, `compose.loadMountsByService`, `compose.getDefaultCommand`, `compose.getConvertedCompose`, `compose.templates`, `compose.getTags`
- **POST**: Used for all write operations (create, update, delete, deploy, lifecycle management)
  - 18+ endpoints for all other operations
- **PUT**: Not used in the compose API
- **DELETE**: Not used (deletion is handled via `POST /compose.delete`)

---

### 2. Required Authentication and Parameters

**Sources**:
- [Dokploy API](https://docs.dokploy.com/docs/api)
- [Auth Reference](https://docs.dokploy.com/docs/api/reference-auth)
- [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose)

#### Authentication Method

**Type**: JWT Token-based authentication

**How to Generate an API Token**:
1. Navigate to `/settings/profile` page in your Dokploy instance
2. Go to the API/CLI Section
3. Generate the token

**How to Authenticate Requests**:

API requests require authentication via HTTP headers:

**Primary Method - Header: `x-api-key`**
```bash
curl -X 'GET' \
  'https://dokploy.com/api/project.all' \
  -H 'accept: application/json' \
  -H 'x-api-key: YOUR-GENERATED-API-KEY'
```

**Alternative Methods** (some endpoints may also accept):
- `Authorization: <token>`
- `Authorization: Bearer <token>`

#### Access Control & Configuration

**User Access Requirements**:
- **Administrators**: Have default access to the API and Swagger UI at `your-vps-ip:3000/swagger`
- **Users**: Do not have direct API access by default; administrators must grant access and enable token generation capabilities

**API Base URL**:
- Default OpenAPI base URL: `http://localhost:3000/api`
- Replace `localhost:3000` with your Dokploy instance's IP address or domain name

#### Required Parameters for Compose Operations

**For `compose.create`**:
- `name` (required, string, min length 1) - Service identifier
- `environmentId` (required, string) - Target environment reference (obtained from `project.all`)
- `appName` (optional, string) - DNS-compatible name (auto-generated based on name field if not provided)

**Optional Parameters**:
- `description` (string) - Service description
- `serverId` (string) - Target server
- `composeFile` (string) - Docker Compose YAML content

**For `compose.deploy`**:
- `composeId` (required, string, min length 1) - Unique service identifier obtained from `compose.create` or `project.all`

**Optional Parameters**:
- `title` (string) - Deployment metadata
- `description` (string) - Deployment metadata

**For `compose.update`**:
- `composeId` (required, string, min length 1) - Service to update
- 20+ optional parameters for various configuration aspects

#### Getting Required IDs

To obtain `composeId` or `environmentId`:

```bash
curl -X 'GET' \
  'https://your-domain/api/project.all' \
  -H 'accept: application/json' \
  -H 'x-api-key: <token>'
```

This returns all projects and their associated services (applications, compose services, databases).

#### AppName Validation Rules

**Source**: [GitHub PR #904](https://github.com/Dokploy/dokploy/pull/904), [GitHub PR #1562](https://github.com/Dokploy/dokploy/pull/1562)

- Must be DNS-compatible
- No trailing dashes (e.g., "dokploy-backend-2-" is invalid, "dokploy-backend" is valid)
- No spaces (spaces are automatically replaced with hyphens via API)
- Must be unique across all database tables (mysql, postgres, mongo, redis, mariadb)
- Used in Docker Compose commands as: `docker compose -p ${compose.appName} up -d`

---

### 3. API Request/Response Structure for Compose Deployments

**Sources**:
- [Dokploy API](https://docs.dokploy.com/docs/api)
- [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose)
- [Application API Reference](https://docs.dokploy.com/docs/api/reference-application)

#### Request Body Structure

**Standard Pattern**:
- **POST** requests use JSON body with `Content-Type: application/json`
- **GET** requests use query parameters
- All requests require `x-api-key` header for authentication

**Example: Create Compose**
```bash
curl -X 'POST' \
  'https://your-domain/api/compose.create' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: <your-token>' \
  -d '{
    "name": "my-compose-app",
    "environmentId": "env-id-string"
  }'
```

**Example: Deploy Compose**
```bash
curl -X 'POST' \
  'https://your-domain/api/compose.deploy' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: <your-token>' \
  -d '{
    "composeId": "string"
  }'
```

**Example: Get Compose Details**
```bash
curl -X 'GET' \
  'https://your-domain/api/compose.one?composeId=<compose-id>' \
  -H 'accept: application/json' \
  -H 'x-api-key: <your-token>'
```

#### Response Format and Structure

**Success Response**:
- **HTTP Status**: `200`
- **Content**: Relevant object (compose configuration, deployment status, etc.)

**Example Success Response** (compose.create):
Returns the created compose object with all fields including:
- `composeId` - Unique identifier
- `name`, `appName`, `description`
- `composeStatus` - Current status value
- Configuration details

#### Status Codes Returned

**Success**:
- **200 OK**: Successful operation

**Error Responses** (tRPC-based):

**Source**: [tRPC Error Handling](https://trpc.io/docs/server/error-handling)

| HTTP Status | Error Code | Use Case |
|------------|-------------|----------|
| 400 | BAD_REQUEST | Client input errors |
| 401 | UNAUTHORIZED | Missing authentication |
| 403 | FORBIDDEN | Access denied |
| 404 | NOT_FOUND | Resource missing |
| 408 | TIMEOUT | Request timeout |
| 409 | CONFLICT | Resource state conflict |
| 422 | UNPROCESSABLE_CONTENT | Invalid input data |
| 429 | TOO_MANY_REQUESTS | Rate limit exceeded |
| 500 | INTERNAL_SERVER_ERROR | Unspecified errors |
| 503 | SERVICE_UNAVAILABLE | Server unavailable |
| 504 | GATEWAY_TIMEOUT | Gateway timeout |

#### Error Response Structure

**Standard Error Format**:
```json
{
  "message": "string",
  "code": "string",
  "issues": [
    {
      "message": "string"
    }
  ]
}
```

**Complete tRPC Error Response** includes:
- **message**: Description of the error
- **code**: JSON-RPC error code (e.g., -32600 for BAD_REQUEST)
- **data object** containing:
  - `code`: tRPC error code
  - `httpStatus`: Associated HTTP status code
  - `stack`: Stack trace (development only)
  - `path`: Procedure path where error occurred

#### Status Values for Deployments

**Source**: [Application API Reference](https://docs.dokploy.com/docs/api/reference-application)

The `composeStatus` or `applicationStatus` field contains one of these values:
- **"idle"**: Not active
- **"running"**: Currently deploying
- **"done"**: Completed successfully
- **"error"**: Failed

#### Documentation Gaps

**Note**: The documentation provides endpoint descriptions and field requirements but lacks comprehensive JSON request/response examples for each endpoint. The most complete and accurate API schema information is available through the Swagger UI at `your-instance:3000/swagger`.

**Limitations**:
1. Limited JSON examples in public documentation
2. Only `200` (success) status code is explicitly documented
3. Field validation details (string length limits, regex patterns) not fully documented
4. Complete response schemas showing all fields not provided in docs
5. No API version information or versioning strategy documented
6. No rate limiting information

---

### 4. Available Options and Configurations for Compose Services

**Sources**:
- [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose)
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose)
- [Environment Variables](https://docs.dokploy.com/docs/core/variables)
- [Mounts API Reference](https://docs.dokploy.com/docs/api/reference-mounts)

#### Core Configuration Fields

**Via `compose.create` and `compose.update`**:

- `name` (required, string) - Service identifier, minimum 1 character
- `environmentId` (required, string) - Target environment reference
- `composeId` (required for updates, string) - Unique compose identifier
- `description` (optional, string) - Service details
- `composePath` (string) - File path within repository
- `composeFile` (string) - YAML content specification (contains the actual Docker Compose file content)
- `composeType` (string) - "docker-compose" or "stack"
- `command` (string) - Custom execution directive
- `suffix` (string) - Identifier appending for isolation
- `randomize` (boolean) - Auto-generate service name variations

#### Git Integration Options

- `sourceType` (string) - "git", "github", "gitlab", "bitbucket", "gitea", or "raw"
- `repository` (string) - Repository metadata
- `owner` (string) - Repository owner
- `branch` (string) - Branch to deploy from
- `autoDeploy` (boolean) - Automatic deployment on push
- `enableSubmodules` (boolean) - Include git submodules
- `watchPaths` (array of strings) - Trigger deployment on specific file changes

**Watch Paths Pattern Matching**:

**Source**: [Watch Paths](https://docs.dokploy.com/docs/core/watch-paths)

- **Glob patterns**: `**`, `*.js`
- **Negation**: `!a/*.js`
- **Extended globs**: `+(x|y)`, `!(a|b)`
- **Character classes**: `[[:alpha:][:digit:]]`
- **Brace expansion**: `foo/{1..5}.md`, `bar/{a,b,c}.js`
- **Regex patterns**: `foo-[1-5].js`, `foo/(abc|xyz).js`

Examples:
- `src/*` - monitors all files in the src directory
- `src/index.js` - targets a specific file

#### Environment Variables Configuration

**Sources**:
- [Environment Variables](https://docs.dokploy.com/docs/core/variables)
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose)

Dokploy allows management of environment variables at multiple levels:

**1. Project-level (shared)** - Accessible across all services in a project
- Referenced using: `${{project.VARIABLE_NAME}}`
- Example: `DATABASE_URL=${{project.DATABASE_URL}}`

**2. Environment-level** - Specific to a single environment
- Referenced using: `${{environment.VARIABLE_NAME}}`
- Support environment-specific configurations like staging vs. production

**3. Service-level** - Specific to individual services
- Referenced using: `${{VARIABLE_NAME}}`
- Can override shared variables

**Special Variables**:
- `DOKPLOY_DEPLOY_URL` - Available in Preview Deployments, points to the deployment URL
  - Usage: `APP_URL=https://${{DOKPLOY_DEPLOY_URL}}`

**File Creation**:
Dokploy automatically creates a `.env` file in the specified Docker Compose file path by default.

**Known Issue**: [GitHub Issue #2777](https://github.com/Dokploy/dokploy/issues/2777) - The ComposeFileEditor component only updates `composeFile` and `sourceType` when saving in Raw mode, but does not reset `composePath`, which can cause the .env file to be created in the wrong directory.

#### Volumes and Mounts

**Sources**:
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose)
- [Mounts API Reference](https://docs.dokploy.com/docs/api/reference-mounts)
- [Volume Backups](https://docs.dokploy.com/docs/core/volume-backups)

**Mounts API Endpoints**:

**POST `/mounts.create`** - Creates a new mount for a service
- Required parameters:
  - `type` (string): "bind", "volume", or "file"
  - `mountPath` (string): Target mount path (minimum length: 1)
  - `serviceId` (string): Associated service ID (minimum length: 1)
- Optional parameters: `hostPath`, `volumeName`, `content`, `filePath`, `serviceType` (defaults to "application")

**POST `/mounts.remove`** - Deletes an existing mount
- `mountId` (string): The mount identifier to remove

**GET `/mounts.one`** - Retrieves a single mount's details
- `mountId` (string): The mount to fetch

**POST `/mounts.update`** - Modifies mount configuration
- `mountId` (string, required): Mount to update
- Optional: `type`, `hostPath`, `volumeName`, `filePath`, `content`, `mountPath`
- Service-specific IDs: `applicationId`, `postgresId`, `mysqlId`, `mongoId`, `mariadbId`, `redisId`, `composeId`

**GET `/mounts.allNamedByApplicationId`** - Lists all mounts for a specific application
- `applicationId` (string, required)

**Two Volume Approaches**:

**Bind Mounts (`../files` folder)**:
- Maps host directories into containers
- Avoid absolute paths as they're cleaned during deployments
- Use relative paths: `"../files/my-database:/var/lib/mysql"`
- Best for configuration files and simple persistence

**Docker Named Volumes**:
- Docker-managed storage with better portability
- Supports automated backups via Dokploy's Volume Backups feature
- Recommended for databases and large datasets
- Only named volumes work with backup functionality (bind mounts do not support backups)

**Important Warning**: When using AutoDeploy, you must move files from your repository to Dokploy's File Mounts (via Advanced → Mounts) instead of mounting them directly from the repository, because Dokploy performs a git clone on each deployment which clears the repository directory.

#### Networks Configuration

**Source**: [Docker Compose Example](https://docs.dokploy.com/docs/core/docker-compose/example)

Services must connect to the `dokploy-network`:
```yaml
networks:
  - dokploy-network
```

The network is defined as external:
```yaml
networks:
  dokploy-network:
    external: true
```

**Important Note**: Don't set `container_name` property to each service, as it will cause issues with logs, metrics, and other features.

#### Docker Compose File Specification

**Sources**:
- [Docker Compose Example](https://docs.dokploy.com/docs/core/docker-compose/example)
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose)

**How to Specify Docker-Compose.yml**:

1. **Via Compose Path**: Specify the path like `./docker-compose.yml` when setting up a Docker Compose service
2. **Via composeFile parameter**: Contains the actual compose file YAML content
3. **Source Types**:
   - **Git providers**: "github", "gitlab", "bitbucket", "gitea" - Pull from repository
   - **Raw mode**: "raw" - Manual compose file input through the UI

**Port Configuration**:
Instead of binding specific ports, services should expose ports without host binding:
- Use: `ports: - 3000`
- Rather than: `3000:3000`

**Traefik Labels Pattern**:
For domain routing, services use Traefik labels following this structure:
- `traefik.enable=true`
- `traefik.http.routers.<unique-name>.rule=Host(<domain>)`
- `traefik.http.routers.<unique-name>.entrypoints=websecure`
- `traefik.http.services.<unique-name>.loadbalancer.server.port=3000`

**For Docker Stack**: Labels should be placed under `deploy.labels` instead of directly under `labels`.

#### Domain Configuration

**Source**: [Domains - Docker Compose](https://docs.dokploy.com/docs/core/docker-compose/domains)

**Method 1: Dokploy Domains (Recommended)**:
- Configure domains directly through the Dokploy UI in the Domains tab
- At runtime, during the deployment phase, Dokploy automatically adds Traefik labels internally to your Docker Compose file

**Method 2: Manual Configuration (Advanced)**:
- Manually add Traefik labels to your compose file
- Add services to the `dokploy-network`
- Configure routing rules using Traefik labels
- Use `expose` instead of `ports` to limit access to the container network

#### Auto-Deploy Configuration

**Source**: [Auto Deploy](https://docs.dokploy.com/docs/core/auto-deploy)

**Webhook-Based Deployment**:

Supported Git providers:
- GitHub (zero configuration)
- GitLab
- Bitbucket
- Gitea
- DockerHub (Applications only)

Setup steps:
1. Enable the 'Auto Deploy' toggle in service's general settings
2. Locate and copy the Webhook URL from deployment logs
3. Configure the webhook in your repository provider's settings

**Important**: When using Git-based providers, ensure that the branch configured in Dokploy matches the branch you intend to push to.

**API-Based Deployment**:
1. Generate an API token in your profile settings
2. Retrieve your service's ID using the `project.all` endpoint
3. Trigger deployment via the `compose.deploy` endpoint

#### Registry Integration

**Source**: [Registry API Reference](https://docs.dokploy.com/docs/api/generated/reference-registry)

Registry API includes endpoints for creating, updating, removing, and testing Docker registries with parameters including:
- `registryName`
- `username`
- `password`
- `registryUrl`
- `registryType`
- `imagePrefix`

**For Docker Stack (Swarm mode)** with private registry: Use the `--with-registry-auth` flag in the command configuration.

#### Advanced Compose-Specific Settings

**Sources**:
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose)
- [Advanced](https://docs.dokploy.com/docs/core/applications/advanced)

**Command Configuration**:
Dokploy has a defined command to run the Docker Compose file, ensuring complete control through the UI. However, you can append flags or options to the command.

**Compose Types**:
- **docker-compose**: For standard configurations
- **stack**: For Docker Swarm orchestration (note: some features like `build` are unavailable)

**Additional Settings** (based on Advanced features):
- **Redirects**: Regex patterns for URL rewriting
- **Ports**: Published port mapping (port on host to port in container)
- **Health Checks**: JSON configuration with Test, Interval, Timeout, StartPeriod, Retries
- **Replicas**: Set number of instances (Replicated, Global, or ReplicatedJob modes)

**Note**: Many advanced features like build servers, cluster settings, swarm configurations, and resource management are primarily designed for Applications, not Docker Compose deployments.

---

### 5. Error Handling and Status Checking

**Sources**:
- [Application API Reference](https://docs.dokploy.com/docs/api/reference-application)
- [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose)
- [Deployment API Reference](https://docs.dokploy.com/docs/api/deployment)
- [tRPC Error Handling](https://trpc.io/docs/server/error-handling)
- [Troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting)

#### Error Response Format and Structure

**Standard Error Response Schema**:
```json
{
  "message": "string",
  "code": "string",
  "issues": [
    {
      "message": "string"
    }
  ]
}
```

**Complete tRPC Error Response** includes:
- **message**: Description of the error
- **code**: JSON-RPC error code (e.g., -32600 for BAD_REQUEST)
- **data object** containing:
  - `code`: tRPC error code
  - `httpStatus`: Associated HTTP status code
  - `stack`: Stack trace (development only)
  - `path`: Procedure path where error occurred

#### Common Error Codes and Their Meanings

Dokploy uses tRPC's error codes with HTTP status code mappings:

| Error Code | HTTP Status | Use Case |
|------------|-------------|----------|
| BAD_REQUEST | 400 | Client input errors |
| UNAUTHORIZED | 401 | Missing authentication |
| FORBIDDEN | 403 | Access denied |
| NOT_FOUND | 404 | Resource missing |
| TIMEOUT | 408 | Request timeout |
| CONFLICT | 409 | Resource state conflict |
| UNPROCESSABLE_CONTENT | 422 | Invalid input data |
| TOO_MANY_REQUESTS | 429 | Rate limit exceeded |
| INTERNAL_SERVER_ERROR | 500 | Unspecified errors |
| SERVICE_UNAVAILABLE | 503 | Server unavailable |
| GATEWAY_TIMEOUT | 504 | Gateway timeout |

**Additional Error Handling Information**:
- In case of an error, the status code is derived from the thrown TRPCError or defaults to 500
- Response metadata can be modified using the `responseMeta` function

#### Common Deployment-Related Errors

**Source**: [Troubleshooting Guide](https://docs.dokploy.com/docs/core/troubleshooting)

- **Exit code 137**: Out-of-memory error
- **"Branch Not Match" error**: Occurs when the configured branch doesn't match the push branch
- **"no such image" or "docker authentication failed"**: Private registry authentication issues without `--with-registry-auth` flag
- **4MB Response Size Limit**: Batched TRPC requests hitting Next.js API response size limit

#### How to Check Deployment Status

**Application/Compose Status Values**:

The `composeStatus` or `applicationStatus` field contains one of these values:
- **"idle"**: Application is not active
- **"running"**: Application/deployment is currently in progress
- **"done"**: Application/deployment has completed successfully
- **"error"**: Application/deployment encountered an error

**Compose Status Checking Endpoints**:

**GET /api/compose.one**
- Retrieves complete compose details including current status
- Required: `composeId`

**Deployment Query Endpoints**:

**Source**: [Deployment API Reference](https://docs.dokploy.com/docs/api/deployment)

1. **GET `/deployment.all`**
   - Parameters: `applicationId` (required)
   - Purpose: Retrieve all deployments for a specific application

2. **GET `/deployment.allByCompose`**
   - Parameters: `composeId` (required)
   - Purpose: Fetches deployments associated with Docker Compose services

3. **GET `/deployment.allByServer`**
   - Parameters: `serverId` (required)
   - Purpose: Lists deployments running on a particular server

4. **GET `/deployment.allByType`**
   - Parameters:
     - `id` (required)
     - `type` (required): "application" | "compose" | "server" | "schedule" | "previewDeployment" | "backup" | "volumeBackup"
   - Purpose: Retrieves deployments filtered by resource type

5. **POST `/deployment.killProcess`**
   - Parameters: `deploymentId` (required)
   - Purpose: Terminates an active deployment process

**Application Monitoring Endpoints**:

- **GET `/application.one`** - Retrieves application details including current status
- **GET `/application.readAppMonitoring`** - Monitors application health using `appName` parameter

#### Polling or Webhook Mechanisms for Status Updates

**Webhook Notifications**:

**Source**: [Webhook Documentation](https://docs.dokploy.com/docs/core/webhook)

**Configuration**:
- **Webhook URL**: Target HTTP endpoint for notifications
- **Name**: Custom identifier for the notification configuration

**Payload Structure**:
```json
{
  "title": "Test Notification",
  "message": "Hi, From Dokploy 👋",
  "timestamp": "2025-12-07T19:41:53.470Z"
}
```

**Notification Events Available**:
- App Deploy: Triggered when an app is deployed
- App Build Error: Triggered when the build fails
- Database Backup: Triggered when a database backup is created
- Volume Backups
- Dokploy service restarts
- Docker cleanup operations
- Server resource threshold breaches

**Webhook Requirements**:
- Accept POST requests
- Return 2xx HTTP status codes for successful delivery
- Handle JSON payloads
- Be internet-accessible (or accessible from the Dokploy server network)
- Implement HTTPS with API key headers for security

**Testing Tool**: [Webhook.site](https://webhook.site) - recommended for development testing

**Auto-Deploy Webhooks**:

**Source**: [Auto Deploy Documentation](https://docs.dokploy.com/docs/core/auto-deploy)

**Supported Platforms**:
- GitHub (auto-configured without setup)
- GitLab
- Bitbucket
- Gitea
- DockerHub (applications only)

**Setup Process**:
1. Toggle 'Auto Deploy' button in application settings
2. Locate webhook URL from deployment logs
3. Add URL to repository platform's webhook settings

**Monitoring and Polling**:

**Source**: [Monitoring Documentation](https://docs.dokploy.com/docs/core/monitoring)

**Refresh Rates** (Cloud Version only):
- **Server metrics**: Default 20 seconds (configurable)
- **Container metrics**: Default 20 seconds (configurable)
- **Metrics retention**: Default 2 days
- **Port requirement**: Port 4500 must be open

**Alert Thresholds**:
- CPU Threshold (%): Configurable (0 = disabled)
- Memory Threshold (%): Configurable (0 = disabled)
- Alerts trigger only when server-level thresholds are exceeded

**Metrics Callback URL**:
- Default: `https://app.dokploy.com/api/trpc/notification.receiveNotification`
- Custom callback URLs can be configured
- Requires Metrics Token for authentication

**Note**: Monitoring is exclusive to the Cloud Version. Initial setup requires a few minutes for data collection before metrics appear.

#### Logging or Debugging Capabilities

**Deployment History**:

**Source**: [Rollbacks Documentation](https://docs.dokploy.com/docs/core/applications/rollbacks)

- View the last 10 deployments of an application
- Each deployment record is linked to a specific image tag in the registry
- Deployment versions displayed alongside rollback buttons

**Docker Service Logs**:

**Source**: [Troubleshooting Documentation](https://docs.dokploy.com/docs/core/troubleshooting)

When Dokploy UI is inaccessible, administrators can examine logs using:
- `docker service logs dokploy` (UI service)
- `docker service logs dokploy-postgres` (database)
- `docker service logs dokploy-redis` (cache)
- `docker logs dokploy-traefik` (routing layer)

**Log Access Issues**:
- **Slow Server**: Affects concurrent requests and SSL handshakes
- **Insufficient Disk Space**: Prevents log loading
- **Remote Worker Nodes**: UI won't have access to logs or monitoring for applications on different cluster nodes

**Compose Debugging Endpoints**:

- **POST `/compose.cleanQueues`** - Clean deployment queues
- **POST `/compose.killBuild`** - Kill ongoing build process
- **GET `/compose.loadServices`** - Load services with cache type option
- **GET `/compose.getConvertedCompose`** - Returns transformed configuration

**Docker API Endpoints**:

**Source**: [Docker API Reference](https://docs.dokploy.com/docs/api/docker)

- **GET `/docker.getContainers`** - List containers (optional `serverId`)
- **GET `/docker.getConfig`** - Get container configuration (requires `containerId`)
- **GET `/docker.getContainersByAppNameMatch`** - Find containers by app name
- **GET `/docker.getContainersByAppLabel`** - Find containers by label
- **GET `/docker.getStackContainersByAppName`** - Get stack containers
- **GET `/docker.getServiceContainersByAppName`** - Get service containers
- **POST `/docker.restartContainer`** - Restart specific container

**Backup Logging**:

**Source**: [v0.22.0 Release Notes](https://dokploy.com/blog/v0-22-0-docker-compose-backups-schedule-tasks-logs)

- Integrated logging for each backup operation
- Detailed logs for every backup performed
- Supports PostgreSQL, MariaDB, MySQL, MongoDB backups

#### Gaps or Limitations

1. **No Specific Log Retrieval Endpoint**: The documentation doesn't show a dedicated API endpoint like `docker.getLogs` or `deployment.getLogs` for programmatically retrieving deployment logs. Logs appear to be accessible primarily through the UI or Docker CLI commands.

2. **Limited Polling Documentation**: No explicit documentation on recommended polling intervals or best practices for status checking via API.

3. **Webhook Event Filtering**: Documentation doesn't specify granular event type filtering or deployment-specific status updates in the webhook system beyond basic event types.

4. **Monitoring Cloud-Only**: The monitoring features with metrics collection are exclusive to the Cloud Version and not available in self-hosted instances.

5. **Incomplete OpenAPI Documentation**: GitHub issue mentions a need for better OpenAPI response definitions.

6. **Error Code Documentation**: While tRPC error codes are documented, Dokploy-specific error codes beyond the standard tRPC codes are not explicitly listed.

---

## Code References

N/A - This is external API documentation research, no codebase files were referenced.

---

## Architecture Documentation

The Dokploy API is built on **tRPC** (TypeScript Remote Procedure Call) framework, which provides:
- Type-safe API calls
- Automatic request/response validation
- Standardized error handling
- OpenAPI generation via custom trpc-openapi integration

**API Architecture**:
- **Base URL**: `http://localhost:3000/api` (customizable)
- **Authentication**: JWT tokens via `x-api-key` header
- **Request Format**: JSON for POST, query parameters for GET
- **Response Format**: JSON with consistent structure
- **Error Handling**: tRPC error codes with HTTP status mappings
- **Interactive Docs**: Swagger UI at `/swagger` endpoint

**Deployment Architecture**:
- Dokploy uses **Traefik** as reverse proxy for routing
- Services must connect to `dokploy-network` for internal communication
- Supports **Docker Compose** and **Docker Stack** (Swarm) deployments
- Git integration with multiple providers (GitHub, GitLab, Bitbucket, Gitea)
- Webhook-based auto-deploy and manual API-triggered deployments

---

## Related Research

N/A - This is the initial research document for Dokploy API compose deployments.

---

## Open Questions

1. **Log Retrieval API**: Is there a dedicated API endpoint for retrieving deployment logs programmatically, or must logs be accessed via Docker CLI or UI only?

2. **Polling Best Practices**: What are the recommended polling intervals for checking deployment status via the API to avoid rate limiting or performance issues?

3. **Webhook Granularity**: Can webhooks be configured to filter for specific event types (e.g., only compose deployment failures) or are all configured events sent to the webhook URL?

4. **Advanced Features for Compose**: Which "Advanced" settings (replicas, health checks, redirects, ports) from the Applications API are fully supported for Docker Compose deployments?

5. **Rate Limiting**: Are there any rate limits on API calls, and if so, what are the thresholds?

6. **API Versioning**: How does Dokploy handle API versioning? Will breaking changes be introduced in future versions?

7. **Complete OpenAPI Schema**: Where can the complete, up-to-date OpenAPI schema be accessed programmatically (beyond the Swagger UI)?

---

## Sources

### Primary Documentation
- [Dokploy API](https://docs.dokploy.com/docs/api) - Main API documentation and authentication
- [Compose API Reference](https://docs.dokploy.com/docs/api/reference-compose) - Compose-specific endpoints
- [Application API Reference](https://docs.dokploy.com/docs/api/reference-application) - Application endpoints (similar patterns)
- [Deployment API Reference](https://docs.dokploy.com/docs/api/deployment) - Deployment query endpoints
- [Docker API Reference](https://docs.dokploy.com/docs/api/docker) - Docker container management
- [Mounts API Reference](https://docs.dokploy.com/docs/api/reference-mounts) - Volume and mount management
- [Notification API Reference](https://docs.dokploy.com/docs/api/reference-notification) - Webhook notifications
- [Auth Reference](https://docs.dokploy.com/docs/api/reference-auth) - Authentication endpoints
- [Registry API Reference](https://docs.dokploy.com/docs/api/generated/reference-registry) - Docker registry integration
- [Preview Deployment API Reference](https://docs.dokploy.com/docs/api/reference-previewDeployment) - Preview deployments

### Core Features Documentation
- [Docker Compose](https://docs.dokploy.com/docs/core/docker-compose) - Compose configuration guide
- [Docker Compose Example](https://docs.dokploy.com/docs/core/docker-compose/example) - Sample configurations
- [Domains - Docker Compose](https://docs.dokploy.com/docs/core/docker-compose/domains) - Domain configuration
- [Environment Variables](https://docs.dokploy.com/docs/core/variables) - Environment variable management
- [Volume Backups](https://docs.dokploy.com/docs/core/volume-backups) - Volume backup features
- [Auto Deploy](https://docs.dokploy.com/docs/core/auto-deploy) - Auto-deployment setup
- [Watch Paths](https://docs.dokploy.com/docs/core/watch-paths) - Selective deployment triggers
- [Webhook](https://docs.dokploy.com/docs/core/webhook) - Webhook notifications
- [Monitoring](https://docs.dokploy.com/docs/core/monitoring) - Monitoring and metrics
- [Troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting) - Common issues and solutions
- [Rollbacks](https://docs.dokploy.com/docs/core/applications/rollbacks) - Deployment rollback features
- [Advanced](https://docs.dokploy.com/docs/core/applications/advanced) - Advanced configuration options
- [Going Production](https://docs.dokploy.com/docs/core/applications/going-production) - Production deployment guide

### External Resources
- [tRPC Error Handling](https://trpc.io/docs/server/error-handling) - tRPC error documentation
- [Dokploy GitHub Repository](https://github.com/dokploy/dokploy) - Open source repository
- [Dokploy trpc-openapi](https://github.com/Dokploy/trpc-openapi) - Custom tRPC-OpenAPI integration
- [GitHub PR #904](https://github.com/Dokploy/dokploy/pull/904) - App Name Handling Fix
- [GitHub PR #1562](https://github.com/Dokploy/dokploy/pull/1562) - App Name Auto-generation
- [GitHub Issue #2777](https://github.com/Dokploy/dokploy/issues/2777) - Environment Variables Bug
- [GitHub Issue #3130](https://github.com/Dokploy/dokploy/issues/3130) - 4MB TRPC Limit
- [v0.22.0 Release Notes](https://dokploy.com/blog/v0-22-0-docker-compose-backups-schedule-tasks-logs) - Docker Compose Backups, Schedule Tasks, Logs
- [Webhook.site](https://webhook.site) - Webhook testing tool
