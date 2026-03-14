# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class MassMailing(models.Model):
    _inherit = 'mailing.mailing'

    scheduled = fields.Integer(compute="_compute_statistics", store=True)
    expected = fields.Integer(compute="_compute_statistics", store=True)
    ignored = fields.Integer(compute="_compute_statistics", store=True)
    sent = fields.Integer(compute="_compute_statistics", store=True)
    delivered = fields.Integer(compute="_compute_statistics", store=True)
    opened = fields.Integer(compute="_compute_statistics", store=True)
    clicked = fields.Integer(compute="_compute_statistics", store=True)
    replied = fields.Integer(compute="_compute_statistics", store=True)
    bounced = fields.Integer(compute="_compute_statistics", store=True)
    failed = fields.Integer(compute="_compute_statistics", store=True)
    received_ratio = fields.Integer(compute="_compute_statistics", string='Received Ratio', store=True)
    opened_ratio = fields.Integer(compute="_compute_statistics", string='Opened Ratio', store=True)
    replied_ratio = fields.Integer(compute="_compute_statistics", string='Replied Ratio', store=True)
    bounced_ratio = fields.Integer(compute="_compute_statistics", string='Bounced Ratio', store=True)

    @api.depends('state', 'mailing_trace_ids', 'mailing_trace_ids.state', 'mailing_trace_ids.mass_mailing_id', 
        'mailing_trace_ids.sent', 'mailing_trace_ids.scheduled', 'mailing_trace_ids.exception', 'mailing_trace_ids.ignored', 
        'mailing_trace_ids.bounced', 'mailing_trace_ids.opened', 'mailing_trace_ids.clicked', 'mailing_trace_ids.replied')
    def _compute_statistics(self):
        """ Compute statistics of the mass mailing """
        for key in (
            'scheduled', 'expected', 'ignored', 'sent', 'delivered', 'opened',
            'clicked', 'replied', 'bounced', 'failed', 'received_ratio',
            'opened_ratio', 'replied_ratio', 'bounced_ratio', 'clicks_ratio',
        ):
            self[key] = False
        if not self.ids:
            return
        self.env.cr.execute("""
            SELECT
                m.id as mailing_id,
                COUNT(s.id) AS expected,
                COUNT(CASE WHEN s.sent is not null THEN 1 ELSE null END) AS sent,
                COUNT(CASE WHEN s.scheduled is not null AND s.sent is null AND s.exception is null AND s.ignored is null AND s.bounced is null THEN 1 ELSE null END) AS scheduled,
                COUNT(CASE WHEN s.scheduled is not null AND s.sent is null AND s.exception is null AND s.ignored is not null THEN 1 ELSE null END) AS ignored,
                COUNT(CASE WHEN s.sent is not null AND s.exception is null AND s.bounced is null THEN 1 ELSE null END) AS delivered,
                COUNT(CASE WHEN s.opened is not null THEN 1 ELSE null END) AS opened,
                COUNT(CASE WHEN s.clicked is not null THEN 1 ELSE null END) AS clicked,
                COUNT(CASE WHEN s.replied is not null THEN 1 ELSE null END) AS replied,
                COUNT(CASE WHEN s.bounced is not null THEN 1 ELSE null END) AS bounced,
                COUNT(CASE WHEN s.exception is not null THEN 1 ELSE null END) AS failed
            FROM
                mailing_trace s
            RIGHT JOIN
                mailing_mailing m
                ON (m.id = s.mass_mailing_id)
            WHERE
                m.id IN %s
            GROUP BY
                m.id
        """, (tuple(self.ids), ))
        for row in self.env.cr.dictfetchall():
            total = row['expected'] = (row['expected'] - row['ignored']) or 1
            row['received_ratio'] = 100.0 * row['delivered'] / total
            row['opened_ratio'] = 100.0 * row['opened'] / total
            row['clicks_ratio'] = 100.0 * row['clicked'] / total
            row['replied_ratio'] = 100.0 * row['replied'] / total
            row['bounced_ratio'] = 100.0 * row['bounced'] / total
            self.browse(row.pop('mailing_id')).update(row)