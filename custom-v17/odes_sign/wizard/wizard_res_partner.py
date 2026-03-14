from ..models.res_partner import ResPartner
from odoo import api, fields, models, _

class OdesChangePartnerNameWizard(models.TransientModel):
    _name = 'odes.change.partner.name.wizard'
    _description = 'Change Partner Wizard'

    # partner_id = fields.Many2one('res.partner',string='Partner')
    old_partner_id = fields.Many2one('res.partner',string='Partner')
    name = fields.Char(string='Name')

    @api.onchange('old_partner_id')
    def _onchange_old_partner_id(self):
        if self.old_partner_id:
            self.name = self.old_partner_id.name

    def save_button(self, default=None):
        # partner = self.env['res.partner'].search([('id','=',self.old_partner_id.id)],limit=1)
        if self.old_partner_id:      
            default = dict(default or {})
            default.update({
                'name': self.name,
            })
            new_partner_name = self.old_partner_id.copy(default)
            # new_partner_name.active = True
            last_id = new_partner_name.id
            self.old_partner_id.active = False

            return {
                'type': 'ir.actions.act_window',
                'name': 'Contact',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'res_id':last_id,
            }