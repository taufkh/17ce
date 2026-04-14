# -*- coding: utf-8 -*-
from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    """
    Override ir.http to:
    1. Read per-user color_scheme from res.users.settings
    2. Clear color_scheme cookie on logout
    """
    _inherit = 'ir.http'

    @classmethod
    def _post_logout(cls):
        super()._post_logout()
        # Remove the color_scheme cookie when user logs out
        request.future_response.set_cookie('color_scheme', max_age=0)

    def color_scheme(self):
        """
        Priority order:
        1. User's stored preference (light/dark) from res.users.settings
        2. Cookie value (set by color_scheme_service.js on the JS side)
        3. Base system default
        """
        cookie_scheme = request.httprequest.cookies.get('color_scheme')
        scheme = cookie_scheme if cookie_scheme else super().color_scheme()

        if user := request.env.user:
            if user._is_public():
                return super().color_scheme()
            user_scheme = user.res_users_settings_id.color_scheme
            if user_scheme in ('light', 'dark'):
                return user_scheme

        return scheme
