# Iconn Access Right Test Scenarios (UAT)

## Scope

This document is used to validate:

- `Access Rights` (group/role assignments)
- `Record Rules` (domain restrictions)
- `ICONN ACCESS` wrapper role implementation
- Contact/Company access matrix (`res.partner`)

Target database: `iconn_dev`

Primary module:

- `iconn_user_access_setup`

## Preconditions (Required)

1. Module `iconn_user_access_setup` is already `installed`.
2. Seed users are available (24 users).
3. Testing is performed in incognito/private browser sessions (one session per user).
4. Prepare minimum test data:
   - At least 2 sales teams with different members
   - CRM leads owned by different users
   - Sales orders in states: `draft`, `sent`, `sale`
   - Purchase orders owned by different users
   - Stock pickings of type `incoming`, `outgoing`, `internal`
   - Vendor Bills (`account.move` with `in_invoice`) and Customer Invoices (`out_invoice`)
   - Contacts/companies:
     - Approved company
     - Draft company
     - Rejected company
     - Contact under approved company
     - Contact under draft company

## Pass/Fail Rule

- `PASS`: Actual result matches expected outcome.
- `FAIL`: User can access data/actions that should be restricted, or cannot perform actions that should be allowed.

## Quick Role Mapping (Current Implementation)

- `keith.goh@mail.com` -> Admin (`Administration / Settings`)
- `nick@mail.com`, `rajesh@mail.com` -> `Iconn / Sales Manager`
- `adarsh/alma/david/hemanth/naidu/ray/yeoh` -> `Iconn / Sales Executive`
- `alicia.liew@mail.com`, `veena@mail.com` -> `Iconn / Sales Operations`
- `lyvian@mail.com`, `louise@mail.com` -> `Iconn / Purchasing`
- `barry@mail.com` -> `Iconn / Warehouse Incoming Only`
- `rashim@mail.com` -> `Iconn / Warehouse User`
- `federick@mail.com` -> `Iconn / Warehouse Manager`
- `sk@mail.com`, `kewei@mail.com` -> `Iconn / Finance Officer`
- `jenny@mail.com`, `shermaine@mail.com` -> `Iconn / Finance Processing`
- `margaret@mail.com` -> `Iconn / Customer Service`

## Scenario Group A: User/Role Assignment

### A1. Verify wrapper role appears on user form

- Users: `Alicia`, `Nick`, `Margaret`, `Barry`, `SK`
- Steps:
  1. Open `Settings > Users & Companies > Users`
  2. Open each user record
  3. Check the `ICONN ACCESS` section
- Expected:
  - `Alicia`: `Iconn / Sales Operations` + `Iconn / Warehouse Manager`
  - `Nick`: `Iconn / Sales Manager` (+ `Project Manager` if assigned)
  - `Margaret`: `Iconn / Customer Service`
  - `Barry`: `Iconn / Warehouse Incoming Only`
  - `SK`: `Iconn / Finance Officer`

### A2. Verify standard role summary fields (upper section) are logically populated

- Steps:
  1. In the same user forms, check standard module role summaries (Sales, Purchase, Inventory, Invoicing, etc.)
- Expected:
  - Values are populated based on implied groups from wrapper roles.
  - Not every field must be populated.
  - Non-relevant fields may remain empty.

## Scenario Group B: CRM / Sales Record Rules

### B1. Sales Executive can see only own CRM leads

- User: `adarsh@mail.com` (or any Sales Executive)
- Steps:
  1. Login as Sales Executive
  2. Open CRM pipeline
  3. Compare visible leads with leads owned by another Sales Executive
- Expected:
  - User can only see leads with `user_id = current user`
  - Leads owned by other users are not visible

### B2. Sales Executive can see only own Sales Orders

- User: `yeoh@mail.com`
- Steps:
  1. Open Sales Orders list
  2. Compare own SOs vs SOs owned by other users
- Expected:
  - Only own Sales Orders are visible

### B3. Sales Manager can see team documents (not global all documents)

- User: `nick@mail.com` or `rajesh@mail.com`
- Steps:
  1. Open CRM Leads and Sales Orders
  2. Verify records owned by same team
  3. Verify records owned by a different team
- Expected:
  - User can see records:
    - owned by self
    - in teams they manage (`team_id.user_id`)
    - in teams where they are a member (`team_id.member_ids`)
  - User cannot see records from unrelated teams (unless another group grants access)

### B4. Sales Operations can view all CRM leads

- User: `veena@mail.com`
- Steps:
  1. Open CRM Leads
- Expected:
  - Can view leads across users (no owner restriction)

### B5. Sales Operations Sales Orders limited to `sent/sale`

- User: `alicia.liew@mail.com`
- Steps:
  1. Open Sales Orders list
  2. Ensure there are SOs in states `draft`, `sent`, `sale`
- Expected:
  - Only SOs in `sent` and `sale` are visible
  - `draft` SOs are not visible

### B6. Customer Service (Margaret): CRM own only + SO draft own only

- User: `margaret@mail.com`
- Steps:
  1. Open CRM Leads
  2. Open Sales Orders
  3. Ensure Margaret has SOs in `draft`, `sent`, and `sale`
- Expected:
  - CRM: only own leads are visible
  - Sales Orders: only own SOs in `draft` are visible
  - Margaret's SOs in `sent/sale` are not visible

## Scenario Group C: Purchase / Inventory Record Rules

### C1. Purchasing role can see only own Purchase Orders

- User: `lyvian@mail.com` or `louise@mail.com`
- Steps:
  1. Open Purchase Orders list
  2. Compare own POs vs POs owned by other users
- Expected:
  - Only own POs are visible (`user_id = current user`)

### C2. Sales Operations can view all Purchase Orders

- User: `alicia.liew@mail.com` or `veena@mail.com`
- Steps:
  1. Open Purchase Orders list
- Expected:
  - Can view POs across owners

### C3. Barry can only see incoming Stock Pickings

- User: `barry@mail.com`
- Steps:
  1. Open Transfers / Stock Pickings
  2. Compare incoming, outgoing, and internal transfers
- Expected:
  - Only `incoming` pickings are visible
  - `outgoing` and `internal` pickings are not visible

### C4. Warehouse User/Manager behavior unaffected (except Barry special role)

- Users: `rashim@mail.com`, `federick@mail.com`
- Steps:
  1. Open stock operations
- Expected:
  - Behavior follows their standard inventory role access
  - They are not affected by Barry's incoming-only restriction

## Scenario Group D: Finance / Invoicing Record Rules

### D1. Finance Processing sees Vendor Bills only

- User: `jenny@mail.com` or `shermaine@mail.com`
- Steps:
  1. Open Invoicing > Journal Entries / Invoices (based on visible menu)
  2. Ensure both `in_invoice` and `out_invoice` records exist
- Expected:
  - Only Vendor Bills (`move_type = 'in_invoice'`) are visible
  - Customer Invoices (`out_invoice`) are not visible

### D2. Finance Officer has broader invoicing access

- User: `sk@mail.com` or `kewei@mail.com`
- Steps:
  1. Open Invoicing screens
  2. Check visibility across invoice types
- Expected:
  - Access follows Finance Officer wrapper + standard accounting groups
  - No custom invoice record rule restricts visibility to one invoice type

## Scenario Group E: Contact / Company Matrix (`res.partner`)

### E0. Data setup validation (company approval status)

- Steps:
  1. Open Company records
  2. Check field `Iconn Company Approval Status`
- Expected:
  - Existing companies (backfilled) are set to `approved`
  - New company default is `draft`

### E1. Sales Executive - Read contacts/companies

- User: `adarsh@mail.com`
- Steps:
  1. Open Contacts
  2. Open both individual contacts and company records
- Expected:
  - Can read both individual contacts and companies

### E2. Sales Executive - Create new company (draft only)

- User: `adarsh@mail.com`
- Steps:
  1. Create a new company
  2. Save
  3. Check `Iconn Company Approval Status`
- Expected:
  - Create succeeds
  - New company status is `draft`

### E3. Sales Executive - Create individual contact only under approved company

- User: `adarsh@mail.com`
- Steps:
  1. Try creating a contact under an approved company
  2. Try creating a contact under a draft company
- Expected:
  - Under approved company: allowed
  - Under draft company: blocked by record rule/access restriction

### E4. Sales Executive - Cannot hard delete partner/company

- User: `adarsh@mail.com`
- Steps:
  1. Try deleting a partner/company
- Expected:
  - Delete is blocked
  - Archive behavior depends on write permission and record state

### E5. Sales Manager - Similar to Sales Executive, but wider limited write access

- User: `nick@mail.com`
- Steps:
  1. Edit a draft company
  2. Edit an approved company master data
- Expected:
  - Draft company edit is allowed
  - Approved company edit is restricted (unless another role grants broader access)

### E6. Customer Service - Can manage company lifecycle (no hard delete)

- User: `margaret@mail.com`
- Steps:
  1. Read any contact/company
  2. Create draft company
  3. Edit company status to `approved` or `rejected`
  4. Archive company (`active = False`)
  5. Try hard delete
- Expected:
  - Read all allowed
  - Create draft company allowed
  - Approve/Reject via status field update allowed
  - Archive allowed (write access)
  - Hard delete blocked

### E7. Finance Processing - Read only on Contacts/Companies

- User: `jenny@mail.com`
- Steps:
  1. Open contacts/companies
  2. Try create/edit/delete
- Expected:
  - Read allowed
  - Create/edit/delete blocked

### E8. Finance Officer - Tax-only edit on approved companies (VAT only)

- User: `sk@mail.com`
- Steps:
  1. Open an approved company, edit `VAT`, and save
  2. Open an approved company, edit `Name`, and save
  3. Open an individual contact, edit `VAT`, and save
  4. Open a draft company, edit `VAT`, and save
- Expected:
  - Edit `VAT` on approved company: allowed
  - Edit non-tax field (e.g. `Name`): blocked (`AccessError`)
  - Edit `VAT` on individual contact: blocked
  - Edit `VAT` on draft company: blocked
  - Create/delete remains blocked

## Scenario Group F: Negative Tests (Security Regression Check)

### F1. Cross-role visibility leak check

- Users: Sales Executive, Customer Service, Finance Processing
- Steps:
  1. Try to access records outside expected domain (other user's SO, customer invoice, outgoing picking, etc.)
- Expected:
  - No unauthorized records are visible

### F2. Admin bypass check

- User: `keith.goh@mail.com`
- Steps:
  1. Access all modules and records listed above
- Expected:
  - No restriction issues (global admin access)

## Known Gaps / Not Yet Fully Implemented

1. `Regional rules` (SG/PH/VN/etc.) are not implemented yet
2. `Finance tax-only` currently whitelists only `VAT`
3. `Sales Manager approve/reject company` is still “limited” (not optional toggle yet)
4. `Warehouse Controller (Federick)` does not yet have a dedicated custom rule set separate from standard inventory behavior

## Test Evidence Template (Per Scenario)

Use this format during UAT:

- Scenario ID:
- User:
- Date:
- Tester:
- Steps performed:
- Actual result:
- Expected result:
- Status: `PASS` / `FAIL`
- Screenshot / attachment:
- Notes:
