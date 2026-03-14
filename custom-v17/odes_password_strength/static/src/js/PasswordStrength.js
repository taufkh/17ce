
function CheckPasswordStrength(new_password,varpassword_strength) { 
    $(".button.oe_button.oe_form_button").remove();
    var password_strength = document.getElementById("password_strength");
    if (new_password.length == 0) {
        new_password = "";
        return;
    }
    console.log(new_password, varpassword_strength, 'dddd')
    var regex = new Array();
    regex.push("[A-Z]"); 
    regex.push("[a-z]");
    regex.push("[0-9]");
    regex.push("[$@$!%*#?& `]"); 
    var passed = 0;

    for (var i = 0; i < regex.length; i++) {
        if (new RegExp(regex[i]).test(new_password)) {
            passed++;
        }
    }
    if (passed > 2 && new_password.length > 8) {
        passed++;
    }
     var color = "";
     var strength = "";
    switch (passed) {
        case 0:
        case 1:
            strength = "Weak";
            strength_style = 'color : #FF0000;';
            password_strength_meter =  1; 
            break;
        case 2:
            strength = "Good";
            strength_style = 'color : #FFA500;';
            password_strength_meter=  2; 
            break;
        case 3:
            strength = "Very Good";
            strength_style = 'color : #EE7600;';
            password_strength_meter=  3; 
            break;
        case 4:
            strength = "<div id=strong>Strong</div>";
            strength_style = 'color : #00FF00;';
            password_strength_meter=  4; 
            break;
        case 5:
            strength = "<div id=very-strong>Very Strong</div>";
            strength_style = 'color : #006400;';
            password_strength_meter=  5; 
            break;
    }
    password_strength = strength;
    console.log(password_strength_meter, 'password_strength_meter')
//    $(".varpassword_strength").attr("id", strength);
//    $(".varpassword_strength").html(password_strength_meter);
    
    var html = '<div style="'+strength_style+'">'+strength+'</div>';
    $(".varpassword_strength").html(html);
    
   
}

     
           
       

