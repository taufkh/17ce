# Auto XML Generation Design (Community Edition)

## 1. Objective
Enable `ce_invoice_now` to auto-generate invoice/credit-note XML in Odoo CE before sending to Datapost, without relying on `account_edi` / `account_edi_ubl_cii`.

## 2. Design Principles
- Keep Community Edition compatibility.
- Generate deterministic XML from `account.move` data.
- Validate XML before attachment and submission.
- Allow configuration per company/environment.
- Keep transport (Datapost send/status) separated from XML builder logic.

## 3. Target Output
- XML file attached automatically to invoice (`ir.attachment`).
- Naming convention:
  - Invoice: `<invoice_number>_ce.xml`
  - Credit note: `<credit_note_number>_ce.xml`
- Optional profile modes:
  - `minimal`: internal schema-compliant XML
  - `datapost`: Datapost-required structure profile

## 4. Proposed Architecture

### 4.1 New Service Layer
Add service module under `ce_invoice_now/services/`:
- `xml_builder.py`
- `xml_mapper.py`
- `xml_validator.py`
- `xml_renderer.py`

Responsibilities:
- `xml_mapper`: map Odoo records to normalized payload dict.
- `xml_renderer`: build XML tree from normalized payload.
- `xml_validator`: structural checks + business rules.
- `xml_builder`: orchestrate map -> render -> validate -> attach.

### 4.2 New Model Extensions

#### `account.move` fields
- `ce_xml_generation_state` (`draft`, `generated`, `error`)
- `ce_xml_attachment_id` (Many2one `ir.attachment`)
- `ce_xml_error_message` (Text)
- `ce_xml_generated_at` (Datetime)
- `ce_xml_hash` (Char)

#### `ce.invoice.now.configuration` fields
- `ce_xml_auto_generate` (Boolean)
- `ce_xml_profile` (Selection: `minimal`, `datapost`)
- `ce_xml_force_regenerate` (Boolean)
- `ce_xml_include_tax_breakdown` (Boolean)

## 5. Generation Trigger Strategy

### 5.1 Manual Trigger
Button on invoice:
- `Generate CE XML`

### 5.2 Pre-send Auto Trigger
Inside send wizard flow:
1. If no XML attachment found and `ce_xml_auto_generate = True`:
2. Generate XML.
3. Attach generated XML.
4. Continue Datapost submission.

### 5.3 Optional Auto Trigger on Post (Phase 2)
Hook after invoice post to pre-generate XML for eligible documents.

## 6. XML Content Mapping (Minimum Viable)

### 6.1 Header
- document id (`move.name`)
- issue date (`invoice_date`)
- due date (`invoice_date_due`)
- currency (`currency_id.name`)
- document type (`out_invoice` / `out_refund`)

### 6.2 Supplier
- company name
- VAT / tax ID
- address lines
- country code

### 6.3 Customer
- partner name
- VAT / tax ID
- address lines
- country code

### 6.4 Lines
For each invoice line:
- line number
- product name
- quantity
- unit price
- discount
- tax code/rate
- line subtotal

### 6.5 Totals
- untaxed total
- tax total
- grand total
- rounding (if any)

## 7. Validation Rules

## 7.1 Structural Validation
- XML is well-formed.
- Mandatory nodes exist.
- Numeric fields are formatted consistently.

### 7.2 Business Validation
- Document must be posted.
- Partner must exist.
- At least one invoice line.
- Currency and invoice dates must be present.

### 7.3 Integrity Validation
- Generated hash stored in `ce_xml_hash`.
- Prevent duplicate attachment spam for identical content.

## 8. Attachment Strategy
- Store generated XML as binary attachment linked to `account.move`.
- Replace old CE-generated attachment only when:
  - invoice changed and hash changed, or
  - `ce_xml_force_regenerate = True`.

## 9. Error Handling
- If generation fails:
  - set `ce_xml_generation_state = error`
  - store details in `ce_xml_error_message`
  - block send action with explicit user message
- If validation fails:
  - no submission to Datapost
  - show field-level reason summary

## 10. Security and Audit
- Log generation events without exposing secrets.
- Track:
  - generator user
  - generation timestamp
  - profile used
- Keep one latest valid CE XML attachment reference on invoice.

## 11. Performance Considerations
- Typical invoice generation is lightweight.
- For bulk operations, use queue/cron batch generation.
- Avoid repeated regeneration by hash comparison.

## 12. Implementation Roadmap

### Phase 1 (MVP)
- Manual `Generate CE XML` button.
- Minimal XML profile.
- Validation + attachment save.
- Send flow consumes generated XML.

### Phase 2
- Auto-generate during send if XML missing.
- Force regenerate option.
- Enhanced tax/discount mapping.

### Phase 3
- Auto-generate on posting.
- Multi-profile support (`minimal`, `datapost`).
- Extended diagnostics and monitoring KPIs.

## 13. Test Scenarios (Design-Level)
- Generate XML for posted invoice with single line.
- Generate XML for multi-line + tax invoice.
- Generate XML for credit note.
- Regenerate after invoice line update.
- Send flow with no XML + auto-generate enabled.
- Send flow blocked when generation fails.

## 14. Risks and Mitigations
- Risk: Datapost requires stricter schema than MVP.
  - Mitigation: profile-based renderer and validation suite.
- Risk: invoice data quality inconsistency.
  - Mitigation: pre-validation and explicit user errors.
- Risk: duplicate sends with stale XML.
  - Mitigation: hash/version control and regenerate policy.

## 15. Recommended First Build
Implement Phase 1 + pre-send auto-generate fallback only.
This gives immediate business value while minimizing complexity and preserving CE compatibility.
