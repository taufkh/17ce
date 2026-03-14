$(document).ready(function() {
	odoo.define('mccoy_website.website_json', function(require) {
	    "use strict";
	    var ajax = require('web.ajax');
	    var wSaleUtils = require('website_sale.utils');

	    $("input[name='product_id']").trigger("change");

	    function updateprice(product_id,qty){
	    	var $input = $("input[name='add_qty']")
	    	var have_moq = $input.data("havemoq")
           var currency_id = parseInt($input.data("currency_id"))
           if(have_moq){
           		ajax.jsonRpc("/get-actual-price-product", 'call', {
						'product_id':product_id,
						'currency_id':currency_id,
						'qty':parseFloat(qty),
					}).then(function(price_unit) {
						price_unit = parseFloat(price_unit)
						$('.oe_price_h4 .oe_currency_value').text(price_unit.toFixed(2))
				});
           }
	    }

	    function changeproductvariant(product_id){
	    	var $input = $("input[name='add_qty']")
	    	var have_moq = $input.data("havemoq")
           var currency_id = parseInt($input.data("currency_id"))
           if(have_moq){
           		ajax.jsonRpc("/get-actual-price-moq-product-change", 'call', {
						'product_id':product_id,
						'currency_id':currency_id,
					}).then(function(result) {
						var price_unit = result[0]
						var new_qty = result[1]
						$("input[name='add_qty']").val(parseInt(new_qty))
						$("input[name='add_qty']").data('min', parseInt(new_qty));
						price_unit = parseFloat(price_unit)
						$('.oe_price_h4 .oe_currency_value').text(price_unit.toFixed(2))
				});
           }
	    }

	    $("input[name='product_id']").change(function(ev) {
	    	var product_id=parseInt($(this).val())
	    	changeproductvariant(product_id)
	    });

	    
	    $("button[id='o_payment_form_pay']").click(function(ev) {
	    	if($("input[name='freight_account']").length){
	    		var freight_account= $("input[name='freight_account']").val()
		    	ajax.jsonRpc("/set-freight-account-order", 'call', {
							'freight_account':freight_account,
						}).then(function(result) {
					});
	    	}
		    	
	    })

	    

	    $('.mccoy_js_add_cart_json').click(function(ev) {
           ev.preventDefault();
           var product_id = parseInt($("input[name='product_id']").val())
           var qtyset = 1
           if($('#moq_qty_product_value').length > 0){
            qtyset = parseInt($('#moq_qty_product_value').text())
           }
           var $link = $(ev.currentTarget);
           var $input =$link.parent().parent().find('input[name="add_qty"]');
           var min = parseFloat($input.data("min") || 1);
           var max = parseFloat($input.data("max") || Infinity);
           var quantity = ($link.hasClass("float_left") ? qtyset : (qtyset*-1)) + parseFloat($input.val(),10);
           var qty = quantity > min ? (quantity < max ? quantity : max) : min
           $('input[name="add_qty"]').val(qty);
           updateprice(product_id,qty);
       });

	    var t;
			$('body').delegate( '.mccoy_js_add_cart_json1', 'click', function(ev){
				var qtyset = 1
	           var $link = $(ev.currentTarget);
	           var $moq_qty_product_value =$link.parent().parent().find('.moq_qty_product_value');
	           if($moq_qty_product_value.length > 0){
	            qtyset = parseInt($moq_qty_product_value.text())
	           }
	           
	           var $input =$link.parent().parent().find('input[name="add_qty"]');
	           var min = parseFloat($input.data("min") || 1);
	           var max = parseFloat($input.data("max") || Infinity);
	           var quantity = ($link.hasClass("float_left") ? qtyset : (qtyset*-1)) + parseFloat($input.val(),10);
	           var qty = quantity > min ? (quantity < max ? quantity : max) : min
	           $input.val(qty);
	           var line_id = parseInt($input.data('line-id'), 10);
	        	var productIDs = parseInt($input.data('product-id'), 10);

			    clearTimeout(t);
			    t = setTimeout( function(){
			        ajax.jsonRpc("/shop/cart/update_json", 'call', {
						'line_id':line_id,
						'product_id':productIDs,
						'set_qty':qty,
					}).then(function(result) {
						$("td.td-price[name='price']#"+line_id).load(location.href + " td.td-price[name='price']#"+line_id+" > *",function(){
				              
				          }); 
						var $qtyNavBar = $(".my_cart_quantity");
					    _.each($qtyNavBar, function ($qtyNavBare) {
					        var $qtyNavBare = $($qtyNavBare);
					        $qtyNavBare.parents('li:first').removeClass('d-none');
					        $qtyNavBare.html(result.cart_quantity).hide().fadeIn(600);
					    });
				});
			    },500)
			})

	   //  $('.mccoy_js_add_cart_json1').click(function(ev) {
	   //  	ev.stopImmediatePropagation();
	   //  	ev.stopPropagation();
    //        var qtyset = 1
    //        var $link = $(ev.currentTarget);
    //        var $moq_qty_product_value =$link.parent().parent().find('.moq_qty_product_value');
    //        if($moq_qty_product_value.length > 0){
    //         qtyset = parseInt($moq_qty_product_value.text())
    //        }
           
    //        var $input =$link.parent().parent().find('input[name="add_qty"]');
    //        var min = parseFloat($input.data("min") || 1);
    //        var max = parseFloat($input.data("max") || Infinity);
    //        var quantity = ($link.hasClass("float_left") ? qtyset : (qtyset*-1)) + parseFloat($input.val(),10);
    //        var qty = quantity > min ? (quantity < max ? quantity : max) : min
    //        $input.val(qty);
    //        var line_id = parseInt($input.data('line-id'), 10);
    //     	var productIDs = parseInt($input.data('product-id'), 10);
    //        ajax.jsonRpc("/shop/cart/update_json", 'call', {
				// 		'line_id':line_id,
				// 		'product_id':productIDs,
				// 		'set_qty':qty,
				// 	}).then(function(result) {
				// 		var $qtyNavBar = $(".my_cart_quantity");
				// 	    _.each($qtyNavBar, function ($qtyNavBare) {
				// 	        var $qtyNavBare = $($qtyNavBare);
				// 	        $qtyNavBare.parents('li:first').removeClass('d-none');
				// 	        $qtyNavBare.html(result.cart_quantity).hide().fadeIn(600);
				// 	    });
				// });
    // //    });


	    $('.submit_enquiry_mccoy').click(function() {
			$('#contactus_section input[name="name"]').removeClass("is-invalid");
			$('#contactus_section input[name="phone"]').removeClass("is-invalid");
			$('#contactus_section input[name="email"]').removeClass("is-invalid");
			$('#contactus_section input[name="subject"]').removeClass("is-invalid");
			var success = 1;
			if($('#contactus_section input[name="name"]').val().length<=0){
				$('#contactus_section input[name="name"]').addClass("is-invalid");
				success = 0;
			}
			if($('#contactus_section input[name="phone"]').val().length<=0){
				$('#contactus_section input[name="phone"]').addClass("is-invalid");
				success = 0;
			}
			if($('#contactus_section input[name="email"]').val().length<=0){
				$('#contactus_section input[name="email"]').addClass("is-invalid");
				success = 0;
			}
			if($('#contactus_section input[name="subject"]').val().length<=0){
				$('#contactus_section input[name="subject"]').addClass("is-invalid");
				success = 0;
			}
			if(success==1){
				var name = $('#contactus_section input[name="name"]').val()
				var phone = $('#contactus_section input[name="phone"]').val()
				var email = $('#contactus_section input[name="email"]').val()
				var subject = $('#contactus_section input[name="subject"]').val()
				var company = $('#contactus_section input[name="company"]').val()
				var company_url = $('#contactus_section input[name="company_url"]').val()
				var question = $('#contactus_section textarea[name="question"]').val()
				var company_id = $('#contactus_section input[name="company_id"]').val()
				var product_id = $('.js_main_product input[name="product_template_id"]').val()
				ajax.jsonRpc("/inquiry-crm", 'call', {
					'product_id':product_id,
					'name':name,
					'phone':phone,
					'email':email,
					'subject':subject,
					'company':company,
					'company_url':company_url,
					'question':question,
					'company_id':company_id,
				}).then(function() {
					if($('.spinner_wrapper .full_screen').length<=0){
            $('main').prepend('<div class="spinner_wrapper full_screen"><div class="spinner_inner"><i class="fa fa fa-refresh rotating"></i></div></div>');
        }
					 $('.spinner_wrapper.full_screen').fadeIn(); 
		           if($("#mccoy_dialog").length == 0) {
			          $("main").prepend( "<div id='mccoy_dialog'></div>" );
			        }
			        
			        setTimeout(function(){    
			         $('.spinner_wrapper.full_screen').fadeOut(1000);   
			         $("#mccoy_dialog").html("<b>Thank you.</b> Our Admin will contact you soon.");
			        	$("#mccoy_dialog").show(1000);    
			        	setTimeout(function(){  
			        		$("#mccoy_dialog").hide(1000); 
			        	}, 3000);
			         }, 3000);
		        });

			}	
		});


	});
		
});