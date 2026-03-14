# Security Guide

## Purpose
Security guidance for deploying and operating `ce_invoice_now` safely.

## 1. Credential Handling
- Treat `client_id` and `secret_key` as sensitive.
- Restrict configuration access to accounting managers.
- Avoid sharing credentials in chat/email/plain logs.

## 2. Access Control
Recommended access:
- Config model (`ce.invoice.now.configuration`): accounting manager only.
- Send wizard: internal users in accounting operations.

## 3. Endpoint Governance
- Use approved endpoint values only.
- Separate sandbox and production credentials.
- Keep endpoint changes documented and approved.

## 4. Auditability
- Keep send/status response fields for operational audit.
- Track retry actions with user and timestamp.

## 5. Logging Hygiene
- Do not log secret keys.
- Avoid exposing full tokens in custom logs.
- Use sanitized logs for troubleshooting.

## 6. Network Controls
- Allow outbound HTTPS only to required Datapost hosts.
- Block unnecessary egress from Odoo host/container.

## 7. Backup and Data Retention
- Include invoice status fields in regular backup policy.
- Define retention policy for diagnostic response content.

## 8. Operational Security Checklist
- Credentials rotated periodically.
- No shared admin account for production operations.
- Principle of least privilege is applied.
- Incident response path is documented.
