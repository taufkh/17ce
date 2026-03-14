 $(document).ready(function() {
     $(window).bind('beforeunload', function(){
        Cookies.remove('categ_tmp_id')
      Cookies.remove('brand_tmp_ids')
    });



    function ShowSubmitButton (){
        $('#o_payment_form_pay').fadeOut()
        $('<a id="submit_pay" href="#" class="btn btn-primary">Submit <i class="fa fa-chevron-right"></i></a>').insertAfter( "#o_payment_form_pay" );
        $('#submit_pay').fadeIn()
        $('#submit_pay').click(function(){
            if($('#div_freight_account input[name="input_fa"][value=1]').is(":checked")){
                var freight_account= $("input[name='freight_account']").val()
                if (freight_account) {
                    $('#o_payment_form_pay').fadeIn()
                    $('#o_payment_form_pay').click()
                    $('#submit_pay').fadeOut()
                }
                else{
                    $("input[name='freight_account']").focus()
                    $('#submit_pay').fadeIn()
                }
            }
            else{
                window.location.href = "/shop/submit";
                $('#submit_pay').fadeIn()
            }
        });
    }

     // if($('#product_blog_mccoy').length > 0){
     //    $('#product_blog_mccoy').clone().insertAfter("#wrap.js_sale .container.mb64");
     //    $('#product_blog_mccoy')[0].remove()
     // }

   	$('.mccoy_custom_tab .tablinks').click(function() {
   		var data_id = $(this).data('id')
   		$('.mccoy_custom_tab .tablinks').removeClass('active')
   		$(this).addClass('active')
   		$('.tabcontent_custom_tab_mccoy').hide()
   		$('.tabcontent_custom_tab_mccoy[data-id='+data_id+']').show()
   	});

   	if($('.mccoy_custom_tab .tablinks').length>0){
   		$('.mccoy_custom_tab .tablinks')[0].click()
   	}


    $('#get_best_price').click(function() {

      if($('.spinner_wrapper .full_screen').length<=0){
            $('main').prepend('<div class="spinner_wrapper full_screen"><div class="spinner_inner"><i class="fa fa fa-refresh rotating"></i></div></div>');
        }
      $('.spinner_wrapper.full_screen').fadeIn(); 
      $('.mccoy_custom_tab .tablinks[data-type="inquiry"]').click()
      $('html, body').animate({
            scrollTop: 999999999999
        }, 500); 
      $('html, body').animate({
            scrollTop: parseInt($('.mccoy_custom_tab .tablinks[data-type="inquiry"]').offset().top-100)
        }, 500); 
      
      
      $('.spinner_wrapper.full_screen').fadeOut(3000); 
       
      

    });

      


    $("form[action='/shop/subscribe']").submit(function() {
        if($("#mccoy_dialog").length == 0) {
          $("main").prepend( "<div id='mccoy_dialog'></div>" );
        }
        $("#mccoy_dialog").html("<b>Thank you for your subscription.</b> Your subscription has been confirmed.");
        $("#mccoy_dialog").show(1000);
        setTimeout(function(){
         $("#mccoy_dialog").hide(1000);              
         }, 3000);

    });


    $(".scrool_top_mccoy").click(function(){
        $('html,body').animate({
            scrollTop: 0
        }, 700);
    });

    // $('#o_shop_collapse_category .nav-item .dropdown').click(function(){
    //   check_fa = $(this).parent().find('.fa')
    //   if(check_fa.length){
    //     if($(check_fa).hasClass('fa-chevron-right')){
    //       $(check_fa).parent().siblings().find('.fa-chevron-down:first').click();
    //       $(check_fa).parents('li').find('ul:first').show('normal');
    //       $(check_fa).toggleClass('fa-chevron-down fa-chevron-right');
    //     }
    //     else if($(check_fa).hasClass('fa-chevron-down')){
    //       $(check_fa).parent().find('ul:first').hide('normal');
    //       $(check_fa).toggleClass('fa-chevron-down fa-chevron-right');
    //     }
    //   }
      
    // });

    $('#o_shop_collapse_category li.nav-item').hover(function () {
        var menu_vertical_subvertical = $(this).find('.menu_vertical_subvertical')
        if(menu_vertical_subvertical.length>0){
          $(menu_vertical_subvertical[0]).addClass('active_menu');
        }
    }, function () {
        var menu_vertical_subvertical = $(this).find('.menu_vertical_subvertical')
        if(menu_vertical_subvertical.length>0){
          $(menu_vertical_subvertical[0]).removeClass('active_menu');
        }
    });

    $('#o_shop_collapse_category li.nav-item a').click(function(){
      $this = this
      // $('#category_active_title').remove()
     //  check$this = $($(this).parents(".dropdown-content")).prev()
     // $('#o_shop_collapse_category .nav-item .dropdown').each(function( index ) {
     //     check_fa = $(this).parent().find('.fa')
     //      if(check_fa.length && $this!=this){
     //        if($(check_fa).hasClass('fa-chevron-down') && $(this).text()!=check$this.html()){
     //          $(check_fa).parent().find('ul:first').hide('normal');
     //          $(check_fa).toggleClass('fa-chevron-down fa-chevron-right');
     //        }
     //      }
     //  });

      if($('.spinner_wrapper .full_screen').length<=0){
            $('main').prepend('<div class="spinner_wrapper full_screen"><div class="spinner_inner"><i class="fa fa fa-refresh rotating"></i></div></div>');
        }
      $('.spinner_wrapper.full_screen').fadeIn(); 
      $('#o_shop_collapse_category li.nav-item a').removeClass('active')
      $(this).addClass('active');
      var data_id = $(this).data('id')
      var text_categ = $(this).text()

      if (data_id){
        Cookies.set('categ_tmp_id',parseInt(data_id));
      }
      // $('.productlist-top-right ul li#product_count').after("<li id='category_active_title'><small>Category : "+text_categ+"</small></li>")
      $(".o_wsale_products_main_row #products_grid").load(location.href + " .o_wsale_products_main_row #products_grid > *",function(){
              $('.spinner_wrapper.full_screen').fadeOut(1000);
              // $('.productlist-top-right ul li#product_count').after("<li id='category_active_title'><small>Category : "+text_categ+"</small></li>")
          }); 
      $(".oe_website_sale .products_pager.justify-content-between").load(location.href + " .oe_website_sale .products_pager.justify-content-between > *",function(){

          }); 
      $(".oe_website_sale .products_pager.justify-content-center").load(location.href + " .oe_website_sale .products_pager.justify-content-center > *",function(){

          }); 
      
    });

    $('form.js_product_partners input').on('change', function(event) {
        var value = $('form.js_product_partners input:checked').serialize()
        if($('.spinner_wrapper .full_screen').length<=0){
            $('main').prepend('<div class="spinner_wrapper full_screen"><div class="spinner_inner"><i class="fa fa fa-refresh rotating"></i></div></div>');
        }
        $('.spinner_wrapper.full_screen').fadeIn(); 
 
          Cookies.set('brand_tmp_ids',value);
        
        $(".o_wsale_products_main_row #products_grid").load(location.href + " .o_wsale_products_main_row #products_grid > *",function(){
              $('.spinner_wrapper.full_screen').fadeOut(1000);
          }); 
        $(".oe_website_sale .products_pager.justify-content-between").load(location.href + " .oe_website_sale .products_pager.justify-content-between > *",function(){

          }); 
      $(".oe_website_sale .products_pager.justify-content-center").load(location.href + " .oe_website_sale .products_pager.justify-content-center > *",function(){

          }); 
        
    });

    // $( "#products_grid .oe_product .oe_product_image" ).hover(
    //   function() {
    //     $( this ).find( "a.d-block" ).addClass('zoom_img_tree_view');
    //   }, function() {
    //     $( this ).find( "a.d-block" ).removeClass('zoom_img_tree_view');
    //   }
    // );

    $( "#products_grid .oe_product .oe_product_image" ).click(function(){
      var urla = $(this).find('a[itemprop="url"]').attr('href')
      location.href = urla
    })


    $('li.o_delivery_carrier_select').each(function(index, value) {
      var badge = $(this).find('.badge')
      if(badge.text() == 'Free') {
        badge.hide()
      }
    });

    $('#div_freight_account input[name="input_fa"]').click(function(){
        if($('#div_freight_account input[name="input_fa"][value=1]').is(":checked")){
            $('input#freight_account').fadeIn()
        }
        else{
            $('input#freight_account').fadeOut()
        }
      
    });

    if($('#div_freight_account').length) {
        ShowSubmitButton()
    }
    else{
        $('#shipping_and_billing a').fadeOut()
    }



    var owl1 = $(".owl-carousel-mccoy-blog");

        owl1.owlCarousel({

            loop: false,
            autoplay: true,
            autoplayTimeout: 3000,
            margin: 10,

            responsiveClass: true,
            responsive: {
                0: {
                    items: 1,
                },
                400: {
                    items: 2,
                },
                600: {
                    items: 3,
                },
                1000: {
                    items: 4,
                }
            }

        });

 });