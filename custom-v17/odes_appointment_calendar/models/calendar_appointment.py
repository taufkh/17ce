from odoo import api, fields, models, _
from odoo.tools.misc import get_lang
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import ValidationError


class CalendarAppointmentType(models.Model):
    _inherit = "calendar.appointment.type"

    def _compute_website_url(self):
        super(CalendarAppointmentType, self)._compute_website_url()
        for appointment_type in self:
            if appointment_type.id :
                appointment_type.website_url = '/appointment/appointment/%s' % (slug(appointment_type),)


