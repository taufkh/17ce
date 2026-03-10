function CheckPassword(new_password,confirm_pwd) {
    console.log(new_password,confirm_pwd, 'fdfd')
    if(new_password == confirm_pwd)
    {
        
        password_confirm = "Passwords match!";
        $(".varpassword_confirm_strength").html(password_confirm)

    }else{
        password_confirm = "Passwords do not match!";
        $(".varpassword_confirm_strength").html(password_confirm)	
    }
}

  
