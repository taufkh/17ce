# -*- coding: utf-8 -*-

import json
import logging

import requests

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class CEInvoiceNowConfiguration(models.Model):
    _name = 'ce.invoice.now.configuration'
    _description = 'CE InvoiceNow configuration'

    name = fields.Char(string='Name', default='CE InvoiceNow Config')
    active = fields.Boolean(default=True)
    client_id = fields.Char(string='Client ID', required=True)
    secret_key = fields.Char(string='Secret Key', required=True)
    base_uri = fields.Char(
        string='Base URI',
        default='https://peppol.datapost.com.sg/services/rest/peppol',
        required=True,
    )
    auth_uri = fields.Char(
        string='Auth URI',
        default='https://peppol.datapost.com.sg/app/services/rest/auth/token',
        required=True,
        help='Use test URI only in sandbox environments.',
    )
    status_uri = fields.Char(
        string='Status URI',
        default='https://peppol.datapost.com.sg/services/rest/peppol',
        required=True,
    )
    inv_document_type = fields.Char(string='Invoice Document Type', default='invoices', required=True)
    inv_document_format = fields.Char(string='Invoice Document Format', default='peppol-invoice-2', required=True)
    credit_document_type = fields.Char(string='Credit Note Document Type', default='credit-notes', required=True)
    credit_document_format = fields.Char(string='Credit Note Document Format', default='peppol-credit-note-2', required=True)
    api_version = fields.Char(string='API Version', default='v10', required=True)

    ce_xml_auto_generate = fields.Boolean(string='Auto Generate CE XML', default=True)
    ce_xml_profile = fields.Selection(
        [('minimal', 'Minimal'), ('datapost', 'Datapost')],
        string='CE XML Profile',
        default='minimal',
        required=True,
    )
    ce_xml_force_regenerate = fields.Boolean(string='Force Regenerate CE XML', default=False)
    ce_xml_include_tax_breakdown = fields.Boolean(string='Include Tax Breakdown', default=True)

    access_token = fields.Text(string='Access Token', readonly=True)
    refresh_token = fields.Text(string='Refresh Token', readonly=True)
    ce_access_token_masked = fields.Char(string='Access Token (Masked)', compute='_compute_masked_tokens')
    ce_refresh_token_masked = fields.Char(string='Refresh Token (Masked)', compute='_compute_masked_tokens')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records.filtered('active')._deactivate_other_configs()
        return records

    def write(self, vals):
        result = super().write(vals)
        if vals.get('active'):
            self.filtered('active')._deactivate_other_configs()
        return result

    @api.constrains('active')
    def _check_single_active_config(self):
        if self.search_count([('active', '=', True)]) > 1:
            raise ValidationError(_('Only one active CE InvoiceNow configuration is allowed.'))

    def _deactivate_other_configs(self):
        for record in self:
            others = self.search([('id', '!=', record.id), ('active', '=', True)])
            if others:
                others.write({'active': False})

    @api.depends('access_token', 'refresh_token')
    def _compute_masked_tokens(self):
        for record in self:
            record.ce_access_token_masked = record._mask_token(record.access_token)
            record.ce_refresh_token_masked = record._mask_token(record.refresh_token)

    @staticmethod
    def _mask_token(token):
        if not token:
            return ''
        if len(token) <= 8:
            return '*' * len(token)
        return '%s%s%s' % (token[:4], '*' * (len(token) - 8), token[-4:])

    @api.model
    def get_active_configuration(self):
        return self.search([('active', '=', True)], limit=1, order='id asc')

    def action_generate_token(self):
        self.ensure_one()
        payload = json.dumps({'clientId': self.client_id, 'secret': self.secret_key})
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(self.auth_uri, headers=headers, data=payload, timeout=30)
        except requests.RequestException as err:
            raise UserError(_('Unable to reach InvoiceNow auth endpoint: %s') % err) from err

        if response.status_code != 200:
            self.write({'access_token': False, 'refresh_token': False})
            raise UserError(_('Generate token failed with status code %s.') % response.status_code)

        try:
            data = response.json()
        except ValueError as err:
            raise UserError(_('Generate token returned invalid JSON response.')) from err

        access_token = data.get('access_token')
        refresh_token = data.get('refresh_token')
        if not access_token:
            raise UserError(_('Generate token succeeded but access token is empty.'))

        self.write({'access_token': access_token, 'refresh_token': refresh_token})
        _logger.info('CE InvoiceNow token generated for configuration %s', self.id)
        return True
