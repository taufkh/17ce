import base64
from datetime import date
from xml.sax.saxutils import escape

from odoo import _, fields, models
from odoo.exceptions import UserError


class IrasAuditFileWizard(models.TransientModel):
    _name = 'l10n.sg.reports.iaf.wizard'
    _description = 'Singaporean IAF Report Wizard'

    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    export_type = fields.Selection([('xml', 'XML'), ('txt', 'TXT')], default='xml', required=True)

    def generate_iras(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError(_('Start Date cannot be after End Date.'))
        if self.export_type == 'xml':
            return self.env['l10n.sg.reports.iaf'].l10n_sg_print_iras_audit_file_xml(
                {'date_from': self.date_from, 'date_to': self.date_to}
            )
        return self.env['l10n.sg.reports.iaf'].l10n_sg_print_iras_audit_file_txt(
            {'date_from': self.date_from, 'date_to': self.date_to}
        )


class IrasAuditFile(models.AbstractModel):
    _name = 'l10n.sg.reports.iaf'
    _description = 'Create IRAS audit file'

    def _build_summary(self, date_from, date_to):
        company = self.env.company
        domain_common = [
            ('company_id', '=', company.id),
            ('state', '=', 'posted'),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]
        sales = self.env['account.move'].search(domain_common + [('move_type', 'in', ('out_invoice', 'out_refund'))])
        purchases = self.env['account.move'].search(domain_common + [('move_type', 'in', ('in_invoice', 'in_refund'))])
        sales_total = sum(sales.mapped('amount_total_signed'))
        purchase_total = sum(purchases.mapped('amount_total_signed'))
        return {
            'company_name': company.name or '',
            'uen': company.l10n_sg_unique_entity_number or '',
            'gst_no': company.vat or '',
            'period_start': fields.Date.to_string(date_from),
            'period_end': fields.Date.to_string(date_to),
            'created_on': fields.Date.to_string(date.today()),
            'sales_total': sales_total,
            'purchase_total': purchase_total,
            'sales_count': len(sales),
            'purchase_count': len(purchases),
        }

    def _build_xml_payload(self, summary):
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<Company>'
            f"<CompanyName>{escape(summary['company_name'])}</CompanyName>"
            f"<CompanyUEN>{escape(summary['uen'])}</CompanyUEN>"
            f"<GSTNo>{escape(summary['gst_no'])}</GSTNo>"
            f"<PeriodStart>{summary['period_start']}</PeriodStart>"
            f"<PeriodEnd>{summary['period_end']}</PeriodEnd>"
            f"<IAFCreationDate>{summary['created_on']}</IAFCreationDate>"
            f"<SalesTotal>{summary['sales_total']:.2f}</SalesTotal>"
            f"<PurchaseTotal>{summary['purchase_total']:.2f}</PurchaseTotal>"
            f"<SalesCount>{summary['sales_count']}</SalesCount>"
            f"<PurchaseCount>{summary['purchase_count']}</PurchaseCount>"
            '</Company>'
        )

    def _build_txt_payload(self, summary):
        lines = [
            f"CompanyName={summary['company_name']}",
            f"CompanyUEN={summary['uen']}",
            f"GSTNo={summary['gst_no']}",
            f"PeriodStart={summary['period_start']}",
            f"PeriodEnd={summary['period_end']}",
            f"IAFCreationDate={summary['created_on']}",
            f"SalesTotal={summary['sales_total']:.2f}",
            f"PurchaseTotal={summary['purchase_total']:.2f}",
            f"SalesCount={summary['sales_count']}",
            f"PurchaseCount={summary['purchase_count']}",
        ]
        return '\n'.join(lines)

    def _make_download_action(self, payload, filename, mimetype):
        data = base64.b64encode(payload.encode('utf-8'))
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': data,
            'mimetype': mimetype,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=1',
            'target': 'self',
        }

    def l10n_sg_print_iras_audit_file_xml(self, options):
        summary = self._build_summary(options['date_from'], options['date_to'])
        payload = self._build_xml_payload(summary)
        return self._make_download_action(payload, 'iras_audit_file.xml', 'application/xml')

    def l10n_sg_print_iras_audit_file_txt(self, options):
        summary = self._build_summary(options['date_from'], options['date_to'])
        payload = self._build_txt_payload(summary)
        return self._make_download_action(payload, 'iras_audit_file.txt', 'text/plain')

