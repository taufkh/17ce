# CE InvoiceNow: Feature Documentation and Community Migration Notes

## 1. Module Purpose
`ce_invoice_now` provides Datapost InvoiceNow integration for Odoo 16 Community Edition.

Primary objectives:
- Send posted customer invoices and credit notes to Datapost.
- Store outbound submission metadata on invoice records.
- Periodically check processing status from Datapost.

## 2. Functional Features

### 2.1 Configuration Management
Model: `ce.invoice.now.configuration`

Main configuration fields:
- `client_id`
- `secret_key`
- `auth_uri`
- `base_uri`
- `status_uri`
- `api_version`
- `inv_document_type` / `inv_document_format`
- `credit_document_type` / `credit_document_format`

Token fields:
- `access_token`
- `refresh_token`

Main action:
- `Generate Token` (`action_generate_token`)

### 2.2 Partner-Level Eligibility
Model extension: `res.partner`

Field:
- `ce_applicable_invoicenow` (Boolean)

Purpose:
- Only customers marked as applicable are processed for InvoiceNow submission.

### 2.3 Invoice Send Action
Model extension: `account.move`

Button on invoice form:
- `CE InvoiceNow` (`action_ce_invoice_now_sent`)

Behavior:
- Available for posted `out_invoice` / `out_refund`.
- Requires partner eligibility (`ce_applicable_invoicenow = True`).
- Opens send wizard with XML attachments.

### 2.4 Send Wizard
Models:
- `ce.send.invoice`
- `ce.send.invoice.line`

Core behavior:
- Loads selected posted invoice(s).
- Collects `.xml` attachments.
- Generates token from configuration.
- Sends document to Datapost via HTTP `PUT`.
- Stores response and generated client reference on invoice.

### 2.5 Invoice Status Tracking
Model extension: `account.move`

Tracking fields:
- `ce_client_ref`
- `ce_send_invoice_req_status`
- `ce_send_invoice_content`
- `ce_send_invoice_status`
- `ce_invoice_status_content`
- `ce_invoice_status`
- `ce_is_completed`

UI:
- `CE InvoiceNow Status` tab on invoice form.

### 2.6 Scheduled Status Polling
Cron:
- `CE InvoiceNow :: Check Status`
- Calls `account.move._check_ce_invoice_status()` every 1 hour.

Behavior:
- Finds non-completed posted customer invoices/credit notes with `ce_client_ref`.
- Calls Datapost status endpoint.
- Updates invoice status fields.
- Marks invoice as completed when Datapost returns `status = Completed`.

## 3. Datapost Integration Flow

### 3.1 Authentication
1. User configures `client_id`, `secret_key`, and `auth_uri`.
2. User clicks **Generate Token**.
3. Module sends `POST` request to auth endpoint.
4. On success, `access_token` is stored in configuration.

### 3.2 Submission
1. User opens posted invoice / credit note.
2. User clicks **CE InvoiceNow**.
3. Wizard loads invoice XML attachment(s).
4. Module sends `PUT` request to:
   - `{base_uri}/business/{api_version}/{document_type}/{document_format}/{client_ref}`
5. Response status/content are stored on invoice.

### 3.3 Status Query
1. Cron calls `_check_ce_invoice_status()`.
2. Module sends `GET` request to:
   - `{status_uri}/business/{api_version}/{inv_document_type}/{inv_document_format}/{client_ref}.json`
3. Response content/code are stored.
4. If Datapost status is `Completed`, invoice is marked completed.

## 4. What Was Changed from Enterprise-Oriented Version to Community-Ready Version

This section details the migration work performed from the original `invoice_now` implementation to `ce_invoice_now`.

### 4.1 Dependency Refactor for CE
Removed enterprise-oriented dependencies:
- `account_edi`
- `account_edi_ubl_cii`

Current CE-safe dependencies:
- `account`
- `mail`

Impact:
- Module can be installed in Odoo Community without requiring EDI enterprise stack.

### 4.2 EDI-Specific Overrides Removed
Removed EDI inheritance logic tied to enterprise EDI models:
- `_inherit = "account.edi.xml.ubl_sg"`
- `_inherit = "account.edi.xml.ubl_20"`
- `_inherit = "account.edi.format"`

Impact:
- No hard dependency on EDI model registry.
- XML generation is expected to come from external process or existing attachments.

### 4.3 UBL Template Customizations Not Carried Forward
Original module contained UBL template overrides under `data/ubl_20_templates.xml`.
These were intentionally excluded from CE module.

Reason:
- Template inheritance relied on `account_edi_ubl_cii` templates.

Impact:
- CE module focuses on Datapost transport + status tracking, not EDI template extension.

### 4.4 Namespacing and Collision Prevention
All new models/fields/actions were namespaced with `ce_`:
- Models: `ce.invoice.now.configuration`, `ce.send.invoice`, `ce.send.invoice.line`
- Fields on `account.move`: `ce_*`
- Field on partner: `ce_applicable_invoicenow`
- XML IDs prefixed as `ce_...`

Impact:
- Safe coexistence with original `invoice_now` module.
- No method/field/action collision during deployment.

### 4.5 Endpoint and Token Handling Cleanup
Community version uses configurable endpoints and guarded HTTP requests with timeout.

Improvements applied:
- Dedicated configurable `auth_uri`, `base_uri`, `status_uri`.
- `requests` exception handling (`RequestException`).
- User-facing error messages via `UserError`.

### 4.6 Legacy Wizard Consolidation
Original source had dual wizard patterns.
Community version keeps one consistent wizard flow:
- `ce.send.invoice` + `ce.send.invoice.line`

Impact:
- Simpler maintenance.
- Clear submission path from invoice to Datapost.

### 4.7 Security Access Rework
Access controls adjusted for CE module objects:
- Config model for accounting managers.
- Send wizard models for internal users.

Impact:
- Practical permissions for accounting operations in CE.

## 5. Known Operational Constraint in CE
Because CE module does not include enterprise EDI generation stack:
- XML invoice file must exist as an attachment before submission.

Recommended process:
- Ensure invoice XML is generated by your existing CE-compatible process.
- Then use `CE InvoiceNow` button for submission and tracking.

## 6. Files Introduced for Community Module
- `models/invoice_now_configuration.py`
- `models/account_move.py`
- `models/res_partner.py`
- `wizard/send_invoice.py`
- `views/invoice_now_configuration_views.xml`
- `views/account_move_views.xml`
- `views/res_partner_views.xml`
- `wizard/send_invoice_views.xml`
- `data/ir_cron.xml`
- `security/ir.model.access.csv`

## 7. Validation Status
Static smoke checks were executed without installation:
- Python compile: PASS
- XML parse: PASS
- Manifest/data reference consistency: PASS
- CE dependency policy: PASS
- Access-model mapping sanity: PASS

Refer to `docs/SMOKE_TEST_REPORT.md` for details.
