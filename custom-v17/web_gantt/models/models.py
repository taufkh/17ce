from lxml.builder import E

from odoo import api, models


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _get_default_gantt_view(self):
        return E.gantt(date_start='create_date', date_stop='write_date')
