# Datapost Connection Test Scenarios

## Purpose
This document defines practical test scenarios to confirm whether Datapost API integration is reachable and functioning.

## Scope
Covers:
- Network connectivity
- Authentication connectivity
- Submission connectivity
- Status-query connectivity

## Test Data Prerequisites
- Valid Datapost credentials (`client_id`, `secret_key`).
- Correct endpoint URIs for the target environment.
- One test customer marked `Applicable for CE InvoiceNow?`.
- One posted test invoice with XML attachment.

## Scenario Group A: Network Reachability

### A-01 DNS and HTTPS Reachability
Objective:
- Verify host and TLS path are reachable from Odoo runtime environment.

Example command (run from Odoo container/host):
```bash
curl -I https://peppol.datapost.com.sg
```

Expected result:
- HTTP response headers returned (not timeout).

Fail indicators:
- DNS resolution failure
- Connection timeout
- TLS handshake failure

Actions if failed:
- Check firewall/egress rules.
- Check proxy settings.
- Check DNS resolution inside runtime container.

## Scenario Group B: Authentication API

### B-01 Token Generation via Odoo UI
Objective:
- Verify auth endpoint and credentials are valid.

Steps:
1. Open CE InvoiceNow configuration.
2. Fill `client_id`, `secret_key`, and `auth_uri`.
3. Click **Generate Token**.

Expected result:
- `access_token` is populated.
- No user error is shown.

Fail indicators:
- 401/403 response
- timeout
- invalid JSON response

### B-02 Token Generation via API (optional direct test)
Objective:
- Isolate API-level auth outside Odoo UI.

Example command:
```bash
curl -X POST "$AUTH_URI" \
  -H "Content-Type: application/json" \
  -d '{"clientId":"<CLIENT_ID>","secret":"<SECRET_KEY>"}'
```

Expected result:
- JSON includes `access_token`.

## Scenario Group C: Submission API

### C-01 Invoice Submit from Odoo
Objective:
- Verify `PUT` submission path works end-to-end.

Steps:
1. Create posted `out_invoice`.
2. Attach XML file.
3. Click **CE InvoiceNow**.
4. Click **Send**.

Expected result:
- `ce_send_invoice_req_status` is `200` or `202`.
- `ce_send_invoice_status` is `True`.
- `ce_client_ref` is populated.

Fail indicators:
- 4xx/5xx response
- empty `ce_client_ref`

### C-02 Credit Note Submit
Objective:
- Verify credit-note path and config mapping.

Steps:
1. Create posted `out_refund`.
2. Attach XML file.
3. Send via CE InvoiceNow wizard.

Expected result:
- Submission succeeds with credit-note endpoint path.

## Scenario Group D: Status API

### D-01 Scheduled Polling Validation
Objective:
- Verify status endpoint integration through cron.

Steps:
1. Ensure invoice has `ce_client_ref`.
2. Ensure cron is active: `CE InvoiceNow :: Check Status`.
3. Wait one cron cycle or trigger manually.

Expected result:
- `ce_invoice_status` and `ce_invoice_status_content` updated.
- `ce_is_completed = True` when Datapost status is completed.

### D-02 Manual API Status Check (optional direct test)
Objective:
- Isolate status endpoint response outside Odoo UI.

Example command:
```bash
curl -X GET "$STATUS_URL" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

Expected result:
- JSON response with document status payload.

## Scenario Group E: Negative Connectivity Tests

### E-01 Invalid Credential
- Set wrong secret key.
- Expected: token generation fails with authorization error.

### E-02 Invalid Auth URI
- Set invalid `auth_uri`.
- Expected: connection or endpoint error.

### E-03 Invalid Base URI
- Set invalid `base_uri` and send invoice.
- Expected: submission fails; response/error captured.

### E-04 Missing XML Attachment
- Attempt send without XML.
- Expected: user-facing validation error.

## Pass/Fail Criteria
Integration is considered connected and functional when all mandatory checks pass:
- A-01 reachability pass
- B-01 token generation pass
- C-01 invoice submit pass
- D-01 status polling pass

## Evidence Checklist
Collect and store:
- Timestamp per scenario
- Endpoint values used
- Request/response status codes
- Odoo invoice screenshots (status tab)
- Any error messages/log excerpts

## Recommended Execution Order
1. A-01
2. B-01
3. C-01
4. D-01
5. C-02
6. Negative tests (E-01 to E-04)
