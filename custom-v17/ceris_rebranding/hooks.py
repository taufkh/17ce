# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


REPLACEMENTS = (
    ("OdooBot", "CerisBot"),
    ("Odoobot", "CerisBot"),
    ("Powered by Odoo", "Powered by CERIS"),
    ("Odoo", "CERIS"),
    ("odoo", "ceris"),
)


def _replace_tokens(value):
    if not value:
        return value
    for source, target in REPLACEMENTS:
        value = value.replace(source, target)
    return value


def post_init_hook(*args):
    # Odoo 17 calls hooks with env, while older signatures use (cr, registry).
    if len(args) == 1:
        env = args[0]
    else:
        cr, _registry = args
        env = api.Environment(cr, SUPERUSER_ID, {})

    # Rename default OdooBot partner if present.
    try:
        partner_root = env.ref('base.partner_root')
        new_name = _replace_tokens(partner_root.name)
        if new_name and new_name != partner_root.name:
            partner_root.name = new_name
    except ValueError:
        pass

    # Replace common branding tokens in mail templates (subject/body).
    templates = env['mail.template'].search([
        '|',
        ('subject', 'ilike', 'odoo'),
        ('body_html', 'ilike', 'odoo'),
    ])
    for template in templates:
        vals = {}
        new_subject = _replace_tokens(template.subject)
        if new_subject != template.subject:
            vals['subject'] = new_subject
        new_body = _replace_tokens(template.body_html)
        if new_body != template.body_html:
            vals['body_html'] = new_body
        if vals:
            template.write(vals)

    # Replace branding in UI views (website snippets, qweb templates, etc.).
    views = env['ir.ui.view'].with_context(lang='en_US').search([
        ('arch_db', 'ilike', 'odoo'),
        ('inherit_id', '=', False),
    ])
    for view in views:
        new_arch = _replace_tokens(view.arch_db)
        if new_arch != view.arch_db:
            with env.cr.savepoint():
                try:
                    view.with_context(lang='en_US').write({'arch_db': new_arch})
                except Exception:
                    # Skip views where token replacement breaks semantics.
                    continue
