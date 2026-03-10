# -*- coding: utf-8 -*-
from odoo import models, fields, api
from functools import lru_cache

class OdesCrmRequirementTaskreport(models.Model):
    _name = 'odes.crm.requirement.task.report'
    _description = 'Requirement Tasks Analysis'
    _auto = False
    _rec_name = 'end_date'
    _order = 'end_date desc'

    name = fields.Char('Task', readonly=True)
    module = fields.Char(string='Module', readonly=True)
    requester = fields.Char(string='Requester', readonly=True)
    mandays = fields.Float(string='Mandays', digits=(16,3), readonly=True)
    estimated_mandays = fields.Float(string='Estimated Mandays', digits=(16,3), readonly=True)
    project = fields.Char(string='Project', readonly=True)
    user = fields.Char(string='Assigned to', readonly=True)
    team = fields.Char(string='Team', readonly=True)
    date_deadline = fields.Date(string='Deadline', readonly=True)
    start_date = fields.Date(string='Start Date', readonly=True)
    end_date = fields.Date(string='End Date', readonly=True)
    stage = fields.Char(string='Stage', readonly=True)
    period = fields.Char(string='Period', readonly=True)
    month_period = fields.Char(string='Period/Month', readonly=True)
    requirement_id = fields.Many2one('odes.crm.requirement', string='Requirement', readonly=True)

    _depends = {
        'odes.crm.requirement.task': [
            'name', 'module', 'requester', 'mandays', 'project', 'user',
            'team', 'date_deadline', 'start_date', 'end_date', 'stage', 'requirement_id'
        ],
    }

    @property
    def _table_query(self):
        return '%s %s %s' % (self._select(), self._from(), self._where())

    @api.model
    def _select(self):
        return '''
            SELECT
                ocrt.id,
                ocrt.name,
                ocrt.module,
                ocrt.requester,
                ocrt.mandays,
                ROUND(ocr.estimated_mandays / (SELECT COUNT(id) FROM odes_crm_requirement_task WHERE requirement_id = ocrt.requirement_id), 3) AS estimated_mandays,
                ocrt.project,
                ocrt.user,
                ocrt.team,
                ocrt.date_deadline,
                ocrt.start_date,
                ocrt.end_date,
                ocrt.stage,
                (CASE WHEN (ocrt.end_date IS NOT NULL AND EXTRACT(DAY FROM ocrt.end_date) > 14) THEN (
                    CONCAT(
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM ocrt.end_date), '-', EXTRACT(MONTH FROM ocrt.end_date)), 'YYYY-MM'), 'YYYY-MM'), ' / ',
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM ocrt.end_date), '-', EXTRACT(MONTH FROM ocrt.end_date), '-15'), 'YYYY-MM-DD'), 'DD Mon YYYY'),
                        ' - ',
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM (ocrt.end_date + INTERVAL '1 MONTH')), '-', EXTRACT(MONTH FROM (ocrt.end_date + INTERVAL '1 MONTH')), '-14'), 'YYYY-MM-DD'), 'DD Mon YYYY')
                    )
                ) WHEN (ocrt.end_date IS NOT NULL AND EXTRACT(DAY FROM ocrt.end_date) <= 14) THEN (
                    CONCAT(
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM (ocrt.end_date - INTERVAL '1 MONTH')), '-', EXTRACT(MONTH FROM (ocrt.end_date - INTERVAL '1 MONTH'))), 'YYYY-MM'), 'YYYY-MM'), ' / ',
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM (ocrt.end_date - INTERVAL '1 MONTH')), '-', EXTRACT(MONTH FROM (ocrt.end_date - INTERVAL '1 MONTH')), '-15'), 'YYYY-MM-DD'), 'DD Mon YYYY'),
                        ' - ',
                        TO_CHAR(TO_DATE(CONCAT(EXTRACT(YEAR FROM ocrt.end_date), '-', EXTRACT(MONTH FROM ocrt.end_date), '-14'), 'YYYY-MM-DD'), 'DD Mon YYYY')
                    )
                ) ELSE (
                    NULL
                ) END) AS period,
                (CONCAT(
                    CONCAT(EXTRACT(YEAR FROM ocrt.end_date), '-', LPAD(EXTRACT(MONTH FROM ocrt.end_date)::text, 2, '0')),
                    ' / ',
                    TO_CHAR(DATE_TRUNC('month', ocrt.end_date), 'DD Mon YYYY'),
                    ' - ',
                    TO_CHAR(DATE_TRUNC('month', ocrt.end_date) + INTERVAL '1 MONTH - 1 DAY', 'DD Mon YYYY')
                )) AS month_period,
                ocrt.requirement_id
        '''

    @api.model
    def _from(self):
        return '''
            FROM odes_crm_requirement_task ocrt
                LEFT JOIN odes_crm_requirement ocr ON ocrt.requirement_id = ocr.id
        '''

    @api.model
    def _where(self):
        return '''
        '''