
// ---------------------------------------------------------------------
// Submit event on the "Log in" button:

// this function disables the submit button inside the current element:
function whenClickedOnLogIn() {
    $(this).find(':input[type=submit]').attr('disabled', true);
  }
  
  // add the on submit event listener to the $("#login-form"):
  $("#login-form").submit(whenClickedOnLogIn)



