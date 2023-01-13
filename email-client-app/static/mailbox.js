// ---------------------------------------------------------------------

// Activate feather icons:
(function () {
  'use strict'  // "strict mode" - can't use undeclared variables
  feather.replace() 
}())
// (it is an IIFE - Immediately Invoked Function Expression. It is called 
// immediately after its definition, because of the () at the end)


// Activate tooltips (hints when hovering over an element):
var tooltipTriggerList = [].slice.call($('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
  return new bootstrap.Tooltip(tooltipTriggerEl)
})
var emailTooltip = tooltipList[0]



// ---------------------------------------------------------------------
// Click event on the email address (to copy it):


// this function copies a string to the clipboard:
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
}

// this function writes a string to the emailTooltip (to the pop-up hint):
function writeToTooltip(text) {
  // Note: this is a hacky solution
  $("#header-email").attr("title", text)
  $("#header-email").attr("data-bs-original-title", text)
  emailTooltip._getTipElement().innerText = text
  
  // If mouse is hovering over $("#header-email"):
  if ($("#header-email").is(":hover")) {
    emailTooltip.show()
  }
}

// this function is called when the user clicks on the email address:
function whenClickedOnEmail() {
  copyToClipboard($(this).text().trim())
  
  // Write "Copied!" it to the emailTooltip:
  writeToTooltip("✅ Copied!")
  // disable the click event listener on the $("#header-email"):
  $(this).off("click")
  
  // Wait for 2 seconds, then write "copy to clipboard" to the emailTooltip:
  setTimeout(() => {
    writeToTooltip("copy to clipboard")
    // enable the click event listener on the $("#header-email") again:
    $(this).click(whenClickedOnEmail)
  }
  , 2000)
}
// Note: $(this) is used not to run the DOM query every time. It will be the same as $("#header-email").

// add the onclick event listener to the $("#header-email"):
$("#header-email").click(whenClickedOnEmail)



// ---------------------------------------------------------------------
// AJAX (for updating page contents, 
// getting info from the db, and then from the server):


/**
 * Access element at index i in a list, and if index out of bounds,
 * return default value.
 * 
 * @param {Array} lst
 * @param {number} i
 * @param {any} default_value
 * @return {any} lst[i] or default_value
 */
function get_or_null(lst, i, default_value=null) {
  if (i < lst.length) {
    return lst[i]
  } else {
    return default_value
  }
}


/** 
 * Corrects the path if it is not full / correct.
 * Returns the corrected path.
 * 
 *  --- Correct path formats: ---
 * #<folder>/<page>/show
 * #<folder>/<page>/show/<uid>
 * #<folder>/<page>/write
 * #<folder>/<page>/write/draft/<uid>
 * 
 * ( <folder> will any folder, if specified )
 * ( <page> will be p<i>, where i = 0...inf )
 * ( <mode> will be "show" or "write" )
 * ( <uid> will stop at the first '/' symbol )
 * 
 * --- Fallbacks: ---
 * <folder>:    inbox
 * <page>:      p0
 * <mode>:      show
 * "the rest":  ""
 * 
 * @param {string} path
 * @return {string} corrected_path
 */
function correct_path(path) {
  let parts = path.split( '/' );
  
  let folder = parts[0].slice(1)  // remove '#' from the beginning
  let page = get_or_null(parts, 1)
  let mode = get_or_null(parts, 2)

  // if folder is not provided:
  if (!folder) {
    folder = 'inbox'
  }
  // if page is not in the format 'p'+i where i is a non-negative integer:
  if (!page || page[0] !== 'p' || !page.slice(1).match(/^[0-9]+$/)) {
    page = 'p0'
  }
  // if mode is not one of ['show', 'write']:
  if (!['show', 'write'].includes(mode)) {
    mode = 'show'
  }

  if (mode === 'show') {
    let uid = get_or_null(parts, 3)
    if (!uid) {
      return '#' + folder + '/' + page + '/show'
    } else {
      return '#' + folder + '/' + page + '/show/' + uid
    }

  } else if (mode === 'write') {
    let draft = get_or_null(parts, 3)
    let uid = get_or_null(parts, 4)
    if (draft !== 'draft' || !uid) {
      return '#' + folder + '/' + page + '/write'
    } else {
      return '#' + folder + '/' + page + '/write/draft/' + uid
    }
  }
}


function render_user_folders(user_folders) {
  // TODO: when rendering the user folders, their active class disappears if not added here (is there a better way to do this? e.g. from database)
  // TODO: rendering user folders takes too much time, if not taked from the database
  let html = ''
  let folder = window.location.hash.split('/')[0].slice(1)
  if (user_folders.length > 0) {
    html = '<ul class="nav flex-column mb-2">'
    for (let user_folder of user_folders) {
      html += '<li class="nav-item text-nowrap">'

      let a = '<a class="nav-link folder'
      if (folder === user_folder) {
        a += ' active'
      }
      a += '" '
      a += 'href="#' + user_folder + '/">'
      a += '<span data-feather="folder"></span> ' + user_folder
      a += '</a>'
      
      html += a
      html += '</li>'
    }
    html += '</ul>'
  } else {
    html = '<p class="text-muted small-message">You have no folders.</p>'
  }
  $("#user-folders").html(html)
  add_listeners_to_all_folders()
}


function render_msg_list(msg_infos) {
  let html = ''
  let parts = window.location.hash.split('/')
  let folder = parts[0].slice(1)
  let page = parts[1]
  let n_msgs = msg_infos.length
  html += '<p class="text-muted small px-3 mb-1 pt-0">' + n_msgs + ' messages</p>'
  for (let msg of msg_infos) {
    let uid = msg.uid
    let date = new Date(msg.date)
    let from_ = msg.from_
    let to = msg.to
    let subject = msg.subject
    let text = msg.text

    let a = '<a href="/mailbox#' + folder + '/' + page + '/show/' + uid + '" '
    a += 'class="list-group-item list-group-item-action py-2 lh-sm" data-bs-toggle="list">'  
    // list-group-item: make the element a list-group-item.
    // list-group-item-action: necessary for it to be clickable.
    // py-2: padding to top and bottom of 0.5rem each.
    // lh-sm: line-height small (interval between lines).
    // active: highlight the current list group item.
    // data-bs-toggle="list" automatically adds the active class to the current list group item
    a += '<div class="d-flex w-100 align-items-center justify-content-between">'
    a += '<strong class="col-9 mb-1 line-clamp-1">' + subject + '</strong>'
    a += '<small>' + date.toLocaleDateString().replace(/\//g, '.') + '</small>'
    a += '</div>'
    a += '<div class="mb-1 small line-clamp-2">' + text + '</div>'
    a += '</a>'
    html += a
    
    html += '<div class="horizontal-divider"></div>'
  }

  $("#msglist").html(html)

  // Example of resulting `html` variable:

  // <p class="text-muted small px-3 mb-1 pt-0">2 messages</p>
  // <a href="/mailbox#a/p0/show/4" class="list-group-item list-group-item-action py-2 lh-sm" data-bs-toggle="list">
  //   <div class="d-flex w-100 align-items-center justify-content-between">
  //     <strong class="col-9 mb-1 line-clamp-1">Subject 1</strong>
  //     <small>01.01.2021</small>
  //   </div>
  //   <div class="mb-1 small line-clamp-2">Text 1</div>
  // </a>
  // <div class="horizontal divider"></div>

}


function update_page_content(path) {
  let parts = path.split( '/' );  // path must be already in the correct format
  let folder = parts[0].slice(1)  // remove '#' from the beginning
  let page = parts[1]
  let mode = parts[2]

  // AJAX request:
  if (mode == 'show') { // TODO: also add support for mode == write
    let uid = get_or_null(parts, 3)
    $.post(
      "/query_the_server",
      {
        command: 'get_folders_and_n_messages',
        folder: folder,
        // page: page  // TODO: add support for pagination
      },

      function(data, status) {
        current_folder = window.location.hash.split('/')[0].slice(1)
        if (current_folder !== folder) {
          return
        }
        if (!data.success) {
          console.log('error: ' + data.error)
        } else {
          data = data.data
          let user_folders = data.user_folders
          let msg_infos = data.msg_infos
          render_user_folders(user_folders)
          render_msg_list(msg_infos)
          // render_message_content(uid)  // TODO: create this functino
        }
      }
    );
  } 
  // else if (mode == 'write') {
  //   return  // TODO: add support for mode == write
  // }
}
// Optional TODOs: 
// -
// compare with the previous path (in history),
// detect which part has changed
// and update only this part on the page
// -
// compare with the previous path (in history),
// detect which part has changed
// and update only this part on the page
// -
// in callback: write to html only if the url is still the same
// so that if the user has clicked away - not to update the new page
// -
// show an error page with some info if an error occurs in Python while handling the AJAX request
// -
// show empty page if no email selected



function render_page() {
  // Update the page hash and page content:
  let path = window.location.hash  // e.g. "#inbox/"
  let corrected_path = correct_path(path)  // e.g. "#inbox/p0/show/123"
  
  if (corrected_path != path) {
    window.location.hash = corrected_path  // set the corrected path
  } else {
    update_page_content(path)
  }
}


function set_default_folder_active() {
  folder = window.location.hash.split('/')[0].slice(1)
  if (folder === 'inbox') {
    $("#inbox").addClass("active")
  } else if (folder === 'sent') {
    $("#sent").addClass("active")
  } else if (folder === 'drafts') {
    $("#drafts").addClass("active")
  } else if (folder === 'bin') {
    $("#bin").addClass("active")
  }
}


window.onload = function() {
  set_default_folder_active()
  render_page()
}

window.addEventListener('hashchange', render_page);



// ---------------------------------------------------------------------
// Folders on click become active and remove active class from the
// previous active folder:

function become_active() {
  let previous = $(".folder.active");
  if (previous.length > 0) {
    previous[0].className = previous[0].className.replace("active", "");
  }
  this.className += " active ";
}

function add_listeners_to_all_folders() {
  // Loop through the folders and add the active class to the current/clicked folder
  let folders = $(".folder");  // all folder buttons
  for (let i = 0; i < folders.length; i++) {
    folders[i].addEventListener("click", become_active);  
    // TODO: move this activation of all folders from here to the hashchange event. 
    // If folder one of the standard ones - choose by id, else can add an id to 
    // user folders to set their active class like this: $("#folder-name").addClass("active")
  }
}
add_listeners_to_all_folders();



// ---------------------------------------------------------------------
// 



