import time

from odoo import models
from odoo.tools.misc import formatLang


class ReportGstReturn(models.AbstractModel):
    _inherit = 'report.sg_account_report.gst_return_report_f5'

    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        datas = docs.read([])[0]
        report_lines = self.get_info(datas)
        return {'doc_ids': self.ids,
                'doc_model': model,
                'data': data,
                'docs': docs,
                'time': time,
                'get_info': report_lines}
