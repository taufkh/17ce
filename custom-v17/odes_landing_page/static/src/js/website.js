const legacyDefine = odoo.define;
 $(document).ready(function() {
    legacyDefine('odes_landing_page.website', function(require) {
      "use strict";
      var ajax = require('web.ajax');
      var html = document.documentElement;
      $(".landing_page_intelligent_automation form").submit(function() {
        ajax.jsonRpc("/intelligent-automation-post", 'call', {
          'contact_name':$(".landing_page_intelligent_automation form input[name='name']").val(),
          'phone':$(".landing_page_intelligent_automation form input[name='phone']").val(),
          'email':$(".landing_page_intelligent_automation form input[name='email']").val(),
          'companyname':$(".landing_page_intelligent_automation form input[name='companyname']").val(),
          'website_id':html.getAttribute('data-website-id') | 0,
        }).then(function(result) {
          if (result){
            if($("#landing_page_dialog").length == 0) {
              $("main").prepend( "<div id='landing_page_dialog'></div>" );
            }
            $("#landing_page_dialog").html("<b>Thank you,</b> we will contact you shortly.");
            $("#landing_page_dialog").show(1000);
            setTimeout(function(){
             $("#landing_page_dialog").hide(1000);    
             $('.landing_page_intelligent_automation form div input').val('')          
             }, 3000);
          }
          else{
            if($("#landing_page_dialog_warning").length == 0) {
              $("main").prepend( "<div id='landing_page_dialog_warning'></div>" );
            }
            $("#landing_page_dialog_warning").html("The name you entered already exists in the database.");
            $("#landing_page_dialog_warning").show(1000);
            setTimeout(function(){
             $("#landing_page_dialog_warning").hide(1000);    
             $('.landing_page_intelligent_automation form div input').val('')          
             }, 3000);
          }

        });

      });

    });


 });