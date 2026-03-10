# -*- coding: utf-8 -*-


def _safe_text(value):
    return value or ''


class CEInvoiceXMLMapper:
    @staticmethod
    def map_invoice(invoice):
        company = invoice.company_id
        partner = invoice.partner_id
        lines = []
        line_seq = 1
        for line in invoice.invoice_line_ids.filtered(lambda l: not l.display_type):
            tax_amount = (line.price_total or 0.0) - (line.price_subtotal or 0.0)
            lines.append(
                {
                    'line_no': line_seq,
                    'product_code': _safe_text(line.product_id.default_code),
                    'description': _safe_text(line.name),
                    'quantity': line.quantity or 0.0,
                    'uom': _safe_text(line.product_uom_id.name),
                    'unit_price': line.price_unit or 0.0,
                    'discount': line.discount or 0.0,
                    'tax_amount': tax_amount,
                    'tax_names': ', '.join(line.tax_ids.mapped('name')),
                    'subtotal': line.price_subtotal or 0.0,
                    'total': line.price_total or 0.0,
                }
            )
            line_seq += 1

        return {
            'header': {
                'document_number': _safe_text(invoice.name),
                'document_type': invoice.move_type,
                'issue_date': str(invoice.invoice_date or invoice.date or ''),
                'due_date': str(invoice.invoice_date_due or ''),
                'currency': _safe_text(invoice.currency_id.name),
                'reference': _safe_text(invoice.ref),
            },
            'supplier': {
                'name': _safe_text(company.name),
                'vat': _safe_text(company.vat),
                'street': _safe_text(company.partner_id.street),
                'street2': _safe_text(company.partner_id.street2),
                'city': _safe_text(company.partner_id.city),
                'zip': _safe_text(company.partner_id.zip),
                'country': _safe_text(company.partner_id.country_id.code),
                'email': _safe_text(company.email),
                'phone': _safe_text(company.phone),
            },
            'customer': {
                'name': _safe_text(partner.name),
                'vat': _safe_text(partner.vat),
                'street': _safe_text(partner.street),
                'street2': _safe_text(partner.street2),
                'city': _safe_text(partner.city),
                'zip': _safe_text(partner.zip),
                'country': _safe_text(partner.country_id.code),
                'email': _safe_text(partner.email),
                'phone': _safe_text(partner.phone),
            },
            'totals': {
                'amount_untaxed': invoice.amount_untaxed or 0.0,
                'amount_tax': invoice.amount_tax or 0.0,
                'amount_total': invoice.amount_total or 0.0,
                'amount_residual': invoice.amount_residual or 0.0,
            },
            'lines': lines,
        }
