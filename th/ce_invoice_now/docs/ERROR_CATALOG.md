# Error Catalog

## Purpose
Reference for common errors and recommended corrective actions.

## 1. Authentication Errors

### 401 Unauthorized
Possible causes:
- Invalid `client_id` or `secret_key`
- Incorrect `Auth URI`

Actions:
- Verify credentials with Datapost.
- Verify environment endpoint (sandbox vs production).
- Regenerate token.

### 403 Forbidden
Possible causes:
- Credential exists but access scope is not allowed

Actions:
- Confirm account permissions with Datapost.
- Confirm endpoint and tenant alignment.

## 2. Submission Errors

### 400 Bad Request
Possible causes:
- Invalid request path or parameters
- Unsupported document type/format

Actions:
- Verify `document_type` and `document_format`.
- Verify URL composition from configuration fields.

### 404 Not Found
Possible causes:
- Wrong `base_uri` or API path

Actions:
- Validate endpoint base and API version.
- Confirm with Datapost API documentation.

### 415 Unsupported Media Type
Possible causes:
- Incorrect file content type

Actions:
- Ensure XML attachment is sent as `text/xml`.

### 422 Unprocessable Entity
Possible causes:
- XML business/validation issue

Actions:
- Validate XML content and mandatory business fields.
- Correct source XML and resend.

### 500/502/503/504 Server Errors
Possible causes:
- Upstream service instability

Actions:
- Retry with controlled interval.
- Escalate to Datapost if persistent.

## 3. Status Polling Errors

### Status endpoint returns non-200
Possible causes:
- Invalid/expired token
- Wrong status endpoint path

Actions:
- Regenerate token.
- Verify status URL configuration.

## 4. Local Validation Errors (Odoo)

### "No XML attachments available"
Possible causes:
- Invoice has no XML attachment

Actions:
- Attach valid XML first.

### "Access token is empty"
Possible causes:
- Token generation did not succeed

Actions:
- Fix configuration and regenerate token.

## 5. Troubleshooting Data to Collect
- Invoice number and ID
- Partner name
- Timestamp
- Request endpoint used
- HTTP status code
- Response body
- Current configuration snapshot
