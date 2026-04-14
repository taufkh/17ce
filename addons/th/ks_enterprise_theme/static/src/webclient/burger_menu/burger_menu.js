/** @odoo-module */
import { BurgerMenu } from "@web/webclient/burger_menu/burger_menu";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

/**
 * EnterpriseBurgerMenu — extends the Community BurgerMenu.
 *
 * The key override: when the Home Menu overlay is visible, we don't show
 * the current app name in the burger menu header (there's no active app).
 */
export class EnterpriseBurgerMenu extends BurgerMenu {
    setup() {
        super.setup();
        try {
            this.hm = useService("home_menu");
        } catch (e) {
            this.hm = null;
        }
    }

    get currentApp() {
        // Don't display active app info when the home menu overlay is open
        return (!this.hm || !this.hm.hasHomeMenu) && super.currentApp;
    }
}

const systrayItem = {
    Component: EnterpriseBurgerMenu,
};

// force: true replaces the community burger_menu systray item
registry.category("systray").add("burger_menu", systrayItem, { sequence: 0, force: true });
