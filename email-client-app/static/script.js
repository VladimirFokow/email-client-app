
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


// Add the onclick event listener to the $("#navbar-email"):
$("#navbar-email").click(function() {
  copyToClipboard($("#navbar-email").text())
  
  // Write "Copied!" it to the emailTooltip:
  writeToTooltip("Copied!")
  
  // Wait for 2 seconds, and write "Click to copy" to the emailTooltip:
  setTimeout(function() {
    writeToTooltip("Click to copy")
  }
  , 2000)
})


