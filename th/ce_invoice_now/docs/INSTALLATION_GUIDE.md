# Installation Guide (Odoo Community Edition)

## Purpose
This guide explains how to install and verify `ce_invoice_now` in Odoo 16 Community Edition.

## 1. Prerequisites
- Odoo 16 Community Edition is running.
- Module source is available at `addons/th/ce_invoice_now`.
- Addons path includes the `addons/th` directory.
- Required modules are available:
  - `account`
  - `mail`
- Outbound HTTPS access to Datapost endpoints is allowed.

## 2. Addons Path Check
Ensure your Odoo configuration includes the parent path that contains `ce_invoice_now`.

Example (`odoo.conf`):
```ini
addons_path = /usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons/th
```

## 3. Module Update List
Refresh apps list from Odoo UI or by command line.

Example:
```bash
docker compose exec -T web odoo -c /etc/odoo/odoo.conf -d <db_name> \
  --db_host=db --db_user=odoo --db_password=odoo -u ce_invoice_now --stop-after-init
```

## 4. Install Module
- Open Apps.
- Search for `CE Invoice Now`.
- Install.

## 5. Post-Install Verification
After installation, verify:
- Menu exists: **Accounting > Configuration > CE InvoiceNow Configuration**.
- New partner field exists: `Applicable for CE InvoiceNow?`.
- Invoice form shows:
  - button `CE InvoiceNow`
  - tab `CE InvoiceNow Status`.
- Scheduled action exists:
  - `CE InvoiceNow :: Check Status`.

## 6. Minimal Smoke Verification
1. Create CE InvoiceNow configuration record.
2. Generate token.
3. Mark one customer as applicable.
4. Post one customer invoice with XML attachment.
5. Use `CE InvoiceNow` send wizard.
6. Confirm status fields are updated.

## 7. Rollback
If rollback is required:
- Disable module usage in operations.
- Uninstall `ce_invoice_now` from Apps (only after impact review).
- Keep backup before uninstall.

## 8. Notes
- This module is CE-compatible and intentionally avoids `account_edi` / `account_edi_ubl_cii` dependencies.
- XML attachment generation must be handled by your CE-compatible process.
