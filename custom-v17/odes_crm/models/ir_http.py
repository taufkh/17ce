# -*- coding: utf-8 -*-
import json
import hashlib
from odoo import api, models
from odoo.tools import ustr
from odoo.http import request
from odoo.addons.web.controllers.main import module_boot, HomeStaticTemplateHelpers

class Http(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        session_info = super(Http, self).session_info()
        user = request.env.user
        user_context = request.session.get_context() if request.session.uid else {}
        if self.env.user.has_group('odes_crm.group_odes_customer'):
            # the following is only useful in the context of a webclient bootstrapping
            # but is still included in some other calls (e.g. '/web/session/authenticate')
            # to avoid access errors and unnecessary information, it is only included for users
            # with access to the backend ('internal'-type users)
            mods = module_boot()
            qweb_checksum = HomeStaticTemplateHelpers.get_qweb_templates_checksum(addons=mods, debug=request.session.debug)
            lang = user_context.get("lang")
            translation_hash = request.env['ir.translation'].get_web_translations_hash(mods, lang)
            menu_json_utf8 = json.dumps(request.env['ir.ui.menu'].load_menus(request.session.debug), default=ustr, sort_keys=True).encode()
            cache_hashes = {
                "load_menus": hashlib.sha512(menu_json_utf8).hexdigest()[:64], # sha512/256
                "qweb": qweb_checksum,
                "translations": translation_hash,
            }
            session_info.update({
                # current_company should be default_company
                "user_companies": {'current_company': (user.company_id.id, user.company_id.name), 'allowed_companies': [(comp.id, comp.name) for comp in user.company_ids]},
                "currencies": self.get_currencies(),
                "show_effect": True,
                "display_switch_company_menu": user.has_group('base.group_multi_company') and len(user.company_ids) > 1,
                "cache_hashes": cache_hashes,
            })
        return session_info