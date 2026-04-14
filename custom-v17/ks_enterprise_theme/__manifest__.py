# -*- coding: utf-8 -*-
{
    'name': 'KS Enterprise Theme',
    'version': '17.0.1.0.0',
    'category': 'Branding',
    'summary': 'Full Enterprise backend theme for Odoo 17 Community',
    'description': """
        Replicates the complete Odoo Enterprise v17 backend theme on Community Edition.
        Features:
        - Enterprise color scheme (purple #714B67 + teal #017e84)
        - Home Menu overlay with app grid (6-column) + search + drag-reorder
        - Enterprise NavBar with 9-dots toggle + active app name/icon
        - Dark Mode with OS detection and per-user preference
        - Enterprise list, kanban, form, pivot view styling
        - Mobile-optimised burger menu integrated with home menu
    """,
    'author': 'KS V17',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['web', 'base_setup'],
    'conflicts': ['web_enterprise', 'legion_enterprise_theme'],
    'data': [
        'security/ir.model.access.csv',
        'views/webclient_templates.xml',
        'views/res_users_settings_views.xml',
    ],
    'assets': {
        # ── PRIMARY VARIABLES ──────────────────────────────────────────────────
        # Injected BEFORE web/primary_variables.scss so Enterprise color values win.
        # Navbar & home_menu *.variables.scss are injected AFTER.
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'ks_enterprise_theme/static/src/scss/primary_variables.scss'),
            ('after', 'web/static/src/scss/primary_variables.scss',
             'ks_enterprise_theme/static/src/webclient/navbar/navbar.variables.scss'),
            ('after', 'web/static/src/scss/primary_variables.scss',
             'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.variables.scss'),
        ],
        # ── SECONDARY VARIABLES ────────────────────────────────────────────────
        'web._assets_secondary_variables': [
            ('before', 'web/static/src/scss/secondary_variables.scss',
             'ks_enterprise_theme/static/src/scss/secondary_variables.scss'),
        ],
        # ── BOOTSTRAP OVERRIDES ────────────────────────────────────────────────
        'web._assets_backend_helpers': [
            ('before', 'web/static/src/scss/bootstrap_overridden.scss',
             'ks_enterprise_theme/static/src/scss/bootstrap_overridden.scss'),
        ],
        # ── FRONTEND (login page background + navbar) ─────────────────────────
        'web.assets_frontend': [
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu_background.scss',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.scss',
        ],
        # ── BACKEND MAIN BUNDLE (light mode only — NO dark files here) ────────
        'web.assets_backend': [
            # SCSS — webclient
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu_background.scss',
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.scss',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.scss',
            'ks_enterprise_theme/static/src/search/control_panel/control_panel.scss',
            'ks_enterprise_theme/static/src/core/search/search_panel/search_panel.scss',
            # SCSS — views
            'ks_enterprise_theme/static/src/views/form/form_controller.scss',
            'ks_enterprise_theme/static/src/views/form/button_box/button_box.scss',
            'ks_enterprise_theme/static/src/views/list/list_controller.scss',
            'ks_enterprise_theme/static/src/views/kanban/kanban_view.scss',
            'ks_enterprise_theme/static/src/views/search/search_panel/search_view.scss',
            'ks_enterprise_theme/static/src/views/search/search_bar/search_bar.scss',
            'ks_enterprise_theme/static/src/views/dashboard/dashboard_controller.scss',
            # SCSS — core
            'ks_enterprise_theme/static/src/core/badge_list/badge_list.scss',
            'ks_enterprise_theme/static/src/core/bottom_sheet/bottom_sheet.scss',
            'ks_enterprise_theme/static/src/core/tags_list/tags_list.scss',
            'ks_enterprise_theme/static/src/core/notebook/notebook.scss',
            'ks_enterprise_theme/static/src/core/dropdown/dropdown.scss',
            'ks_enterprise_theme/static/src/core/popover/popover.scss',
            'ks_enterprise_theme/static/src/webclient/dialog/dialog.scss',
            # JS — services (must load before components)
            'ks_enterprise_theme/static/src/webclient/color_scheme/color_scheme_service.js',
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu_service.js',
            # JS — OWL components
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.js',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.js',
            'ks_enterprise_theme/static/src/webclient/burger_menu/burger_menu.js',
            'ks_enterprise_theme/static/src/webclient/share_url/share_url.js',
            'ks_enterprise_theme/static/src/webclient/share_url/burger_menu.js',
            'ks_enterprise_theme/static/src/webclient/webclient.js',
            # JS — view patches
            'ks_enterprise_theme/static/src/views/list/list_renderer_desktop.js',
            # XML templates
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.xml',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.xml',
            'ks_enterprise_theme/static/src/webclient/share_url/burger_menu.xml',
            ('after', 'web/static/src/views/list/list_renderer.xml',
             'ks_enterprise_theme/static/src/views/list/list_renderer_desktop.xml'),
        ],
        # ── BACKEND LAZY (pivot — loaded on demand) ───────────────────────────
        'web.assets_backend_lazy': [
            'ks_enterprise_theme/static/src/views/pivot/pivot_renderer.scss',
            'ks_enterprise_theme/static/src/views/pivot/pivot_renderer.js',
            'ks_enterprise_theme/static/src/views/pivot/pivot_renderer.xml',
        ],
        # ── ENTRY POINT: replace community main.js with Enterprise WebClient ──
        'web.assets_web': [
            ('replace', 'web/static/src/main.js',
             'ks_enterprise_theme/static/src/webclient/main.js'),
        ],
        # ── DARK MODE VARIABLE OVERRIDES ──────────────────────────────────────
        # These are included via ('include', 'web.dark_mode_variables') in dark bundles.
        # We simply add the dark variable files directly — no 'before' reference needed
        # because the dark variables are meant to OVERRIDE the light ones, so load order
        # just needs them to come after the light variable bundles.
        'web.dark_mode_variables': [
            'ks_enterprise_theme/static/src/scss/primary_variables.dark.scss',
            'ks_enterprise_theme/static/src/scss/secondary_variables.dark.scss',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.variables.dark.scss',
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.variables.dark.scss',
        ],
        # ── DARK MODE LAZY BUNDLE ─────────────────────────────────────────────
        'web.assets_backend_lazy_dark': [
            ('include', 'web.dark_mode_variables'),
            'ks_enterprise_theme/static/src/scss/bootstrap_overridden.dark.scss',
            'ks_enterprise_theme/static/src/scss/bs_functions_overridden.dark.scss',
        ],
        # ── FULL DARK BUNDLE (loaded when dark mode is active) ────────────────
        # dark_mode_variables already included by the base web dark bundle mechanism.
        # We add bootstrap dark overrides + all component .dark.scss files.
        'web.assets_web_dark': [
            ('include', 'web.dark_mode_variables'),
            'ks_enterprise_theme/static/src/scss/bootstrap_overridden.dark.scss',
            'ks_enterprise_theme/static/src/scss/bs_functions_overridden.dark.scss',
            # Component dark overrides (webclient)
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu.dark.scss',
            'ks_enterprise_theme/static/src/webclient/home_menu/home_menu_background.dark.scss',
            'ks_enterprise_theme/static/src/webclient/navbar/navbar.dark.scss',
            'ks_enterprise_theme/static/src/search/control_panel/control_panel.dark.scss',
            # Component dark overrides (views)
            'ks_enterprise_theme/static/src/views/list/list_controller.dark.scss',
            'ks_enterprise_theme/static/src/views/kanban/kanban_controller.dark.scss',
            'ks_enterprise_theme/static/src/views/form/form_controller.dark.scss',
            'ks_enterprise_theme/static/src/views/form/button_box/button_box.dark.scss',
            'ks_enterprise_theme/static/src/views/dashboard/dashboard_controller.dark.scss',
            'ks_enterprise_theme/static/src/views/fields/image/image_field.dark.scss',
            'ks_enterprise_theme/static/src/views/fields/properties/properties_field.dark.scss',
            'ks_enterprise_theme/static/src/views/search/search_bar/search_bar.dark.scss',
            'ks_enterprise_theme/static/src/views/search/search_panel/search_view.dark.scss',
            'ks_enterprise_theme/static/src/webclient/settings_form_view/settings_form_view.dark.scss',
            'ks_enterprise_theme/static/src/webclient/dialog/dialog.dark.scss',
            # Component dark overrides (core)
            'ks_enterprise_theme/static/src/core/notebook/notebook.dark.scss',
            'ks_enterprise_theme/static/src/core/badge_list/badge_list.dark.scss',
            'ks_enterprise_theme/static/src/core/bottom_sheet/bottom_sheet.dark.scss',
            'ks_enterprise_theme/static/src/core/colorlist/colorlist.dark.scss',
            'ks_enterprise_theme/static/src/core/dropdown/dropdown.dark.scss',
            'ks_enterprise_theme/static/src/core/popover/popover.dark.scss',
            'ks_enterprise_theme/static/src/core/search/search_panel/search_panel.dark.scss',
            'ks_enterprise_theme/static/src/core/tags_list/tags_list.dark.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
