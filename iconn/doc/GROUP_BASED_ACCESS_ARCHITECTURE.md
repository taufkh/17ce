# Iconn Group-Based Access Architecture

## Purpose
This document is group-centric (not user-centric) so access review remains clear even when some roles have no assigned users yet.

## Scope
Source of truth:
1. Odoo groups under category `Iconn Access`
2. Active `Iconn Access / ...` record rules
3. Group implied permissions currently configured

## 1. Group Coverage Snapshot
| Group (Iconn Access) | Assigned Users | Record Rules Bound | Status |
|---|---:|---:|---|
| Administrator | 1 | 0 | Active (system admin role) |
| Shipping / Manager | 1 | 3 | Active |
| Shipping / User | 2 | 0 | Active |
| Warehouse / Incoming Only | 1 | 1 | Active (special restriction) |
| Warehouse / Manager | 0 | 0 | Defined, waiting assignment |
| Warehouse / Outgoing Only | 0 | 0 | Defined, waiting assignment |
| Sales Team / Country Manager | 0 | 7 | Defined, waiting assignment |
| Sales Team / User | 0 | 7 | Defined, waiting assignment |
| Finance / Manager | 0 | 3 | Defined, waiting assignment |
| Finance / User | 0 | 3 | Defined, waiting assignment |
| Customer Service / Manager | 0 | 6 | Defined, waiting assignment |
| Customer Service / User | 0 | 6 | Defined, waiting assignment |
| Purchasing / Manager | 0 | 0 (inherits legacy purchasing mapping) | Partial |
| Purchasing / User | 0 | 1 | Partial |
| HR / Manager | 1 | 0 | Role shell only (mapping pending) |
| HR / Assistant Manager | 1 | 0 | Role shell only (mapping pending) |
| HR / User | 1 | 0 | Role shell only (mapping pending) |
| Solution Engineering Cluster (FAE) / Manager | 1 | 0 | Role shell only (mapping pending) |
| Solution Engineering Cluster (FAE) / User | 2 | 0 | Role shell only (mapping pending) |
| Marketing / Manager | 0 | 0 | Role shell only (mapping pending) |
| Marketing / User | 0 | 0 | Role shell only (mapping pending) |
| Product Manager / Manager | 0 | 0 | Role shell only (mapping pending) |
| Product Manager / User | 0 | 0 | Role shell only (mapping pending) |
| Quote Team / Manager | 0 | 0 | Role shell only (mapping pending) |
| Quote Team / User | 0 | 0 | Role shell only (mapping pending) |
| Quality / Manager | 0 | 0 | Role shell only (mapping pending) |
| Quality / User | 0 | 0 | Role shell only (mapping pending) |
| IT / Manager | 0 | 0 | Role shell only (mapping pending) |
| IT / User | 0 | 0 | Role shell only (mapping pending) |

## 2. Functional Group Definitions (Implemented)

### 2.1 Administrator
1. Scope: global system
2. Can see/do: all modules, configuration, users, technical settings
3. Cannot: no explicit restriction (super-admin by design)
4. Sensitive control: limit membership to 1-2 users only

### 2.2 Shipping / Manager
1. Scope: sales operations + warehouse management
2. Can see/do:
   - CRM leads: all (`Iconn Access / Sales Operations CRM Leads - All`)
   - Sales Orders: `sent` and `sale` only
   - Purchase Orders: all
   - Stock: manager level
3. Cannot:
   - No explicit payroll role
4. Reporting:
   - Operational reporting (shipping/sales ops/warehouse)

### 2.3 Shipping / User
1. Scope: warehouse user flow
2. Can see/do:
   - Stock user-level operations
3. Cannot:
   - No manager approvals
   - No payroll role

### 2.4 Warehouse / Incoming Only
1. Scope: inbound warehouse only
2. Can see/do:
   - Stock picking where `picking_type_id.code = 'incoming'`
3. Cannot:
   - Outgoing/internal picking outside rule

### 2.5 Sales Team / Country Manager
1. Scope: team-level sales
2. Can see/do:
   - CRM leads: own/team
   - Sales orders: own/team
   - Contacts/companies: manager-level contact workflow rules
3. Cannot:
   - No payroll role

### 2.6 Sales Team / User
1. Scope: own sales documents
2. Can see/do:
   - CRM leads: own only
   - Sales orders: own only
   - Contacts/companies: create draft company + approved parent contact flow
3. Cannot:
   - Team-wide visibility
   - Hard delete partner records

### 2.7 Finance / Manager
1. Scope: finance manager operations
2. Can see/do:
   - Full finance manager implied rights
   - Partner read-all
   - Partner edit only on approved companies (VAT-only enforced in code)
3. Cannot:
   - Partner create/delete (explicit deny)
   - Payroll not explicitly granted by this group design

### 2.8 Finance / User
1. Scope: AP processing
2. Can see/do:
   - Vendor bills only (`move_type = in_invoice`)
   - Partner read-all
3. Cannot:
   - Partner write/create/delete
   - Payroll not granted

### 2.9 Customer Service / Manager and Customer Service / User
1. Scope: customer-facing partner + own sales workflow
2. Can see/do:
   - Partner read-all
   - Create draft company or contact under approved parent
   - Write partner records for CS workflow
   - CRM own leads
   - Sales order draft own
3. Cannot:
   - Hard delete partner records
   - Payroll access

## 3. Group Shells (Defined but Not Fully Mapped Yet)
These groups exist for org-chart completeness but still require explicit functional mapping:
1. HR / Manager
2. HR / Assistant Manager
3. HR / User
4. Solution Engineering Cluster (FAE) / Manager
5. Solution Engineering Cluster (FAE) / User
6. Marketing / Manager
7. Marketing / User
8. Product Manager / Manager
9. Product Manager / User
10. Quote Team / Manager
11. Quote Team / User
12. Quality / Manager
13. Quality / User
14. IT / Manager
15. IT / User
16. Warehouse / Manager
17. Warehouse / Outgoing Only
18. Purchasing / Manager (still partial via legacy bridge)

## 4. Security Answers (Group-Based)
1. Do Managers automatically see all users under them?
   - No, only where explicit team/domain rules exist (e.g., Sales Team / Country Manager).
2. Can Managers edit user accounts?
   - No, unless they are also in Administrator/Settings rights.
3. Can Purchasing see stock valuation?
   - Not by policy default; depends on accounting/valuation rights. Must be explicitly approved.
4. Can Customer Service see cost?
   - Not intended by policy; customer-facing groups are not cost-control groups.
5. Does Administrator override everything?
   - Yes.
6. Is Administrator allowed payroll?
   - Yes if payroll modules are installed; must remain tightly limited.

## 5. Payroll and Confidential Data Protection
1. Default-deny payroll policy for all non-admin groups.
2. Keep payroll in a dedicated role if needed; do not mix with Finance User/CS/Sales/Shipping.
3. Maintain no-hard-delete controls on partner master data.
4. Keep report export restricted for sensitive roles unless approved.

## 6. Review Workflow (Keith)
1. Validate group list vs org chart
2. Validate which groups are Active vs Shell
3. Approve functional mapping for Shell groups
4. Approve payroll policy and exception roles
5. Sign off before assigning users to remaining groups
