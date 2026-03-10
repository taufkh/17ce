# -*- coding: utf-8 -*-

from xml.etree import ElementTree

from odoo import _
from odoo.exceptions import UserError


class CEInvoiceXMLValidator:
    @staticmethod
    def validate_invoice(invoice):
        if invoice.move_type not in ('out_invoice', 'out_refund'):
            raise UserError(_('CE XML generation is only available for customer invoice or credit note.'))
        if invoice.state != 'posted':
            raise UserError(_('Invoice must be posted before generating CE XML.'))
        if not invoice.partner_id:
            raise UserError(_('Invoice has no customer partner.'))
        line_count = len(invoice.invoice_line_ids.filtered(lambda l: not l.display_type))
        if line_count == 0:
            raise UserError(_('Invoice must contain at least one invoice line.'))

    @staticmethod
    def validate_xml(xml_bytes):
        try:
            ElementTree.fromstring(xml_bytes)
        except ElementTree.ParseError as err:
            raise UserError(_('Generated XML is not well-formed: %s') % err) from err
