
// Activate the feather icons:
(function () {
  'use strict'  // make sure that the code is executed in "strict mode", meaning that you can't use undeclared variables (best practice)
  feather.replace() 
}())  // it is IIFE (Immediately Invoked Function Expression) - it is called immediately after definition because of the () at the end


// Function that accepts a string and copies it to the clipboard:
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
}

// Activate the tooltips (hints when hovering over elements):
var tooltipTriggerList = [].slice.call($('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
var emailTooltip = tooltipList[0]


// Function that accepts a string and writes it to the emailTooltip:
function writeToTooltip(text) {
  // Note: a hacky solution:
  $("#navbar-email").attr("title", text)
  $("#navbar-email").attr("data-bs-original-title", text)
  emailTooltip._getTipElement().innerText = text

  // If mouse is hovering over $("#navbar-email"):
  if ($("#navbar-email").is(":hover")) {
    emailTooltip.show()
  }
}


// Function that is called when the user clicks on the email:
function whenClickedOnEmail() {
  copyToClipboard($("#navbar-email").text())
  
  // Write "Copied!" it to the emailTooltip:
  writeToTooltip("Copied!")
  // disable the click event listener on the $("#navbar-email"):
  $("#navbar-email").off("click")
  
  // Wait for 2 seconds, them write "Click to copy" to the emailTooltip:
  setTimeout(() => {
    writeToTooltip("Click to copy")
    // enable the click event listener on the $("#navbar-email") again:
    $("#navbar-email").click(whenClickedOnEmail)
  }
  , 2000)
}

// Add the onclick event listener to the $("#navbar-email"):
$("#navbar-email").click(whenClickedOnEmail)





