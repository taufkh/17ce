from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Department(models.Model):
    _inherit = "hr.department"

    is_included_in_timeoff_approval = fields.Boolean("Timeoff Approval", help="Include the department manager in the Timeoff Approval (manager substitue)")