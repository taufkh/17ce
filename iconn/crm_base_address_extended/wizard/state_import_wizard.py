import csv
import os

from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource


class StateImportWizard(models.TransientModel):
    _name = "crm.state.import.wizard"
    _description = "State Import Wizard"

    country_id = fields.Many2one("res.country", required=True)

    def _get_states_csv_path(self):
        return get_module_resource("crm_base_address_extended", "data", "states.csv")

    def action_import(self):
        self.ensure_one()
        if not self.country_id:
            return {"type": "ir.actions.act_window_close"}

        country_code = self.country_id.code
        if not country_code:
            raise UserError(_("Selected country does not have a code."))

        states_csv = self._get_states_csv_path()
        if not states_csv or not os.path.exists(states_csv):
            raise UserError(_("States dataset not found in module data."))

        state_obj = self.env["res.country.state"].sudo()
        existing = state_obj.search([("country_id", "=", self.country_id.id)])
        existing_codes = {s.code for s in existing if s.code}
        existing_names = {s.name.lower() for s in existing if s.name}

        to_create = []
        created_count = 0
        with open(states_csv, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("country_code") != country_code:
                    continue
                name = row.get("name")
                if not name:
                    continue
                code = row.get("iso2") or row.get("state_code") or row.get("code")
                if code and code in existing_codes:
                    continue
                if name.lower() in existing_names:
                    continue
                existing_names.add(name.lower())
                if code:
                    existing_codes.add(code)
                to_create.append(
                    {
                        "name": name,
                        "code": code or False,
                        "country_id": self.country_id.id,
                    }
                )
                if len(to_create) >= 500:
                    state_obj.create(to_create)
                    created_count += len(to_create)
                    to_create = []
        if to_create:
            state_obj.create(to_create)
            created_count += len(to_create)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("State Import Completed"),
                "message": _("Imported %s states.") % created_count,
                "type": "success",
                "sticky": False,
            },
        }
