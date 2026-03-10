odoo.define('sale_product_configurator.ProductConfiguratorFormRenderer', function (require) {
"use strict";

var FormRenderer = require('web.FormRenderer');
var VariantMixin = require('sale.VariantMixin');
var ajax = require('web.ajax');

var ProductConfiguratorFormRenderer = FormRenderer.extend(VariantMixin, {

    events: _.extend({}, FormRenderer.prototype.events, VariantMixin.events, {
        'click button.js_add_cart_json': 'onClickAddCartJSON',
        'change input.product_id': '_onChangePVariant',
        'change input.mccoy_addqty': '_onChangeAddqty',
    }),

    /**
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this.pricelistId = this.state.context.default_pricelist_id || 0;
        this.partnerId = this.state.context.default_partner_id || 0;
    },
    /**
     * @override
     */
    start: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.$el.append($('<div>', {class: 'configurator_container'}));
            self.renderConfigurator(self.configuratorHtml);
            self._checkMode();
        });
    },

    //--------------------------------------------------------------------------
    // Public
    //--------------------------------------------------------------------------

    /**
     * Renders the product configurator within the form
     *
     * Will also:
     *
     * - add events handling for variant changes
     * - trigger variant change to compute the price and other
     *   variant specific changes
     *
     * @param {string} configuratorHtml the evaluated template of
     *   the product configurator
     */
    renderConfigurator: function (configuratorHtml) {
        var $configuratorContainer = this.$('.configurator_container');
        $configuratorContainer.empty();

        var $configuratorHtml = $(configuratorHtml);
        $configuratorHtml.appendTo($configuratorContainer);

        this.triggerVariantChange($configuratorContainer);
        this._applyCustomValues();
        var product_id = parseInt($(".configurator_container input[name='product_id']").val())
        var qty = parseFloat($(".configurator_container input[name='add_qty']").val())
        this.updateprice(product_id,qty)
    },

    updateprice: function (product_id,qty) {
        var $input = $(".configurator_container input[name='add_qty']")
        var have_moq = $input.data("havemoq")
        var currency_id = parseInt($input.data("currency_id"))
       if(have_moq){
            ajax.jsonRpc("/get-actual-price-product", 'call', {
                    'product_id':parseInt(product_id),
                    'currency_id':currency_id,
                    'qty':parseFloat(qty),
                }).then(function(price_unit) {
                    price_unit = parseFloat(price_unit)
                    $('.configurator_container .oe_currency_value').text(price_unit.toFixed(2))
            });
       }

    },

    _onChangeAddqty: function (ev) {
        var product_id = parseInt($(".configurator_container input[name='product_id']").val());
        var $input = $(ev.currentTarget)
        var qty = $input.val()
        var have_moq = $input.data("havemoq")
        var min_qty = parseInt($input.data("min"))
       if(!isNaN(parseInt(qty))){
            var moq = $input.data("moq")
            qty = parseInt(qty)
            // if (qty <= min_qty) {
            //     qty = min_qty
            // }
            // else {
            //     var residual = 0;
            //     qty = qty - 1
            //     var check_qty = qty - min_qty
            //     residual = check_qty % moq
            //     qty = (check_qty + min_qty- residual) + moq
                
            // }
            // $input.val(qty)
            if(have_moq){
                this.updateprice(product_id,qty)
            }
       }

    },

    _onChangePVariant: function (ev) {
        var product_id = parseInt($(ev.currentTarget).val());

        var $input = $(".configurator_container input[name='add_qty']")
        var $list_sales = $(".configurator_container .list_sales")
        var $list_sales_tbody = $(".configurator_container .list_sales tbody")
        var $input_code = $(".configurator_container input[name='default_code']")
        var cust_id = parseInt($(".configurator_container input.cust_id").val())
        var have_moq = $input.data("havemoq")
        var currency_id = parseInt($input.data("currency_id"))
        $list_sales_tbody.remove()
        ajax.jsonRpc("/get-history-sales-product", 'call', {
                'product_id':product_id,
                'cust_id':cust_id,
            }).then(function(result) {
                $list_sales.append(result)
        });

       if(have_moq){
            ajax.jsonRpc("/get-actual-price-moq-product-change", 'call', {
                    'product_id':product_id,
                    'currency_id':currency_id,
                }).then(function(result) {
                    var price_unit = result[0]
                    var new_qty = result[1]
                    var code = result[2]
                    $input.val(parseInt(new_qty))
                    $input_code.val(code)
                    $input.data('min', parseInt(new_qty));
                    price_unit = parseFloat(price_unit)
                    $('.configurator_container .oe_currency_value').text(price_unit.toFixed(2))
            });
       }
    },
    onClickAddCartJSON: function (ev) {
        var qty_set = 1
        ev.preventDefault();
        var product_id = parseInt($(".configurator_container input[name='product_id']").val())
        var $link = $(ev.currentTarget);
        var $input = $link.closest('.input-group').find("input");

        var moq_qty = parseInt($input.data("moq") || 0);
        if (moq_qty){
            qty_set = moq_qty
        }

        var min = parseFloat(1 || 0);
        var max = parseFloat($input.data("max") || Infinity);
        var previousQty = parseFloat($input.val() || 0, 10);
        var quantity = ($link.has(".fa-minus").length ? -1 : 1) + previousQty;
        var quantity = ($link.has(".fa-minus").length ? qty_set*-1 : qty_set) + previousQty;
        var newQty = quantity > min ? (quantity < max ? quantity : max) : min;

        if (newQty !== previousQty) {
            $input.val(newQty);
            this.updateprice(product_id,newQty)
        }

        return false;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * If the configuratorMode in the given context is 'edit', we need to
     * hide the regular 'Add' button to replace it with an 'EDIT' button.
     *
     * If the configuratorMode is set to 'options', we will directly open the
     * options modal.
     *
     * @private
     */
    _checkMode: function () {
        if (this.state.context.configuratorMode === 'edit') {
            this.$('.o_sale_product_configurator_add').hide();
            this.$('.o_sale_product_configurator_edit').css('display', 'inline-block');
        } else if (this.state.context.configuratorMode === 'options') {
            this.trigger_up('handle_add');
        }
    },

    /**
     * Toggles the add button depending on the possibility of the current
     * combination.
     *
     * @override
     */
    _toggleDisable: function ($parent, isCombinationPossible) {
        VariantMixin._toggleDisable.apply(this, arguments);
        $parent.parents('.modal').find('.o_sale_product_configurator_add').toggleClass('disabled', !isCombinationPossible);
    },

    /**
     * Will fill the custom values input based on the provided initial configuration.
     *
     * @private
     */
    _applyCustomValues: function () {
        var self = this;
        var customValueIds = this.state.data.product_custom_attribute_value_ids;
        if (customValueIds) {
            _.each(customValueIds.data, function (customValue) {
                if (customValue.data.custom_value) {
                    var attributeValueId = customValue.data.custom_product_template_attribute_value_id.data.id;
                    var $input = self._findRelatedAttributeValueInput(attributeValueId);
                    $input
                        .closest('li[data-attribute_id]')
                        .find('.variant_custom_value')
                        .val(customValue.data.custom_value);
                }
            });
        }
    },

    /**
     * Find the $.Element input/select related to that product.attribute.value
     *
     * @param {integer} attributeValueId
     *
     * @private
     */
    _findRelatedAttributeValueInput: function (attributeValueId) {
        var selectors = [
            'ul.js_add_cart_variants input[data-value_id="' + attributeValueId + '"]',
            'ul.js_add_cart_variants option[data-value_id="' + attributeValueId + '"]'
        ];

        return this.$(selectors.join(', '));
    }
});

return ProductConfiguratorFormRenderer;

});
