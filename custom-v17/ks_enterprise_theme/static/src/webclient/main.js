/** @odoo-module */
import { startWebClient } from "@web/start";
import { WebClientEnterprise } from "./webclient";

/**
 * Entry point for ks_enterprise_theme.
 * Replaces community main.js to boot WebClientEnterprise instead of
 * the base WebClient, enabling the Enterprise home menu overlay and
 * the Enterprise NavBar.
 */
startWebClient(WebClientEnterprise);
