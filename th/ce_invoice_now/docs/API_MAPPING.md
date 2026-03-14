# API Mapping

## Purpose
Technical mapping between Odoo CE InvoiceNow objects and Datapost API interactions.

## 1. Authentication Call

### Endpoint
`POST {auth_uri}`

### Request payload
```json
{
  "clientId": "<client_id>",
  "secret": "<secret_key>"
}
```

### Stored output
- `ce.invoice.now.configuration.access_token`
- `ce.invoice.now.configuration.refresh_token`

## 2. Submission Call

### Endpoint pattern
`PUT {base_uri}/business/{api_version}/{document_type}/{document_format}/{client_ref}`

### Request content
- multipart file field: `document`
- attachment source: `ir.attachment` XML file

### Mapping logic
- `document_type` from:
  - invoice: `inv_document_type`
  - credit note: `credit_document_type`
- `document_format` from:
  - invoice: `inv_document_format`
  - credit note: `credit_document_format`
- `client_ref`: generated UUID per submission

### Stored output on `account.move`
- `ce_send_invoice_req_status`
- `ce_send_invoice_content`
- `ce_send_invoice_status`
- `ce_client_ref`

## 3. Status Query Call

### Endpoint pattern
`GET {status_uri}/business/{api_version}/{inv_document_type}/{inv_document_format}/{client_ref}.json`

### Stored output on `account.move`
- `ce_invoice_status_content`
- `ce_invoice_status`
- `ce_is_completed` (set `True` when JSON field `status == "Completed"`)

## 4. Odoo Object Mapping Summary
- Config model: `ce.invoice.now.configuration`
- Partner eligibility field: `res.partner.ce_applicable_invoicenow`
- Send wizard: `ce.send.invoice`
- Send line: `ce.send.invoice.line`
- Invoice tracking fields: `account.move.ce_*`

## 5. Implementation Notes
- HTTP calls use token-based bearer authorization.
- Timeouts are applied for auth, submit, and status calls.
- Non-200 responses are preserved for diagnostics.
