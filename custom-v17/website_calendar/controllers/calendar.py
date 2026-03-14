from odoo import http


class WebsiteCalendarController(http.Controller):
    # Compatibility controller base for custom inheritance.
    def view_meeting(self, token, id):
        return None
