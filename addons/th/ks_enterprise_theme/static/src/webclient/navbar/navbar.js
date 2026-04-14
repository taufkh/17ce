/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { useService, useBus } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { useEffect, useRef } from "@odoo/owl";

/**
 * EnterpriseNavBar — extends the Community NavBar with:
 *  - 9-dots toggle button to open/close Home Menu overlay
 *  - Active app name + icon displayed next to the toggle
 *  - Integrated with home_menu service for state awareness
 *  - Mobile sidebar integration via burger menu
 */
export class EnterpriseNavBar extends NavBar {
    static template = "ks_enterprise_theme.EnterpriseNavBar";

    setup() {
        super.setup();
        try {
            this.hm = useService("home_menu");
        } catch (e) {
            this.hm = null;
        }
        // pwa service only exists in Enterprise; make it optional in Community
        try { this.pwa = useService("pwa"); } catch (e) { this.pwa = null; }
        this.menuAppsRef = useRef("menuApps");
        this.navRef = useRef("nav");
        this._busToggledCallback = () => this._updateMenuAppsIcon();
        useBus(this.env.bus, "HOME-MENU:TOGGLED", this._busToggledCallback);
        useEffect(() => this._updateMenuAppsIcon());
    }

    get hasBackgroundAction() {
        return this.hm ? this.hm.hasBackgroundAction : false;
    }

    get isInApp() {
        return this.hm ? !this.hm.hasHomeMenu : true;
    }

    _openAppMenuSidebar() {
        if (this.hm && this.hm.hasHomeMenu) {
            this.hm.toggle(false);
        } else {
            this.state.isAppMenuSidebarOpened = true;
        }
    }

    _updateMenuAppsIcon() {
        const menuAppsEl = this.menuAppsRef.el;
        if (!menuAppsEl) return;

        menuAppsEl.classList.toggle("o_hidden", !this.isInApp && !this.hasBackgroundAction);
        menuAppsEl.classList.toggle(
            "o_menu_toggle_back",
            !this.isInApp && this.hasBackgroundAction
        );

        if (!this.isScopedApp) {
            const title =
                !this.isInApp && this.hasBackgroundAction
                    ? _t("Previous view")
                    : _t("Home menu");
            menuAppsEl.title = title;
            menuAppsEl.ariaLabel = title;
        }

        const navEl = this.navRef.el;
        if (!navEl) return;

        const menuBrand = navEl.querySelector(".o_menu_brand");
        if (menuBrand) {
            menuBrand.classList.toggle("o_hidden", !this.isInApp);
        }

        const menuBrandIcon = navEl.querySelector(".o_menu_brand_icon");
        if (menuBrandIcon) {
            menuBrandIcon.classList.toggle("o_hidden", !this.isInApp);
        }

        const appSubMenus = this.appSubMenus?.el;
        if (appSubMenus) {
            appSubMenus.classList.toggle("o_hidden", !this.isInApp);
        }

        const breadcrumb = navEl.querySelector(".o_breadcrumb");
        if (breadcrumb) {
            breadcrumb.classList.toggle("o_hidden", !this.isInApp);
        }
    }

    getAppIconSrc(app) {
        const raw = app?.webIconData;
        if (!raw) {
            return app?.webIcon || "";
        }
        if (raw.startsWith("data:image") || raw.startsWith("/") || raw.startsWith("http")) {
            return raw;
        }
        const prefix = raw.startsWith("P")
            ? "data:image/svg+xml;base64,"
            : `data:${app?.webIconDataMimetype || "image/png"};base64,`;
        return prefix + raw.replace(/\s/g, "");
    }

    /** @override — also open home menu */
    onAllAppsBtnClick() {
        super.onAllAppsBtnClick();
        if (this.hm) {
            this.hm.toggle(true);
        }
        this._closeAppMenuSidebar();
    }
}
