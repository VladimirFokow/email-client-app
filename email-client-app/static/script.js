// Activate feather icons:
(function () {
  'use strict'  // make sure that the code is executed in "strict mode", meaning that you can't use undeclared variables (best practice)
  feather.replace() 
}())  // it is IIFE (Immediately Invoked Function Expression) - it is called immediately after definition because of the () at the end


// Activate tooltips (hints when hovering over an element):
var tooltipTriggerList = [].slice.call($('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
var emailTooltip = tooltipList[0]



// ---------------------------------------------------------------------
// Submit event on the "Log in" button:

// this function disables the submit button inside the current element:
function whenClickedOnLogIn() {
  $(this).find(':input[type=submit]').attr('disabled', true);
}

// add the on submit event listener to the $("#login-form"):
$("#login-form").submit(whenClickedOnLogIn)



// ---------------------------------------------------------------------
// Click event on the email address:

// this function copies a string to the clipboard:
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
}

// this function writes a string to the emailTooltip (to the pop-up hint):
function writeToTooltip(text) {
  // Note: this is a hacky solution
  $("#navbar-email").attr("title", text)
  $("#navbar-email").attr("data-bs-original-title", text)
  emailTooltip._getTipElement().innerText = text
  
  // If mouse is hovering over $("#navbar-email"):
  if ($("#navbar-email").is(":hover")) {
    emailTooltip.show()
  }
}

// this function is called when the user clicks on the email address:
function whenClickedOnEmail() {
  copyToClipboard($(this).text().trim())
  
  // Write "Copied!" it to the emailTooltip:
  writeToTooltip("✅ Copied!")
  // disable the click event listener on the $("#navbar-email"):
  $(this).off("click")
  
  // Wait for 2 seconds, then write "copy to clipboard" to the emailTooltip:
  setTimeout(() => {
    writeToTooltip("copy to clipboard")
    // enable the click event listener on the $("#navbar-email") again:
    $(this).click(whenClickedOnEmail)
  }
  , 2000)
}
// Note: $(this) is used not to run the DOM query every time. It will be the same as $("#navbar-email").

// add the onclick event listener to the $("#navbar-email"):
$("#navbar-email").click(whenClickedOnEmail)




// ---------------------------------------------------------------------
// Toggle "active" class of the navigation buttons on the first sidebar:

let allFolders = $(".folder");

// this function toggles the "active" class on the clicked folder
// and removes it from all the other folders:
function toggleActiveClass(allFolders, activeFolder) {
  for (const folder of allFolders) {
    folder.classList.remove("active");  // remove the "active" class from all folders
  }
  activeFolder.classList.add("active");  // add the "active" class to the clicked folder
}

// For all existing folders: add this click event listener:
for (const folder of allFolders) {
  folder.addEventListener("click", event => {
    toggleActiveClass(allFolders, event.target);
  });
}



// ---------------------------------------------------------------------












