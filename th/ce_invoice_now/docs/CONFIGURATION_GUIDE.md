# Configuration Guide

## Purpose
This guide explains runtime configuration for Datapost integration in `ce_invoice_now`.

## 1. Configuration Menu
Navigate to:
- **Accounting > Configuration > CE InvoiceNow Configuration**

Create one active configuration record.

## 2. Field-by-Field Setup
- `Name`: Internal label for your team.
- `Client ID`: Datapost client ID.
- `Secret Key`: Datapost secret key.
- `Auth URI`: Token endpoint.
- `Base URI`: Submit endpoint base.
- `Status URI`: Status query endpoint base.
- `API Version`: API version segment (default `v10`).
- `Invoice Document Type`: Usually `invoices`.
- `Invoice Document Format`: Usually `peppol-invoice-2`.
- `Credit Note Document Type`: Usually `credit-notes`.
- `Credit Note Document Format`: Usually `peppol-credit-note-2`.

## 3. Environment Profiles

### 3.1 Sandbox Profile (example)
- Use Datapost sandbox credentials.
- Set sandbox `Auth URI`, `Base URI`, and `Status URI`.

### 3.2 Production Profile (example)
- Use production credentials.
- Set production `Auth URI`, `Base URI`, and `Status URI`.

## 4. Token Generation
- Click **Generate Token**.
- Verify `Access Token` is populated.

If token is empty:
- Re-check credentials.
- Re-check `Auth URI`.
- Confirm outbound network access.

## 5. Customer Eligibility
On customer partner:
- Enable `Applicable for CE InvoiceNow?`.

Only eligible partners are submitted by send flow.

## 6. Invoice Prerequisites
For each invoice/credit note:
- Must be posted (`out_invoice` or `out_refund`).
- Must have at least one XML attachment.

## 7. Status Polling
Verify scheduled action:
- `CE InvoiceNow :: Check Status`
- Interval: hourly

## 8. Recommended Controls
- Restrict configuration edit access to accounting managers.
- Keep one active config record per environment.
- Document and version-control endpoint changes.
