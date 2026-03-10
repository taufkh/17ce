from odoo import api, fields, models

class SmartIOTTermCondition(models.Model):
    _name = "smart.iot.term.condition"
    _description = "Smart IOT Term and Condition"

    name = fields.Char("Name")
    term_condition = fields.Char("Term and Condition")