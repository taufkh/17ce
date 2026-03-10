odoo.define('mccoy_websitew.product_configurator_modal', function (require) {
    "use strict";

var OptionalProductsModal = require('sale_product_configurator.OptionalProductsModal');
var ajax = require('web.ajax');

OptionalProductsModal.include({

    onChangeVariant: function (ev) {
        var $parent = $(ev.target).closest('.js_product');
        if (!$parent.data('uniqueId')) {
            $parent.data('uniqueId', _.uniqueId());
        }
        this._throttledGetCombinationInfo($parent.data('uniqueId'))(ev);
        var $tr = $($(ev.target).parents()[4])
        if($tr.hasClass('js_product')) {
            setTimeout(function(){ 

                var product_id = $tr.find('input.product_id').val()
                var $input =  $tr.find('input[name="add_qty"]')
                var currency_id = parseInt($input.data("currency_id"))
                var have_moq = $input.data("havemoq")
                if(have_moq){
                    ajax.jsonRpc("/get-actual-price-moq-product-change", 'call', {
                            'product_id':parseInt(product_id),
                            'currency_id':parseInt(currency_id),
                        }).then(function(result) {
                            var price_unit = result[0]
                            var new_qty = result[1]
                            $tr.find('input[name="add_qty"]').data('product_id', product_id);
                            $tr.find('input.min_qty').val(parseInt(new_qty))
                            $input.val(parseInt(new_qty))
                            $input.data('min', parseInt(new_qty));
                            price_unit = parseFloat(price_unit)
                            $tr.find('.oe_currency_value').text(price_unit.toFixed(2))
                    });
               }

            }, 500);

            


        }
    },

    _onAddOrRemoveOption: function (ev) {
        ev.preventDefault();
        var self = this;
        var $target = $(ev.currentTarget);
        var $modal = $target.parents('.oe_optional_products_modal');
        var $parent = $target.parents('.js_product:first');
        $parent.find("a.js_add, span.js_remove").toggleClass('d-none');
        $parent.find(".js_remove");

        var productTemplateId = $parent.find(".product_template_id").val();
        if ($target.hasClass('js_add')) {
            self._onAddOption($modal, $parent, productTemplateId);
            var get_min_qty = $($target.parents()[1]).find('input.min_qty').val()
            $($target.parents()[1]).find('input[name="add_qty"]').val(get_min_qty)
             $($target.parents()[1]).find('input[name="add_qty"]').data('min', get_min_qty);
        } else {
            self._onRemoveOption($modal, $parent);
            var get_min_qty = $($target.parents()[2]).find('input.min_qty').val()
            $($target.parents()[2]).find('input[name="add_qty"]').val(get_min_qty)
            $($target.parents()[2]).find('input[name="add_qty"]').data('min', get_min_qty);
            $($($target.parents()[2]).find('.float_left.js_add_cart_json')).click()
        }
    },


    onClickAddCartJSON: function (ev) {
        ev.preventDefault();
        var $link = $(ev.currentTarget);
        var qty_set = 1
        var moq_qty = parseInt($link.data("moq") || 0);
        if (moq_qty){
            qty_set = moq_qty
        }


        var $input = $link.closest('.input-group').find("input");
        var product_id = parseInt($input.data("product_id"))
        var min = parseFloat($input.data("min") || 0);
        var max = parseFloat($input.data("max") || Infinity);
        var previousQty = parseFloat($input.val(),10);
        var quantity = ($link.has(".fa-minus").length ? qty_set*-1 : qty_set) + previousQty;
        var newQty = quantity > min ? (quantity < max ? quantity : max) : min;
        $input.val(newQty);
        this.updateprice(product_id,newQty,$input);
        

        return false;
    },
    updateprice: function (product_id,qty,$input) {
        var have_moq = $input.data("havemoq")
        var currency_id = parseInt($input.data("currency_id"))
       if(have_moq){
            ajax.jsonRpc("/get-actual-price-product", 'call', {
                    'product_id':product_id,
                    'currency_id':currency_id,
                    'qty':parseFloat(qty),
                }).then(function(price_unit) {
                    price_unit = parseFloat(price_unit)
                    $($($($input).parents()[2]).find('.oe_currency_value')).text(price_unit.toFixed(2))
            });
       }
    }
    /**
     * If the "isWebsite" param is true, will also disable the following events:
     * - change [data-attribute_exclusions]
     * - click button.js_add_cart_json
     *
     * This has to be done because those events are already registered at the "website_sale"
     * component level.
     * This modal is part of the form that has these events registered and we
     * want to avoid duplicates.
     *
     * @override
     * @param {$.Element} parent The parent container
     * @param {Object} params
     * @param {boolean} params.isWebsite If we're on a web shop page, we need some
     *   custom behavior
     */
    
});

});