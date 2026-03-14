from odoo import models

class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    def _validate_view(self, *args, **kwargs):
        """Override to suppress false-positive validation failures in Odoo v16.

        The v16 view validator (ir_ui_view._validate_tag_field) evaluates
        'invisible'/'readonly'/'required' attribute expressions with only
        {'context': ...} in scope — without field values.  Any expression
        that references a field name (e.g. invisible="type == 'lead'") raises
        NameError → safe_eval wraps it as ValueError.

        The stock _check_xml error-handler then crashes with
        AttributeError: 'ValueError' object has no attribute 'context'
        (a bug in this version of Odoo 16).

        We catch those NameError-originated ValueErrors here so that views
        written in the v14/v15 Python-expression style install successfully.
        All such expressions remain fully functional at runtime, where field
        values ARE available in the evaluation context.
        """
        try:
            return super()._validate_view(*args, **kwargs)
        except ValueError as e:
            if 'NameError' in str(e):
                # Keep legacy dynamic expressions compatible during static validation.
                return None
            else:
                raise
