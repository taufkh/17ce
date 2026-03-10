# CE InvoiceNow

`ce_invoice_now` is a Community Edition compatible Datapost InvoiceNow integration module.

## Documentation Index
- Feature and migration details:
  - `docs/FEATURES_AND_COMMUNITY_MIGRATION.md`
- Static smoke test evidence:
  - `docs/SMOKE_TEST_REPORT.md`
- Datapost connectivity test scenarios:
  - `docs/DATAPOST_CONNECTION_TEST_SCENARIOS.md`
- Auto XML generation technical design:
  - `docs/AUTO_XML_GENERATION_DESIGN.md`

## Goal
- Send posted customer invoices and credit notes (XML attachment) to Datapost InvoiceNow.
- Track request and processing status on invoice form.
- Poll document status periodically via scheduled action.

## Community Edition Compatibility
This module is intentionally built for Odoo CE and only depends on:
- `account`
- `mail`

It does **not** depend on `account_edi` / `account_edi_ubl_cii`.

## Quick Flow
1. Configure CE InvoiceNow credentials and endpoints.
2. Generate token.
3. Enable partner eligibility.
4. Post invoice/credit note with XML attachment.
5. Click `CE InvoiceNow` and send.
6. Monitor status from invoice status tab.
