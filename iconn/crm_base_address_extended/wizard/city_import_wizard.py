import csv
import os

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import get_module_resource


class CityImportWizard(models.TransientModel):
    _name = "crm.city.import.wizard"
    _description = "City Import Wizard"

    country_id = fields.Many2one("res.country", required=True)
    state_id = fields.Many2one(
        "res.country.state",
        domain="[('country_id', '=', country_id)]",
        help="Optional. If set, only cities for this state will be imported.",
    )
    import_all_states = fields.Boolean(
        string="Import all states in selected country",
        default=False,
        help="If enabled, all cities in the country will be imported.",
    )
    enable_enforce_cities = fields.Boolean(
        string="Enable city dropdown for this country",
        default=True,
        help="When enabled, city selection uses the city dropdown for this country.",
    )

    def _get_states_csv_path(self):
        return get_module_resource("crm_base_address_extended", "data", "states.csv")

    def _get_cities_csv_path(self):
        return get_module_resource("crm_base_address_extended", "data", "cities.csv")

    def _load_state_map(self, country_code):
        state_obj = self.env["res.country.state"].sudo()
        existing = state_obj.search([("country_id.code", "=", country_code)])
        state_by_code = {s.code: s for s in existing if s.code}
        state_by_name = {s.name.lower(): s for s in existing if s.name}

        states_csv = self._get_states_csv_path()
        if not states_csv or not os.path.exists(states_csv):
            return state_by_code, state_by_name

        to_create = []
        with open(states_csv, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("country_code") != country_code:
                    continue
                code = row.get("iso2") or row.get("state_code") or row.get("code")
                name = row.get("name")
                if not name:
                    continue
                if code and code in state_by_code:
                    continue
                if name.lower() in state_by_name:
                    continue
                to_create.append(
                    {
                        "name": name,
                        "code": code or False,
                        "country_id": self.country_id.id,
                    }
                )
        if to_create:
            created = state_obj.create(to_create)
            for state in created:
                if state.code:
                    state_by_code[state.code] = state
                state_by_name[state.name.lower()] = state
        return state_by_code, state_by_name

    def action_import(self):
        self.ensure_one()
        if not self.country_id:
            return {"type": "ir.actions.act_window_close"}

        country_code = self.country_id.code
        if not country_code:
            raise UserError(_("Selected country does not have a code."))

        if self.enable_enforce_cities:
            self.country_id.sudo().write({"enforce_cities": True})

        state_by_code, state_by_name = self._load_state_map(country_code)

        target_state = self.state_id if not self.import_all_states else None
        if not target_state and not self.import_all_states:
            raise UserError(_("Please select a state or enable 'Import all states'."))

        cities_csv = self._get_cities_csv_path()
        if not cities_csv or not os.path.exists(cities_csv):
            raise UserError(_("Cities dataset not found in module data."))

        city_obj = self.env["res.city"].sudo()
        existing_domain = [("country_id", "=", self.country_id.id)]
        if target_state:
            existing_domain.append(("state_id", "=", target_state.id))
        existing = city_obj.search(existing_domain)
        existing_keys = {
            (c.name.lower(), c.state_id.id if c.state_id else False, c.country_id.id)
            for c in existing
        }

        to_create = []
        created_count = 0
        with open(cities_csv, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if row.get("country_code") != country_code:
                    continue
                state_code = row.get("state_code")
                state_name = row.get("state_name")
                state = None
                if state_code and state_code in state_by_code:
                    state = state_by_code[state_code]
                elif state_name and state_name.lower() in state_by_name:
                    state = state_by_name[state_name.lower()]

                if target_state and state and state.id != target_state.id:
                    continue
                if target_state and not state:
                    continue

                name = row.get("name")
                if not name:
                    continue
                key = (name.lower(), state.id if state else False, self.country_id.id)
                if key in existing_keys:
                    continue
                existing_keys.add(key)
                to_create.append(
                    {
                        "name": name,
                        "country_id": self.country_id.id,
                        "state_id": state.id if state else False,
                    }
                )
                if len(to_create) >= 1000:
                    city_obj.create(to_create)
                    created_count += len(to_create)
                    to_create = []
        if to_create:
            city_obj.create(to_create)
            created_count += len(to_create)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("City Import Completed"),
                "message": _("Imported %s cities.") % created_count,
                "type": "success",
                "sticky": False,
            },
        }
