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
// Main page logic:
// - update page contents
// - get info from the db, and then from the server using AJAX


// Helper functions:

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
 * Returns the corrected path if the current one is not full / is incorrect.
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
 * --- Default values: ---
 * <folder>:    inbox
 * <page>:      p0
 * <mode>:      show
 * "the rest":  ""
 * 
 * @return {string} corrected_path
 */
function get_corrected_path() {
  let [folder, page, mode, part3, part4] = get_path_parts()

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
  // depending on the mode:
  if (mode === 'show') {
    let uid = part3
    if (!uid) {
      return '#' + folder + '/' + page + '/show'
    } else {
      return '#' + folder + '/' + page + '/show/' + uid
    }
  } else if (mode === 'write') {
    let draft = part3
    let uid = part4
    if (draft !== 'draft' || !uid) {
      return '#' + folder + '/' + page + '/write'
    } else {
      return '#' + folder + '/' + page + '/write/draft/' + uid
    }
  }
}


// Returns all parts as a list (if don't exist, they are null)
//  --- Correct path formats: ---
// #<folder>/<page>/show
// #<folder>/<page>/show/<uid>
// #<folder>/<page>/write
// #<folder>/<page>/write/draft/<uid>
function get_path_parts() {
  path = window.location.hash  // e.g. #inbox/p1/show/1
  if (path) {
    path = path.substring(1)  // remove hash (#)
  }
  let parts = path.split( '/' );
  let folder = parts[0]
  if (folder == '') {
    folder = null
  }
  let page = get_or_null(parts, 1)
  let mode = get_or_null(parts, 2)
  let part3 = get_or_null(parts, 3)
  let part4 = get_or_null(parts, 4)
  return [folder, page, mode, part3, part4]
}


// Returns an html component for just an empty main page, saying
// "Select an email or write a new one" 
// in the middle of the page (centered horizontally AND vertically - by the whole height of the page)
// in middle font and muted colors:
function empty_main_page() {
  let container = document.createElement('div')
  container.classList.add('d-flex', 'justify-content-center', 'align-items-center', 'h-100', 'opacity-50')
  let text = document.createElement('h3')
  text.classList.add('text-muted')
  text.innerText = 'Select an email or create a new one'
  container.appendChild(text)
  return container
}

// Returns an html component for the "write email" page:

function empty_email_writing_page() {
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
  save.onclick = save_draft

  form.appendChild(to)
  form.appendChild(subject)
  form.appendChild(text)
  form.appendChild(attach_container)
  form.appendChild(send)
  form.appendChild(save)

  container.appendChild(form)
  return container
}


// Class for an Email Message:
class Message {
  constructor(uid, date, from_, to, subject, text) {
    this.uid = uid
    this.date = date
    this.from_ = from_
    this.to = to
    this.subject = subject
    this.text = text
  }


  // Alternative constructor - from an imap message
  // (the imap message is a json object - response from the POST request).
  // Usage: let msg = Message.from_json(json_msg)
  static from_json(json_msg) {
    let uid = json_msg.uid
    let date = new Date(json_msg.date)
    let from_ = json_msg.from_
    let to = json_msg.to
    let subject = json_msg.subject
    let text = json_msg.text
    return new Message(uid, date, from_, to, subject, text)
  }


  // Returns an html element – an email-message-list-item:
  create_msg_list_item() {
    let uid = this.uid
    let date = new Date(this.date)
    let subject = this.subject
    let text = this.text
    let msg = this
  
    let a = document.createElement('a')
    let [folder, page, mode, part3, part4] = get_path_parts()
    // If we are on a draft url - meaning this message is a draft:
    if (part3 == 'draft') {
      a.href = '#' + folder + '/' + page + '/write/draft/' + uid
    } else {
      a.href = '#' + folder + '/' + page + '/show/' + uid  
    }
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
  
    a.onclick = function() {
      // Remove the "active" class from all message-list-items:
      $(".message-list-item").removeClass("active")
      // Add the "active" class to the current (clicked) message-list-item:
      $(this).addClass("active")
      // Render this email message instance in the main section
      msg.render_in_main_section()  // why doesn't this render the message?
    }

    return a
  }


  // A function that renders the message in the main section of the page:
  render_in_main_section() {
    let container

    // Constituent parts of the path in the current url:
    let [folder, page, mode, part3, part4] = get_path_parts()
    // If we are on a draft url - meaning this message is a draft:
    if (part3 == 'draft') {
      // Create a writing page with draft details filled in
      container = empty_email_writing_page()
      container.querySelector('#write_to').value = this.to
      container.querySelector('#write_subject').value = this.subject
      container.querySelector('#write_text').value = this.text
    
    } else {
      // Create a container with this message for viewing
      container = document.createElement('div')
      container.classList.add('pt-3', 'pb-4')

      let info1 = document.createElement('div')
      info1.classList.add('mt-2', 'd-flex', 'flex-nowrap', 'justify-content-between')

      let p1 = document.createElement('p')
      p1.classList.add('line-clamp-1')
      p1.innerHTML = 'From: ' + '<span class="text-muted">' + this.from_ + '</span>'
      let small = document.createElement('small')
      small.innerText = this.date.toLocaleDateString()
      info1.appendChild(p1)
      info1.appendChild(small)
      
      let info2 = document.createElement('div')
      info2.classList.add('border-bottom')
      let p2 = document.createElement('p')
      p2.innerHTML = 'To: ' + '<span class="text-muted">' + this.to + '</span>'
      let h3 = document.createElement('h3')
      h3.innerText = this.subject
      info2.appendChild(p2)
      info2.appendChild(h3)

      let email_text = document.createElement('div')
      email_text.classList.add('pt-4')
      email_text.innerText = this.text
      
      container.appendChild(info1)
      container.appendChild(info2)
      container.appendChild(email_text)
    }

    // Render this message (set the contents of $("main")):
    $("main").html(container)
  }
}


// Class for all the messages in all the folders (which are currently in memory):
class EmailStore {
  constructor() {
    // this.emails will be { <folder_name> : {<uid> : <Message>} }
    this.emails = {
      'inbox': {},
      'sent': {},
      'drafts': {},
      'bin': {},
      // ... all the user folders
    };
  }
  
  getEmails(folderfolder=null) {
    if (folder) {
      return this.emails[folder];
    }
    return this.emails;
  }
  addEmails(newEmails) {
    this.emails = newEmails;
  }

  getEmail(folder, uid) {
    return this.emails[folder][uid];
  }
  addEmail(folder, uid, msg) {
    this.emails[folder][uid] = msg;
  }

  deleteEmail(folder, uid) {
    delete this.emails[folder][uid];
  }
  moveEmail(folder, uid, newFolder) {
    let msg = this.getEmail(folder, uid);
    this.addEmail(newFolder, uid, msg);
    this.deleteEmail(folder, uid);
  }

  getAllFolders() {
    return Object.keys(this.emails);
  }
  getUserFolders() {
    let all_folders = this.getAllFolders();
    let user_folders = all_folders.filter(folder => !['inbox', 'sent', 'drafts', 'bin'].includes(folder));
    return user_folders;  // ['folder1', 'folder2', ...]
  }

  replaceAll(newEmails) {
    this.emails = newEmails;
  }
  replaceAllFromJson(jsonEmails) {
    // `jsonEmails` is a dictionary in the following format:
    // { <folder_name> : {<uid> : <json_msg>} }
    // Convert the json messages to Message objects:
    let newEmails = {};
    for (let folder in jsonEmails) {
      newEmails[folder] = {};
      for (let uid in jsonEmails[folder]) {
        let json_msg = jsonEmails[folder][uid];
        newEmails[folder][uid] = Message.from_json(json_msg);
      }
    }
    this.replaceAll(newEmails);
  }
  getSortedByDate(folder) {
    // Returns the messages in `folder` sorted by date (newest first)
    let msgs = Object.values(this.emails[folder]);
    msgs.sort((a, b) => b.date - a.date);
    return msgs;  // array of Message objects
  }

  folderExists(folder_name) {
    return this.emails.hasOwnProperty(folder_name);
  }
  createFolder(folder_name) {
    this.emails[folder_name] = {};
  }
}
const emailStore = new EmailStore();  // global singleton



// ---------------------------
// Render all user folders:


function render_user_folders() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  let user_folders = emailStore.getUserFolders()

  let html = ''
  if (user_folders.length > 0) {
    html = '<ul class="nav flex-column mb-2">'
    for (let user_folder of user_folders) {
      html += '<li class="nav-item text-nowrap">'

      let a = document.createElement('a')
      a.classList.add('nav-link', 'folder')
      if (folder === user_folder) {
        a.classList.add('active')  // to highlight the current folder
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


  // Also add them to the modal list:
  let folder_list = document.createElement('div')
  user_folders.unshift('inbox')  // add 'inbox' as the first element of user_folders:
  for (let user_folder of user_folders) {
    let button = document.createElement('button')
    button.classList.add('list-group-item', 'list-group-item-action', 'submit-move-to')
    if (folder === user_folder) {
      button.classList.add('disabled')
    }
    button.dataset.bsDismiss = 'modal'
    button.dataset.newFolder = user_folder
    button.onclick = submit_move_to
    button.innerText = user_folder
    folder_list.appendChild(button)
  }
  $('#move-to-folder-folders').html(folder_list)
}


// Renders the list of email messages of the current folder:

function render_msg_list() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  let messages = emailStore.getSortedByDate(folder)
  let msg_list = $('#msg-list')[0]
  msg_list.innerHTML = ''  // clear the list

  // The number of messages:
  let n_msgs = messages.length
  let n_msgs_element = document.createElement('p')
  n_msgs_element.classList.add('text-muted', 'small', 'px-3', 'mb-1', 'pt-0')
  n_msgs_element.innerText = n_msgs + ' messages'
  msg_list.appendChild(n_msgs_element)

  // The messages themselves:
  for (let i = 0; i < n_msgs; i++) {
    msg_list.appendChild(messages[i].create_msg_list_item())
    if (i < n_msgs - 1) {
      let horizontal_divider = document.createElement('div')
      horizontal_divider.classList.add('horizontal-divider')
      msg_list.appendChild(horizontal_divider)
    }
  }
}



// ---------------------------
// Button actions:



function save_email_to(folder='drafts', to='', subject='', text='', attachments=[]) {
  // Create and save email to the folder "folder" on the server and on the client:
  $.post(
    "/query_the_server",
    {
      command: 'save_email',
      save_folder: folder,
      to: to,
      subject: subject,
      text: text,
      // attachments: attachments  // TODO
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully saved email to the server folder: ' + folder)
        // Save the draft to the client:

        // Note: the response is not returned by the send method, so we do not
        // have the full information here about all the fields of the newly 
        // sent email (like date, uid)
        // TODO: fix this - fetch the email from the server and add it to the 
        // client not waiting for the manual refresh when the folder changes?
        let uid = data.uid
        date = null
        from_ = null
        let msg = Message(uid, date, from_, to, subject, text)
        emailStore.addEmail(folder, uid, msg)
        // go to #<folder>/<page>/write/draft/<uid>
        // window.location.hash = '#' + folder + '/' + page + '/write/draft/' + uid
      } else {
        console.log('error saving the email to folder: ' + folder + " : " + data.error)
      }
    }
  );
}


// When the "send email" button is clicked:

function send_email() {
  let to = $("#write_to").val()
  let subject = $("#write_subject").val()
  let text = $("#write_text").val()
  let attachments = []  // TODO
  $("main").html(empty_main_page())  // clear the main page
  
  // Send the email:
  $.post(
    "/query_the_server",
    {
      command: 'send_email',
      to: to,
      subject: subject,
      text: text,
      // attachments: attachments  // TODO
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully sent email')
        save_email_to('sent', to, subject, text, attachments)
      } else {
        console.log('error sending email: ' + data.error)
      }
    }
  );
}


// When the "save draft" button is clicked:

function save_draft() {
  let to = $("#write_to").val()
  let subject = $("#write_subject").val()
  let text = $("#write_text").val()
  let attachments = []  // TODO
  $("main").html(empty_main_page())  // clear the main page
  // replace write to show in the url:
  let [folder, page, mode, part3, part4] = get_path_parts()
  window.location.hash = '#' + folder + '/' + page + '/show'
  // Save the draft:
  save_email_to('drafts', to, subject, text, attachments)
}


// Button "create new email":
$("#create").click(function() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  window.location.hash = '#' + folder + '/' + page + '/write'
})


// Button "bin":
$("#move-to-bin").click(function() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  if (mode != 'show' || part3 == null) {
    return
  }
  uid = part3

  $.post(
    "/query_the_server",
    {
      command: 'move_to_bin',
      folder: folder,
      uid: uid
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully moved the message to bin')
        // Delete from the client:
        emailStore.moveEmail(folder, uid, 'bin')
        $("main").html(empty_main_page())  // clear the main page
        render_msg_list()
      } else {
        console.log('error moving an email to bin: ' + data.error)
      }
    }
  );
})


// Button "delete":
$("#delete").click(function() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  if (mode != 'show' || part3 == null) {
    return
  }
  uid = part3

  $.post(
    "/query_the_server",
    {
      command: 'delete',
      folder: folder,
      uid: uid
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully deleted the message from the server')
        // Delete from the client:
        emailStore.deleteEmail(folder, uid)
        $("main").html(empty_main_page())  // clear the main page
        render_msg_list()
      } else {
        console.log('error moving an email deleting an email: ' + data.error)
      }
    }
  );
})


// Button "move" (to show the selection of folders for the user to choose):
$("#move").click(function() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  if (mode != 'show' || part3 == null) {
    return
  }  
})


// A function which will be fired when a 'submit-move-to' button clicked
// (to submit the move to another folder):
function submit_move_to() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  let uid = part3
  let new_folder = this.dataset.newFolder

  $.post(
    "/query_the_server",
    {
      command: 'move_to',
      folder: folder,
      uid: uid,
      new_folder: new_folder
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully moved the email to folder: ' + new_folder)
        // Delete from the client:
        emailStore.deleteEmail(folder, uid)
        $("main").html(empty_main_page())  // clear the main page
      } else {
        console.log('error moving an email: ' + data.error)
      }
    }
  );
}


// Listener for the "create new folder" input name when typing:
$("#input-new-folder-name").keyup(function() {
  let folder_name = $("#input-new-folder-name").val()
  let error_field = $("#new-folder-name-error-message")
  let submit_button = $("#submit-create-new-folder")
  
  if (!folder_name.trim()) {
    // if folder name is empty - show the error message:
    error_field.html("Folder name cannot be empty")
    submit_button.prop("disabled", true)
    return
  }
  if (emailStore.folderExists(folder_name)) {
    // if folder name already exists - show the error message:
    error_field.html("Folder \"" + folder_name + "\" already exists")
    submit_button.prop("disabled", true)
    return
  }
  error_field.html("")
  submit_button.prop("disabled", false)
});


// Button to submit the creation of a new folder:
$("#submit-create-new-folder").click(function() {
  let folder_name = $("#input-new-folder-name").val()
  // Create the folder:
  $.post(
    "/query_the_server",
    {
      command: 'create_folder',
      folder: folder_name
    },
    function(data, status) {
      if (data.success) {
        console.log('successfully created folder: ' + folder_name + ' on the server')
        // Create the folder on the client:
        emailStore.createFolder(folder_name)
        // Render the new folder:
        render_user_folders()
        // clear the input field:
        $("#input-new-folder-name").val("")
        // Close the modal:
        hideCreateNewFolderModal()
      } else {
        console.log('error creating a folder: ' + folder_name + '. Error: ' + data.error)
      }
    }
  );
})



// ---------------------------
// Whole page rendering:

// On the hash change of the url: render the page contents
// - folders and the message list if mode=='show',
// - and also the writing area if mode=='write':      TODO- as well. 

function update_page_content() {
  let [folder, page, mode, part3, part4] = get_path_parts()
  
  if (mode == 'show') {
    let uid = part3
    if (uid) {  // Do not make a request to the server, if a message is selected.
      // Note: this is a temporary measure. 
      // But in the future (after refactoring) there will be even less server requests.
      return
    }

    render_msg_list()  // render the message list

    // AJAX request:
    $.post(
      "/query_the_server",
      {
        command: 'get_emails',
        // folder: folder,
        // page: page  // TODO: add support for pagination
      },

      function(data, status) {
        if (data.success) {
          emailStore.replaceAllFromJson(data.email_messages)
          render_user_folders()
          render_msg_list()
        } else {
          console.log('error getting emails: ' + data.error)
        }
      }
    );
  } 

  else if (mode == 'write') {
    // Display a new page with forms for writing a new email:
    let draft = part3
    let uid = part4
    if (draft !== 'draft' || !uid) {
      $("main").html(empty_email_writing_page())  // new page with empty fields
    
    } else {
      // Page with the draft contents filled in:
      let draft = emailStore.getEmail('drafts', uid)
      draft.render_in_main_section()
    }
    activate_feather_icons()
  }
}


// If the active folder should be one of the default ones, set it as active:

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


// Change the url if needed, and render the whole page:

function render_page() {
  // Update the page hash and page content:
  let path = window.location.hash  // e.g. "#inbox/"
  let corrected_path = get_corrected_path()  // e.g. "#inbox/p0/show/123"
  if (path != corrected_path) {   // need to change the path:
    window.location.hash = corrected_path  // set the corrected path
  } else {
    set_default_folder_active()  // if it's the default folder, make it active
    update_page_content()  // render the actual page content
  }
}


window.onload = function() {
  $("main").html(empty_main_page())
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
  }
}
add_listeners_to_all_folders();


// ---------------------------------------------------------------------
// Modal autofocus:

const createNewFolderModal = document.getElementById('create-new-folder-modal')
const inputNewFolderName = document.getElementById('input-new-folder-name')

createNewFolderModal.addEventListener('shown.bs.modal', () => {
  inputNewFolderName.focus()
})


// ---------------------------------------------------------------------
// 

