# Limitations and Assumptions

## 1. Scope Assumptions
- Module is designed for Odoo 16 Community Edition.
- Datapost credentials and endpoints are provided by customer.

## 2. Key Limitation: XML Generation
This module does not generate EDI XML by itself in CE.

Assumption:
- XML invoice/credit note file is already available as invoice attachment.

## 3. No Enterprise EDI Dependencies
Removed by design:
- `account_edi`
- `account_edi_ubl_cii`
- UBL template inheritance from enterprise EDI stack

Impact:
- Transport and status tracking are covered.
- EDI template rendering is out of scope for this module.

## 4. Single Configuration Pattern
Operational assumption:
- One primary active configuration record is used per environment.

If multiple records exist:
- Current implementation reads first record (`search([], limit=1)`).

## 5. Datapost API Dependency
Integration behavior depends on external Datapost availability and API behavior.

Out of module control:
- Upstream outages
- API contract changes
- Tenant permission changes

## 6. Retry and Idempotency Consideration
- Safe retry policy must be governed by business team.
- Duplicate submission prevention is process-dependent.

## 7. Runtime Validation Boundaries
Without installation/runtime test in Odoo server:
- Static checks can pass while environment-specific issues still exist.

## 8. Recommended Future Enhancements
- Optional strict configuration selector (single active record).
- Retry policy controls with explicit audit notes.
- Optional endpoint health check action.
