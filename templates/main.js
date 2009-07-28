$(document).ready(function() {
  
  $('#shorturl_form').submit(function(eventObject) {

    $('#shorturl_form').click();
    return false;

  });
  
  
  $('#shorturl_form_submit').click(function(eventObject) {

       $('#ajax_spinner').show();
       $(eventObject.target).attr("disabled", "true");


       $.ajax({
          type: "GET",
          url: "/api",
          data: {url: $('#shorturl_form input[name=url]').val()},
          dataType: 'json',
          success: function(msg){

              $('#ajax_spinner').hide();
              $(eventObject.target).removeAttr("disabled");

              if (msg.success == false) {

              } else {

                  $("#shorturl").text(msg.shorturl);
                  $("#shorturl").show();
              }

          },
          error: function(msg){

            $('#ajax_spinner').hide();
            $(eventObject.target).removeAttr("disabled");

            ScienceSlidesUtil.trackAjax("/ajax/err/");
          }       
        });

  });
  
});