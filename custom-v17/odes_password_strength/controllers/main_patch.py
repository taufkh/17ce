from odoo import api, fields, models, _
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.http import request
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError, ValidationError

class OdesPasswordStrengthPatch(AuthSignupHome):

    def _signup_with_values(self, token, values):
        error = request.env['res.users'].sudo().pre_signup(values, token)
        return super(OdesPasswordStrengthPatch, self)._signup_with_values(token, values)