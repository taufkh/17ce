# -*- coding: utf-8 -*-

from xml.etree.ElementTree import Element, SubElement, tostring


def _f2(value):
    return f"{float(value or 0.0):.2f}"


class CEInvoiceXMLRenderer:
    @staticmethod
    def render(payload):
        root = Element('CEInvoiceDocument')

        header = SubElement(root, 'Header')
        for key, value in payload['header'].items():
            SubElement(header, key).text = str(value or '')

        supplier = SubElement(root, 'Supplier')
        for key, value in payload['supplier'].items():
            SubElement(supplier, key).text = str(value or '')

        customer = SubElement(root, 'Customer')
        for key, value in payload['customer'].items():
            SubElement(customer, key).text = str(value or '')

        lines_node = SubElement(root, 'Lines')
        for line in payload['lines']:
            line_node = SubElement(lines_node, 'Line')
            for key in ('line_no', 'product_code', 'description', 'uom', 'tax_names'):
                SubElement(line_node, key).text = str(line.get(key, '') or '')
            SubElement(line_node, 'quantity').text = _f2(line.get('quantity'))
            SubElement(line_node, 'unit_price').text = _f2(line.get('unit_price'))
            SubElement(line_node, 'discount').text = _f2(line.get('discount'))
            SubElement(line_node, 'tax_amount').text = _f2(line.get('tax_amount'))
            SubElement(line_node, 'subtotal').text = _f2(line.get('subtotal'))
            SubElement(line_node, 'total').text = _f2(line.get('total'))

        totals = SubElement(root, 'Totals')
        SubElement(totals, 'amount_untaxed').text = _f2(payload['totals'].get('amount_untaxed'))
        SubElement(totals, 'amount_tax').text = _f2(payload['totals'].get('amount_tax'))
        SubElement(totals, 'amount_total').text = _f2(payload['totals'].get('amount_total'))
        SubElement(totals, 'amount_residual').text = _f2(payload['totals'].get('amount_residual'))

        return tostring(root, encoding='utf-8', xml_declaration=True)
