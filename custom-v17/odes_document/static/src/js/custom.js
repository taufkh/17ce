odoo.define("odes_document.ajax", function (require) {
  "use strict";
  require("web.dom_ready");

  $(document).ready(function () {
    var $form = $("#pardot-form");


    $form.submit(function(ev){
      ev.preventDefault();

      if($form.hasClass('loading') == false){
        $.ajax({
          type: 'POST',
          url: '/document/form/save', 
          data: $form.serializeArray(),
          dataType: 'json',
          cache: false,
          success: function(datas) {
            try {
                if(datas.success == true){
                  // window.location = datas.url;
                  $('meta[http-equiv="refresh"]').remove();
                  var $redirectTo = $('<meta http-equiv="refresh" content="0; url='+datas.url+'">');
                  $redirectTo.appendTo('head');
                  window.location.assign(datas.url);

                  var $success_msg = $(''
                    +'    <div class="alert alert-success alert-dismissible" style="position:fixed;left: 0;top:0;z-index:2000;width:100%;text-align: center;">'
                    +'      <a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a>'
                    +'        <strong>Thank you for download. Please wait a moment we are generating your file...</strong>'
                    +'    </div>');
                  $success_msg.appendTo('body');
                  
                  document.getElementById("pardot-form").reset();
                }else{
                  alert('Some thing wrong!\n3:'+datas);
                }
            }catch(err) { 
              alert('Some thing wrong!\n1:'+err);
            }
            console.log("datas",datas)

            $form.removeClass('loading');
          },
          error:  function( jqXHR, textStatus, errorThrown ) {
            alert('Some thing wrong!\n2'+errorThrown);
          }
        });
      }
      $form.addClass('loading');
      
    });

   



  });
});
