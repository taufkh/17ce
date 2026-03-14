# Iconn Access Security Architecture Definition

## 1. Objective of This Document
This document defines role-based access for Iconn in Odoo so reviewers can validate:
1. Every role definition
2. What each role can see
3. What each role can do
4. What each role cannot access
5. Controls to prevent payroll and confidential data leakage
6. A simple validation structure for Keith and management review

## 2. Security Principles
1. Least privilege by default
2. Manager and User roles are separated
3. Cross-department access is denied unless explicitly approved
4. Sensitive data (payroll, salary, confidential remarks) is denied unless explicitly approved
5. No hard-delete for sensitive master data (company/contact)

## 3. Role Overview Matrix (High-Level)
| Department | Role | Scope | Payroll Access | Leave/Claims Access | Purchasing Access | Warehouse Access | Reporting Visibility |
|---|---|---|---|---|---|---|---|
| Administration | Administrator | Global | Full system-level (if payroll apps installed) | Full | Full | Full | Full internal + export |
| Shipping | Shipping / Manager | Operational cross-flow (Sales Ops + Warehouse) | No payroll by design | Indirect from implied groups | Full PO view (rule-based) | Inventory Manager | Internal operational reports |
| Shipping | Shipping / User | Operational warehouse user | No | No dedicated approval | No | Warehouse user | Operational warehouse reports |
| Customer Service | Customer Service / Manager | Customer-facing records | No | User-level leave/expense visibility only | No | No | Customer-facing + own/team sales drafts |
| Customer Service | Customer Service / User | Customer-facing records | No | User-level leave/expense visibility only | No | No | Customer-facing + own/team sales drafts |
| Finance | Finance / Manager | Finance operations | No payroll by default policy | Manager-level leave/expense | No purchasing workflow | No | Full invoicing/internal finance reports |
| Finance | Finance / User | AP processing | No payroll by default policy | User-level leave/expense | No purchasing workflow | No | Vendor-bill focused reports |
| HR | HR / Manager | HR scope only | Denied until payroll role is explicitly defined | Expected HR manager scope | No | No | HR reports only |
| HR | HR / Assistant Manager | HR support scope | Denied until payroll role is explicitly defined | Expected HR support scope | No | No | HR support reports |
| HR | HR / User | HR user scope | Denied until payroll role is explicitly defined | Expected HR user scope | No | No | Basic HR reports |
| Sales | Sales Team / Country Manager | Team sales scope | No | Team approver (expenses) | No | No | Team pipeline + team sales |
| Sales | Sales Team / User | Own sales scope | No | User leave/expense | No | No | Own pipeline + own sales |
| Purchasing | Purchasing / Manager | Purchasing scope | No | User leave/expense | Own PO + purchasing ops | Stock user level | Purchasing reports |
| Purchasing | Purchasing / User | Purchasing scope | No | User leave/expense | Own PO + purchasing ops | Stock user level | Purchasing reports |
| Warehouse | Warehouse / Manager | Warehouse management scope | No | No dedicated approval | No | Inventory Manager | Full warehouse reports |
| Warehouse | Warehouse / Incoming Only | Inbound warehouse scope | No | No | No | Incoming picking only | Inbound warehouse reports |
| Warehouse | Warehouse / Outgoing Only | Outbound warehouse scope | No | No | No | Warehouse user (outbound process policy) | Outbound warehouse reports |
| FAE | Solution Engineering Cluster (FAE) / Manager | Pending final mapping | Denied by default | Pending | Pending | Pending | Pending |
| FAE | Solution Engineering Cluster (FAE) / User | Pending final mapping | Denied by default | Pending | Pending | Pending | Pending |
| Marketing | Marketing / Manager | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Marketing | Marketing / User | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Product | Product Manager / Manager | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Product | Product Manager / User | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Quote | Quote Team / Manager | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Quote | Quote Team / User | Pending final mapping | Denied by default | Pending | No | No | Pending |
| Quality | Quality / Manager | Pending final mapping | Denied by default | Pending | No | Warehouse-adjacent (pending) | Pending |
| Quality | Quality / User | Pending final mapping | Denied by default | Pending | No | Warehouse-adjacent (pending) | Pending |
| IT | IT / Manager | Pending final mapping | Denied by default | Pending | No | No | Technical reports only (pending) |
| IT | IT / User | Pending final mapping | Denied by default | Pending | No | No | Technical reports only (pending) |

## 4. Detailed Role Breakdown

### 4.1 Administrator
#### Access Scope Definition
1. Company scope: all assigned companies (currently single-company)
2. Department scope: all departments
3. Record ownership: unrestricted

#### Functional Permissions
1. View: all modules and records
2. Create: all records
3. Edit: all records
4. Delete: all records (except model-level constraints)
5. Approve: all workflows where model permits

#### Sensitive Data Controls
1. Has potential payroll access if payroll modules are installed
2. Must be restricted to 1-2 trusted users only

#### Reporting Visibility
1. Can see internal remarks
2. Can export reports
3. Can modify all report filters

---

### 4.2 Shipping / Manager
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: shipping + sales operations + warehouse operational flow
3. Record ownership: mixed (all in some models via rules)

#### Functional Permissions
1. View: CRM leads (all), SO (sent/sale), PO (all), inventory operations
2. Create: operational documents per implied app rights
3. Edit: operational documents per app rights and record rules
4. Delete: per app/model policy (no explicit global delete grant)
5. Approve: operational confirmations based on implied manager-level stock rights

#### Sensitive Data Controls
1. No payroll access by architecture policy
2. No explicit salary model access

#### Reporting Visibility
1. Internal operational reports only
2. Export rights depend on technical export setting (not globally forced)

---

### 4.3 Shipping / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: warehouse user operations
3. Record ownership: operational, non-manager scope

#### Functional Permissions
1. View: warehouse documents allowed by stock user rights
2. Create/Edit: stock user actions only
3. Delete: restricted by stock/user model policies
4. Approve: no manager approval privilege

#### Sensitive Data Controls
1. No payroll access
2. No finance master access

#### Reporting Visibility
1. Warehouse operational visibility only
2. No manager-level report override

---

### 4.4 Customer Service / Manager and Customer Service / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: customer/contact + sales front-office scope
3. Record ownership rules:
   - CRM leads: own only
   - Sales orders: own + draft for CS flow
   - Contacts/Companies: rule-driven with approval-state controls

#### Functional Permissions
1. View: contacts, companies, own CRM/sales scope
2. Create: draft company + contacts under approved company
3. Edit: broad edit for CS company/contact process (no hard delete)
4. Delete: denied (hard delete blocked)
5. Approve: company approval workflow (through status control per process)

#### Sensitive Data Controls
1. No payroll access
2. No salary visibility
3. No accounting admin rights

#### Reporting Visibility
1. Can see customer-related internal notes within accessible records
2. Vendor-safe representation depends on report template design
3. Export not globally granted by this role definition

---

### 4.5 Finance / Manager
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: finance + invoicing domain
3. Record ownership: broad finance scope, partner write limited by rule + code

#### Functional Permissions
1. View: accounting/invoicing records by implied account manager rights
2. Create: finance records per account rights
3. Edit:
   - Contacts/companies: only approved companies and tax field policy (VAT-only in current implementation)
4. Delete: restricted for contact/company by explicit deny rule
5. Approve: credit-note approval via `iconn_account` group and finance workflow rights

#### Sensitive Data Controls
1. Payroll is **not** granted by default policy in this architecture
2. If payroll access is required, create a dedicated payroll role (do not reuse finance manager)

#### Reporting Visibility
1. Full internal finance reporting visibility
2. Export policy should be explicitly approved by management
3. Can modify finance report filters

---

### 4.6 Finance / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: finance processing (AP/vendor bills)
3. Record ownership rules:
   - Account move restricted to vendor bills (`move_type = in_invoice`)

#### Functional Permissions
1. View: finance records allowed by user-level account rights + rules
2. Create/Edit/Delete:
   - Contacts/companies: denied by explicit rule
3. Approve: no manager-level approval rights by default

#### Sensitive Data Controls
1. No payroll access
2. No salary visibility

#### Reporting Visibility
1. AP-focused reporting only
2. Internal remarks visibility limited to accessible finance records

---

### 4.7 Sales Team / Country Manager
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: sales team
3. Record ownership:
   - CRM and SO team-based rule (`own OR team manager OR team member`)

#### Functional Permissions
1. View: team pipeline and team sales orders
2. Create/Edit: sales manager-level operations
3. Delete: not broadly granted by custom rule
4. Approve: sales approvals per sales manager rights

#### Sensitive Data Controls
1. No payroll access
2. No HR salary access

#### Reporting Visibility
1. Full team sales reporting
2. Can adjust team-level report filters

---

### 4.8 Sales Team / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: own sales activity
3. Record ownership:
   - CRM own only
   - SO own only

#### Functional Permissions
1. View: own leads and own sales orders
2. Create/Edit: own sales records
3. Delete: limited by model rights
4. Approve: no manager approval authority

#### Sensitive Data Controls
1. No payroll access
2. No finance confidential access

#### Reporting Visibility
1. Own pipeline and own sales reporting
2. No team-wide override by default

---

### 4.9 Purchasing / Manager and Purchasing / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: purchasing
3. Record ownership:
   - PO own-only rule for purchasing role

#### Functional Permissions
1. View: purchasing records in scope
2. Create/Edit: purchasing operations per role rights
3. Delete: restricted by model security
4. Approve: purchasing approvals per app settings

#### Sensitive Data Controls
1. No payroll access
2. Stock valuation visibility depends on account/stock valuation settings; must be explicitly approved

#### Reporting Visibility
1. Purchasing reports only
2. Export policy should be controlled by management

---

### 4.10 Warehouse / Manager
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: warehouse end-to-end
3. Record ownership: warehouse-wide manager view

#### Functional Permissions
1. View/Create/Edit: warehouse operations with manager rights
2. Delete: limited by model policy
3. Approve: warehouse validation/manager-level operations

#### Sensitive Data Controls
1. No payroll access
2. No HR salary visibility

#### Reporting Visibility
1. Full warehouse reporting
2. Can adjust warehouse filters and views

---

### 4.11 Warehouse / Incoming Only
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: inbound warehouse only
3. Record ownership:
   - Stock picking restricted to incoming (`picking_type_id.code = incoming`)

#### Functional Permissions
1. View/Create/Edit: incoming receipts only
2. Delete: restricted by model policy
3. Approve: inbound validation in allowed flow

#### Sensitive Data Controls
1. No payroll access
2. No finance confidential access

#### Reporting Visibility
1. Inbound-only operational visibility
2. No outbound/internal transfer full visibility

---

### 4.12 Warehouse / Outgoing Only
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: outbound warehouse process
3. Record ownership: outbound policy target role

#### Functional Permissions
1. View/Create/Edit: outbound process target
2. Delete: restricted by model policy
3. Approve: outbound process as configured

#### Sensitive Data Controls
1. No payroll access
2. No finance confidential access

#### Reporting Visibility
1. Outbound operational reports

---

### 4.13 HR / Manager, HR / Assistant Manager, HR / User
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: HR domain
3. Record ownership: HR model policies (to be finalized with explicit group implications)

#### Functional Permissions
1. View/Create/Edit/Delete/Approve: pending final technical mapping
2. Current org roles exist, but detailed implied HR groups must be finalized

#### Sensitive Data Controls
1. Payroll and salary fields are denied by default until explicit payroll role definition
2. No HQ payroll access unless explicitly approved and implemented

#### Reporting Visibility
1. HR reports only, after final mapping
2. Payroll reports denied by default

---

### 4.14 FAE, Marketing, Product, Quote, Quality, IT Roles
#### Access Scope Definition
1. Company scope: assigned company
2. Department scope: role exists, detailed app mapping pending
3. Record ownership: pending role-specific rule definition

#### Functional Permissions
1. Role shell exists for assignment
2. Detailed functional permissions are pending design approval and implementation

#### Sensitive Data Controls
1. Payroll denied by default
2. Confidential finance/HR data denied by default

#### Reporting Visibility
1. Pending final role mapping

## 5. Sensitive Data and Payroll Leakage Controls
1. Payroll access is denied-by-default for all non-admin roles.
2. No role should receive payroll access indirectly through finance/HR convenience mappings.
3. Finance user access is restricted to AP/vendor-bill scope where implemented.
4. Contact/company hard-delete is blocked for customer-facing and finance roles.
5. Tax data edit for finance manager is restricted (VAT-only on approved companies in current implementation).
6. Recommendation: create a dedicated `Payroll Admin` role instead of reusing `Administrator`.

## 6. Reporting Visibility Policy
1. Internal remarks are visible only within records accessible to the role.
2. Vendor-safe reports must be a separate report template policy (not implicit).
3. Export rights must be approved explicitly for sensitive roles; do not assume enabled.
4. Report filter modification is allowed for manager-level analytical roles; user roles should remain scoped.

## 7. Answers to Critical Review Questions
1. Does a Manager automatically see all Users under them?
   - No by default; only where explicit team-based record rules exist (e.g., Sales Team / Country Manager).
2. Can Managers edit user data?
   - No, unless they are assigned administration/security settings rights.
3. Can Purchasing see warehouse stock valuation?
   - Not by default policy; valuation visibility depends on accounting/valuation permissions and must be explicitly approved.
4. Can Customer Service see cost?
   - Not by policy; customer service is customer-facing scope and should not see confidential costing unless explicitly approved.
5. Does Administrator override everything?
   - Yes, effectively full system override (`base.group_system`).
6. Is Administrator allowed to access payroll?
   - Yes if payroll modules are installed; therefore admin users must be strictly limited.

## 8. Company, Department, and Ownership Defaults
1. Company scope: single-company currently; multi-company requires explicit allowed-company assignment.
2. Department scope: enforced via role groups and record rules.
3. Ownership scope: enforced where rules exist (`own`, `team`, `state`, or `picking type`).

## 9. Implementation Status for Review
### Implemented and Active
1. Administrator, Shipping, Sales Team, Finance, Customer Service, Purchasing, Warehouse role mappings (majority)
2. Contact/company approval-state controls and no-hard-delete controls
3. Core record rules for Sales/Customer Service/Purchasing/Finance Processing/Warehouse Incoming

### Partially Implemented / Pending Final Mapping
1. HR detailed implied groups
2. FAE, Marketing, Product, Quote, Quality, IT detailed functional mappings
3. Full removal of legacy compatibility bindings in remaining rule definitions
4. Explicit export-right control matrix per role

## 10. Review Checklist for Keith
1. Confirm role names and hierarchy match org chart
2. Confirm payroll policy: who (if anyone) may access payroll
3. Confirm manager-vs-user boundary per department
4. Confirm reporting/export policy per role
5. Confirm pending roles before UAT sign-off
