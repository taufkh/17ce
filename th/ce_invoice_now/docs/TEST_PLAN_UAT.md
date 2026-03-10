# UAT Test Plan

## Purpose
Validate `ce_invoice_now` functional behavior in a user acceptance environment.

## 1. Test Preconditions
- Module installed and visible in Apps.
- Valid configuration record exists.
- Datapost endpoint connectivity is available.
- Test users have required access rights.

## 2. Positive Scenarios

### UAT-01 Generate Token
- Steps:
  1. Open CE InvoiceNow Configuration.
  2. Fill valid credentials.
  3. Click Generate Token.
- Expected:
  - Access token is stored.

### UAT-02 Send Customer Invoice
- Steps:
  1. Mark partner as applicable.
  2. Post customer invoice.
  3. Attach XML.
  4. Click CE InvoiceNow and Send.
- Expected:
  - Send code/content populated.
  - `ce_send_invoice_status = True` for successful response.
  - `ce_client_ref` populated.

### UAT-03 Send Credit Note
- Steps:
  1. Post customer credit note.
  2. Attach XML.
  3. Send via CE InvoiceNow wizard.
- Expected:
  - Submission processed with credit-note config path.

### UAT-04 Poll Status via Cron
- Steps:
  1. Ensure cron is active.
  2. Wait one run cycle or trigger manually.
- Expected:
  - Status code/content updated.
  - `ce_is_completed = True` when Datapost status is Completed.

## 3. Negative Scenarios

### UAT-05 Send Without XML
- Steps:
  1. Open posted invoice without XML attachment.
  2. Click CE InvoiceNow.
- Expected:
  - User error indicating XML attachment is required.

### UAT-06 Invalid Credential
- Steps:
  1. Set wrong credentials.
  2. Click Generate Token.
- Expected:
  - Token generation error is shown.

### UAT-07 Non-Applicable Partner
- Steps:
  1. Keep partner applicability unchecked.
  2. Try send flow.
- Expected:
  - Submission should be skipped by internal logic.

### UAT-08 Wrong Endpoint
- Steps:
  1. Set invalid base/status URI.
  2. Run send or status check.
- Expected:
  - Error or non-200 response captured for troubleshooting.

## 4. Evidence to Capture
- Screenshots of configuration.
- Invoice status tab before/after send.
- Response codes and content.
- Cron execution evidence.

## 5. Exit Criteria
- All positive scenarios pass.
- Negative scenarios produce expected errors safely.
- No blocking defects remain.
