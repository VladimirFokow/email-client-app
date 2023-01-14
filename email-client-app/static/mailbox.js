// ---------------------------------------------------------------------

// Activate feather icons:
function activate_feather_icons() {
  'use strict'  // "strict mode" - can't use undeclared variables
  feather.replace() 
}
activate_feather_icons()


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


function render_user_folders(user_folders, folder) {
  // TODO: when rendering the user folders, their active class disappears if not added here (is there a better way to do this? e.g. from database)
  // TODO: rendering user folders takes too much time, if not taked from the database
  let html = ''
  if (user_folders.length > 0) {
    html = '<ul class="nav flex-column mb-2">'
    for (let user_folder of user_folders) {
      html += '<li class="nav-item text-nowrap">'

      let a = document.createElement('a')
      a.classList.add('nav-link', 'folder')
      if (folder === user_folder) {
        a.classList.add('active')
      }
      a.href = '#' + user_folder + '/'
      a.innerHTML = '<span data-feather="folder"></span> ' + user_folder

      html += a.outerHTML
      html += '</li>'
    }
    html += '</ul>'
  } else {
    html = '<p class="text-muted small-message">You have no folders.</p>'
  }
  $("#user-folders").html(html)
  activate_feather_icons()
  add_listeners_to_all_folders()
}


function create_render_msg_func(msg) {
  // When an email message is selected - this function will be called:
  // (for each email message - a unique function)
  function render_msg() {
    // Add the "active" class to the selected message, and remove it from the others:
    $(".message-list-item").removeClass("active")
    $(this).addClass("active")

    // Render the message (set the contents of $("main")):
    let uid = msg.uid
    let date = new Date(msg.date)
    let from_ = msg.from_
    let to = msg.to
    let subject = msg.subject
    let text = msg.text

    let container = document.createElement('div')
    container.classList.add('pt-3', 'pb-4')

    let info1 = document.createElement('div')
    info1.classList.add('mt-2', 'd-flex', 'flex-nowrap', 'justify-content-between')

    let p1 = document.createElement('p')
    p1.classList.add('line-clamp-1')
    p1.innerHTML = 'From: ' + '<span class="text-muted">' + from_ + '</span>'
    let small = document.createElement('small')
    small.innerText = date.toLocaleDateString()
    info1.appendChild(p1)
    info1.appendChild(small)
    
    let info2 = document.createElement('div')
    info2.classList.add('border-bottom')
    let p2 = document.createElement('p')
    p2.innerHTML = 'To: ' + '<span class="text-muted">' + to + '</span>'
    let h3 = document.createElement('h3')
    h3.innerText = subject
    info2.appendChild(p2)
    info2.appendChild(h3)

    let email_text = document.createElement('div')
    email_text.classList.add('pt-4')
    email_text.innerText = text
    
    container.appendChild(info1)
    container.appendChild(info2)
    container.appendChild(email_text)

    $("main").html(container)
  }
  return render_msg
}


function create_msg_list_item(msg, folder, page) {
  let uid = msg.uid
  let date = new Date(msg.date)
  let subject = msg.subject
  let text = msg.text

  let a = document.createElement('a')
  a.href = '#' + folder + '/' + page + '/show/' + uid  
  a.classList.add('message-list-item', 'list-group-item', 'list-group-item-action', 'py-2', 'lh-sm')
  // list-group-item: make the element a list-group-item.
  // list-group-item-action: necessary for it to be clickable.
  // py-2: padding to top and bottom of 0.5rem each.
  // lh-sm: line-height small (interval between the lines).
  let a_inner = ''
  a_inner += '<div class="d-flex w-100 align-items-center justify-content-between">'
  a_inner += '  <strong class="col-9 mb-1 line-clamp-1">' + subject + '</strong>'
  a_inner += '  <small>' + date.toLocaleDateString().replace(/\//g, '.') + '</small>'
  a_inner += '</div>'
  a_inner += '<div class="mb-1 small line-clamp-2">' + text + '</div>'
  a.innerHTML = a_inner

  render_msg = create_render_msg_func(msg)
  a.onclick = render_msg
  return a
}


function render_msg_list(msg_infos, folder, page) {
  let msg_list = $('#msg-list')[0]
  msg_list.innerHTML = ''

  // Add number of messages:
  let n_msgs = msg_infos.length
  let info_n_msgs = document.createElement('p')
  info_n_msgs.classList.add('text-muted', 'small', 'px-3', 'mb-1', 'pt-0')
  info_n_msgs.innerText = n_msgs + ' messages'
  msg_list.appendChild(info_n_msgs)

  // Add messages themselves:
  for (let i = 0; i < n_msgs; i++) {
    msg_list.appendChild(create_msg_list_item(msg_infos[i], folder, page))
    if (i < n_msgs - 1) {
      let horizontal_divider = document.createElement('div')
      horizontal_divider.classList.add('horizontal-divider')
      msg_list.appendChild(horizontal_divider)
    }
  }
}


// When send email button is clicked:
function send_email() {
  let to = $("#write_to").val()
  let subject = $("#write_subject").val()
  let text = $("#write_text").val()
  $.post(
    "/send_email",
    {
      to: to,
      subject: subject,
      text: text,
      // attachments: attachments  // TODO
    },
    function(data, status) {
      if (!data.success) {
        console.log('error: ' + data.error)
      } else {
        console.log('success')
      }
    }
  );
}



// When save draft button is clicked:
function save_draft() {
  let to = $("#write_to").val()
  let subject = $("#write_subject").val()
  let text = $("#write_text").val()
  $.post(
    "/save_draft",
    {
      to: to,
      subject: subject,
      text: text,
      // attachments: attachments  // TODO
    },
    function(data, status) {
      if (!data.success) {
        console.log('error: ' + data.error)
      } else {
        console.log('success')
      }
    }
  );
}


function empty_email_write_page() {
  // A new empty element with forms to write an email:
  let container = document.createElement('div')
  container.classList.add('pt-3', 'pb-4')

  // `container` will have such forms to enter data:
  // To
  // Subject
  // Text
  // Add attachments
  // Send button
  // Save draft button

  let form = document.createElement('form')
  form.classList.add('pt-2')

  // To: id="write_to"
  let to = document.createElement('div')
  to.classList.add('form-group', 'mb-3')
  let to_label = document.createElement('label')
  to_label.setAttribute('for', 'write_to')
  to_label.innerText = 'To:'
  let to_input = document.createElement('input')
  to_input.classList.add('form-control', 'mt-1')
  to_input.setAttribute('type', 'text')
  to_input.setAttribute('id', 'write_to')
  to_input.setAttribute('placeholder', 'Enter email')
  to.appendChild(to_label)
  to.appendChild(to_input)

  // Subject: id="write_subject"
  let subject = document.createElement('div')
  subject.classList.add('form-group', 'mb-3')
  let subject_label = document.createElement('label')
  subject_label.setAttribute('for', 'write_subject')
  subject_label.innerText = 'Subject:'
  let subject_input = document.createElement('input')
  subject_input.classList.add('form-control', 'mt-1')
  subject_input.setAttribute('type', 'text')
  subject_input.setAttribute('id', 'write_subject')
  subject_input.setAttribute('placeholder', 'Enter subject')
  subject.appendChild(subject_label)
  subject.appendChild(subject_input)
  
  // Text: id="write_text"
  let text = document.createElement('div')
  text.classList.add('form-group', 'mb-3')
  let text_label = document.createElement('label')
  text_label.setAttribute('for', 'write_text')
  text_label.innerText = 'Text:'
  let text_input = document.createElement('textarea')
  text_input.classList.add('form-control', 'mt-1')
  text_input.setAttribute('id', 'write_text')
  text_input.setAttribute('rows', '6')
  text.appendChild(text_label)
  text.appendChild(text_input)

  // Attachments: id="attach_input"
  let attach_container = document.createElement('div')
  attach_container.classList.add('form-group', 'mb-3')
  let attach_icon = document.createElement('span')
  attach_icon.setAttribute('data-feather', 'paperclip')
  attach_icon.classList.add('me-2')
  let attach_label = document.createElement('label')
  attach_label.setAttribute('for', 'attach_input')
  attach_label.innerText = 'Attachments:'
  let attach_input = document.createElement('input')
  attach_input.setAttribute('id', 'attach_input')
  attach_input.classList.add('form-control', 'mt-1')
  attach_input.setAttribute('type', 'file')
  attach_input.setAttribute('multiple', 'multiple')
  
  // After attaching the files - the user can view their list:
  let attach_ul = document.createElement('ul')
  attach_ul.classList.add('mt-2')
  attach_ul.setAttribute('id', 'attach_ul')
  // When the user uploads files:
  attach_input.onchange = function() {
    // Remove all previous files:
    let attach_ul = $('#attach_ul')[0]
    attach_ul.innerHTML = ''
    // Render them in `attach_ul`:
    let files = attach_input.files
    let n_files = files.length
    for (let i = 0; i < n_files; i++) {
      let file_li = document.createElement('li')
      file_li.innerText = files[i].name
      attach_ul.appendChild(file_li)
    }
  }
  
  // Button to remove all the attached files:
  let delete_button = document.createElement('button')
  delete_button.classList.add('btn', 'btn-outline-danger', 'mt-2', 'py-1', 'px-2')
  delete_button.setAttribute('type', 'button')
  let delete_button_icon = document.createElement('span')
  delete_button_icon.setAttribute('data-feather', 'trash')
  delete_button_icon.classList.add('me-2')
  delete_button.append(delete_button_icon)
  delete_button.append('Remove attachments')
  delete_button.onclick = function() {
    // Remove all files:
    let attach_ul = $('#attach_ul')[0]
    attach_ul.innerHTML = ''
    // Remove all files from `attach_input`:
    let attach_input = $('#attach_input')[0]
    attach_input.value = ''
    }

  attach_container.appendChild(attach_icon)
  attach_container.appendChild(attach_label)
  attach_container.appendChild(attach_input)
  attach_container.appendChild(attach_ul)
  attach_container.appendChild(delete_button)

  // Send button:
  let send = document.createElement('button')
  send.classList.add('btn', 'btn-primary')
  send.setAttribute('type', 'submit')
  send.innerText = 'Send'
  send.onclick = send_email

  // Save draft button:
  let save = document.createElement('button')
  save.classList.add('btn', 'btn-secondary', 'ml-2', 'mx-3')
  save.setAttribute('type', 'button')
  save.innerText = 'Save draft'
  // save.onclick = save_draft  // TODO- save draft

  form.appendChild(to)
  form.appendChild(subject)
  form.appendChild(text)
  form.appendChild(attach_container)
  form.appendChild(send)
  form.appendChild(save)

  container.appendChild(form)
  return container
}


function render_email_write_page(draft, uid) {
  let container = empty_email_write_page()
  if (draft !== 'draft' || !uid) {
    // New page with empty fields:
    $("main").html(container)
  } else {
    // TODO- get the email from the drafts 
    // and fill in its contents in the forms of a container.
    $("main").html(container)
  }
  activate_feather_icons()
}


function update_page_content(path) {
  let parts = path.split( '/' );  // path must be already in the correct format
  let folder = parts[0].slice(1)  // remove '#' from the beginning
  let page = parts[1]
  let mode = parts[2]

  if (mode == 'show') {
    let uid = get_or_null(parts, 3)
    if (uid) {
      // Note: this is a temporary measure. 
      // But in the future (after refactoring) there will be even less server requests.
      return
    }

    $('#msg-list')[0].innerHTML = ''  // clear the msg-list
    // AJAX request:
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
          // if the user has changed the folder
          return  // don't update the page with the results of this request
        }
        if (!data.success) {
          console.log('error: ' + data.error)
        } else {
          data = data.data
          let user_folders = data.user_folders
          let msg_infos = data.msg_infos
          render_user_folders(user_folders, folder)
          render_msg_list(msg_infos, folder, page)
        }
      }
    );
  } 

  // TODO- when opening saved draft emails - their link should be '...write/draft/uid' (not '...show/uid') )
  else if (mode == 'write') {
    // Display a new page with forms for writing a new email:
    let draft = get_or_null(parts, 3)
    let uid = get_or_null(parts, 4)
    render_email_write_page(draft, uid)
  }
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
  
  if (corrected_path != path) {   // need to change the path:
    window.location.hash = corrected_path  // set the corrected path
  } else {
    update_page_content(path)  // render the actual content
  }
}


function set_default_folder_active() {
  let folder = window.location.hash.split('/')[0].slice(1)
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

window.addEventListener('hashchange', render_page)



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


// TODO (good style): 
// When loading the page - use the DATABASE for fast initial emails

// if loading the page for the first time (window.onload) - then (disregarding the future clicks between folders - even with the clicks the data must still load), query the email server and save the results to the database 100%, and update the page contents again

// Subsequently, query the server only in this case: on the button click
// Question: can we somehow listen to the incoming emails, and update page when a new email comes in? // in a pinch, can query the server just every 2 mins

// When clicking the buttons, can:
// - either use Bootstrap's  data-bs-toggle="list"  (all information will be present in the dom, just not shown)
// - or load all the data into the onclick events - so it will be stored in the javascript, and inserted on click

///
// On successful log in - maybe already send the request to the database for the data?

// when querying the server - must query for EVERYTHING! (not only new emails, but also new folders, moved emails, deleted emails, trash updates, drafts, etc.... so much... how to do it?)
        


// info not needed anymore?:
// (
// You have to escape special characters with a double backslash:
// $('#\\/about\\/')
// )




// ---------------------------------------------------------------------

// Create new email button:
$("#create").click(function() {
  let parts = window.location.hash.split('/')
  let folder = parts[0].slice(1)
  let page = parts[1]
  window.location.hash = '#' + folder + '/' + page + '/write'
})


