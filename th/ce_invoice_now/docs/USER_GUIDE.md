# User Guide (Accounting Team)

## Purpose
This guide explains how end users send invoices to Datapost and monitor status.

## 1. Before You Start
Confirm with admin:
- CE InvoiceNow configuration is completed.
- Token generation works.
- Your customer is marked as applicable.

## 2. Send an Invoice
1. Open a posted customer invoice.
2. Confirm XML attachment exists.
3. Click **CE InvoiceNow**.
4. In wizard, review invoice and attachment list.
5. Click **Send**.

## 3. Send a Credit Note
1. Open a posted customer credit note.
2. Confirm XML attachment exists.
3. Click **CE InvoiceNow**.
4. Click **Send**.

## 4. Check Send Result
Open tab **CE InvoiceNow Status** on invoice form:
- `CE Send Invoice Status Code`
- `CE Send Invoice Content`
- `CE Send Invoice Status`

## 5. Check Processing Status
The scheduler updates status fields:
- `CE Invoice Status Content`
- `CE Invoice Status Code`
- `CE Is Completed`

## 6. Typical Outcomes
- `200` or `202` send code: request accepted.
- `CE Is Completed = True`: Datapost status completed.

## 7. If Send Fails
Provide to admin/support:
- Invoice number
- Send status code
- Send response content
- Time of submission attempt

## 8. Good Practices
- Send only after invoice is final and posted.
- Validate XML attachment correctness before send.
- Do not resend completed invoices unless business-approved.
