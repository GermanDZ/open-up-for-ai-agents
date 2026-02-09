# API Reference Documentation

This file provides detailed instructions for generating API reference documentation from code and design documents.

## When to Generate API References

Generate API references when:
- Implementing REST or GraphQL APIs
- Creating SDKs or client libraries
- Documenting internal APIs for other teams
- Preparing for external API release

## Process

### 1. Identify API Endpoints

From code and design documents, identify:
- All HTTP endpoints (GET, POST, PUT, DELETE, PATCH)
- GraphQL queries and mutations
- WebSocket events
- RPC methods

Sources:
- Route definitions in code (e.g., Express.js routes, Spring controllers)
- API design documents: `docs/design/*api*.md`
- OpenAPI/Swagger specifications
- Postman collections

### 2. Document Authentication

Extract authentication details:
- Authentication method (API key, OAuth2, JWT, etc.)
- How to obtain credentials
- Where to include credentials in requests
- Token refresh logic (if applicable)

### 3. Document Base URLs

Identify environment-specific URLs:
- Production URL
- Staging/testing URL
- Development URL
- API versioning scheme

### 4. Document Each Endpoint

For each endpoint, document:

**Request Details:**
- HTTP method and path
- Path parameters (with types and validation)
- Query parameters (with types, defaults, and validation)
- Request headers (especially auth headers)
- Request body schema (for POST/PUT/PATCH)

**Response Details:**
- Success response status codes
- Success response body schema
- Error response format
- Error codes and meanings

**Examples:**
- Sample request (curl, JavaScript, Python)
- Sample response for success
- Sample response for errors

### 5. Extract Request/Response Schemas

From code, extract:
- Request validation rules
- Response structure
- Data types and constraints
- Required vs optional fields
- Enum values

Look for:
- TypeScript interfaces/types
- JSON Schema definitions
- Pydantic models
- Javadoc/KDoc comments
- OpenAPI annotations

### 6. Document Error Handling

For each error code:
- HTTP status code
- Error code/identifier
- Error message
- Common causes
- How to resolve

Common error codes to document:
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 409 Conflict
- 422 Unprocessable Entity
- 429 Rate Limit Exceeded
- 500 Internal Server Error
- 503 Service Unavailable

### 7. Document Rate Limiting

If applicable:
- Rate limit rules per tier/user
- Rate limit headers
- What happens when limits are exceeded
- How to request higher limits

### 8. Generate Code Examples

Create examples in multiple languages:
- cURL (always include)
- JavaScript/TypeScript (fetch, axios)
- Python (requests)
- Java (OkHttp, HttpClient)
- Go (net/http)

Each example should:
- Be complete and runnable
- Use realistic data
- Include error handling
- Show response parsing

### 9. Create SDK Sections (if applicable)

If SDKs exist:
- List available SDKs with versions
- Installation instructions
- Quick start example
- Link to full SDK documentation

### 10. Add Changelog

Document API changes:
- Breaking changes (highlight prominently)
- New features
- Deprecations (with removal dates)
- Bug fixes

## Output Format

API references are typically created as:
- OpenAPI/Swagger specification (machine-readable)
- Markdown documentation
- HTML documentation with search
- Interactive API explorers

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Missing error codes | Document all possible error responses |
| No authentication details | Clearly show how to authenticate |
| Outdated examples | Generate examples from actual API specs |
| Missing rate limits | Document rate limiting clearly |
| No deprecation policy | Add versioning and deprecation info |
