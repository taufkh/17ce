# Changelog

## 2026-03-05

### Added
- New Community Edition module: `ce_invoice_now`.
- CE-compatible configuration model: `ce.invoice.now.configuration`.
- Partner applicability field: `res.partner.ce_applicable_invoicenow`.
- Invoice tracking fields (`account.move.ce_*`).
- Send wizard models:
  - `ce.send.invoice`
  - `ce.send.invoice.line`
- Hourly cron status polling: `CE InvoiceNow :: Check Status`.
- Documentation set under `docs/`.

### Changed (from enterprise-oriented implementation)
- Removed dependency on:
  - `account_edi`
  - `account_edi_ubl_cii`
- Removed EDI inheritance/UBL template coupling.
- Introduced CE-safe namespace prefix `ce_` for model/field/action IDs.
- Reworked endpoint configuration to explicit `auth_uri`, `base_uri`, `status_uri`.
- Consolidated operational send flow into CE wizard path.

### Validation
- Static smoke checks executed and passed:
  - Python compile
  - XML parsing
  - manifest/data consistency
  - dependency policy
  - access-model mapping sanity
