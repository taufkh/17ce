# Operations Runbook

## Purpose
Operational procedures for monitoring and supporting `ce_invoice_now` in production-like environments.

## 1. Daily Monitoring Checklist
- Confirm scheduler `CE InvoiceNow :: Check Status` is active.
- Review latest posted invoices with `ce_send_invoice_status = True` and `ce_is_completed = False`.
- Check response codes and response content for anomalies.

## 2. Key Monitoring Points
- Token generation failures.
- Submission failures (`4xx`/`5xx`).
- Status polling failures.
- Repeated non-completed invoices beyond expected SLA.

## 3. Incident Handling Procedure
1. Capture evidence:
   - invoice ID/number
   - response code/content
   - timestamp
2. Determine stage:
   - auth
   - submit
   - status polling
3. Apply recovery:
   - refresh/fix configuration
   - retry submission if business-approved
   - validate endpoint/network availability
4. Document root cause and final action.

## 4. Escalation Criteria
Escalate if:
- Repeated auth failure for valid credentials.
- API returns persistent `5xx`.
- Multiple invoices stuck in non-completed state beyond agreed SLA.

## 5. Data Integrity Checks
- Ensure `ce_client_ref` is set for successful sends.
- Ensure `ce_invoice_status` is periodically updated by cron.
- Ensure completed documents are flagged with `ce_is_completed = True`.

## 6. Safe Retry Policy
- Retry only for non-completed and failed submissions.
- Avoid duplicate business submissions without approval.
- Keep audit note of each retry attempt.

## 7. Backup and Recovery
- Include database backup in standard operational backup cycle.
- Preserve invoice status and response content for audit traceability.
