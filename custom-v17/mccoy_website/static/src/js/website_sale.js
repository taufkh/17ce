
odoo.define('mccoy_website.mccoy_website', function (require) {
'use strict';

var core = require('web.core');
var config = require('web.config');
var publicWidget = require('web.public.widget');
var VariantMixin = require('sale.VariantMixin');
var wSaleUtils = require('website_sale.utils');
const wUtils = require('website.utils');
require('website_sale.website_sale');

publicWidget.registry.WebsiteSale.include({
    // selector: '.oe_website_sale',
    // events: _.include({}, publicWidget.registry.WebsiteSale.prototype.events, {
    //     'click .oe_cart a.mccoy_js_add_suggested_products': '_onClickSuggestedProductmccoy',
    //     // 'change .oe_cart input.js_quantity[data-product-id]': '_onChangeCartQuantitymccoy',
    // }),


    _onClickSuggestedProduct: function (ev) {
        if (!$(ev.currentTarget).prev('input').val()) {
            $(ev.currentTarget).prev('input').val(1);
        }
        $(ev.currentTarget).prev('input').trigger('change');
    },
    // _onChangeCartQuantitymccoy: function (ev) {
    //     var $input = $(ev.currentTarget);
    //     if ($input.data('update_change')) {
    //         return;
    //     }
    //     var value = parseInt($input.val() || 0, 10);
    //     if (isNaN(value)) {
    //         value = 1;
    //     }
    //     var $dom = $input.closest('tr');
    //     // var default_price = parseFloat($dom.find('.text-danger > span.oe_currency_value').text());
    //     var $dom_optional = $dom.nextUntil(':not(.optional_product.info)');
    //     var line_id = parseInt($input.data('line-id'), 10);
    //     var productIDs = [parseInt($input.data('product-id'), 10)];
    //     WebsiteSale._changeCartQuantity($input, value, $dom_optional, line_id, productIDs);
    // },

});
});
