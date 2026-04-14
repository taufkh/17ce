/** @odoo-module */
import { WebClient } from "@web/webclient/webclient";
import { useService } from "@web/core/utils/hooks";
import { EnterpriseNavBar } from "./navbar/navbar";

/**
 * WebClientEnterprise — extends the Community WebClient with:
 *  - EnterpriseNavBar (9-dots toggle + active app name/icon)
 *  - Home Menu overlay as the default landing page after login
 */
export class WebClientEnterprise extends WebClient {
    static components = {
        ...WebClient.components,
        NavBar: EnterpriseNavBar,
    };

    setup() {
        super.setup();
        try {
            this.hm = useService("home_menu");
        } catch (e) {
            this.hm = null;
        }
    }

    /** Override: show Home Menu overlay instead of the first app on load */
    _loadDefaultApp() {
        if (this.hm) {
            return this.hm.toggle(true);
        }
        return super._loadDefaultApp(...arguments);
    }
}
