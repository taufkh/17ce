from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain=[('is_company', '=', True)],
        check_company=True,
    )
    contact_id = fields.Many2one(
        'res.partner',
        string='Contact',
    )

    @api.onchange('partner_id')
    def _onchange_partner_id_contact(self):
        for lead in self:
            lead.contact_id = False
            lead.email_from = False
            lead.phone = False
            lead.contact_name = False

    @api.onchange('contact_id')
    def _onchange_contact_id(self):
        for lead in self:
            contact = lead.contact_id
            if contact and contact.parent_id:
                lead.partner_id = contact.parent_id
            if contact:
                lead.email_from = contact.email or False
                lead.phone = contact.phone or contact.mobile or False
                lead.contact_name = contact.name
            else:
                lead.email_from = False
                lead.phone = False
                lead.contact_name = False
