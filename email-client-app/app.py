from flask import (Flask, render_template, redirect, url_for, flash, jsonify,
                   request, session)
from flask_session import Session
from secrets import token_hex
from imap_tools import (MailBox, MailMessage, MailMessageFlags,
                        MailboxFolderCreateError)
import flask_mail  # flask_mail.Mail, flask_mail.Message, flask_mail.Attachment
from util.database import get_models
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from util.configs import SMPT_CONFIGS, IMAP_CONFIGS
from util.forms import LoginForm
from util.actions import (get_user_folders,
                          client_to_server_folder_name, 
                          are_credentials_valid)


app = Flask(__name__)
# Session:
app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_PERMANENT'] = False  # TODO: does this influence the browser-wide session? test it
# Database:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to prevent warning about future changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
# WTForms needs a secret key (to protect against CSRF):
app.config['SECRET_KEY'] = token_hex(16)


db, Email, Folder, Attachment, User = get_models(app)
Session(app)


@app.route('/query_the_server', methods=['POST'])
def query_the_server():
    """ 
    Query the email server, also updating the local database (if needed).

    This function is executed by AJAX requests, with the required argument:
    - command

    Additional required arguments, depending on the command:
    - folder
    - uid
    - recipient, subject, body, attachments
    """
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    command = request.form['command']
    with MailBox(host=host, port=port).login(email, password) as mailbox:
        if command == 'get_folders_and_n_messages':
            folder = request.form['folder']
            return get_folders_and_n_messages(mailbox, folder)
        elif command == 'create_folder':
            folder = request.form['folder']
            return create_folder(mailbox, folder)
        elif command == 'move_to':
            uid = request.form['uid']
            folder = request.form['folder']
            return move_to(mailbox, uid, folder)
        elif command == 'save_draft':
            recipient = request.form['recipient']
            subject = request.form['subject']
            body = request.form['body']
            attachments = []
            # for file in files:
            #     with app.open_resource("logo.png") as fp:
            #         attachments.append(flask_mail.Attachment(
            #             filename="logo.png", content_type="logo/png", data=fp.read()
            #         ))  # (content_type is mimetype)
            smtp_msg = create_smtp_msg(recipient, subject, body, attachments)
            return save_to_drafts(mailbox, email_provider, )


# These functions are used by the AJAX function above:
# (they all also update the local database if needed)

def create_folder(mailbox, folder):
    # To the server:
    try:
        mailbox.folder.create(folder)
    except MailboxFolderCreateError as e:
        # could not create folder on the server
        return jsonify({'success': False, 'error': str(e)})

    # To the local database:
    try:
        folder = Folder(name=folder)
        db.session.add(folder)
        db.session.commit()
    except (DataError, IntegrityError) as e:
        # DataError - if folder already exists
        # IntegrityError - if folder name is too long
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': True})


def get_folders_and_n_messages(mailbox, folder, n=10):

    # Email of the owner of the account:
    owner_email = session['email']
    owner = db.session.execute(db.select(User).where(User.username == owner_email)).scalar_one()
    if not owner:
        return jsonify({'success': False, 'error': 'User not found in database'})

    # Fetch all owner's folders from the server
    user_folders = get_user_folders(mailbox)  # list of user folder names

    # .. and add them to the local database:
    for folder_name in user_folders:
        folder_object = Folder(name=folder_name, owner=owner)
        db.session.add(folder_object)

    # Fetch n owner's emails from the server:
    server_folder = client_to_server_folder_name(folder, mailbox)
    mailbox.folder.set(server_folder)
    messages = list(mailbox.fetch(limit=n, bulk=True, reverse=True))

    # .. and add them to the local database:
    msg_infos = []
    for msg in messages:
        # Prepare the message info (to be returned):
        msg_info = {
            'uid': msg.uid,
            'date': msg.date.isoformat(),
            'from_': msg.from_,
            'to': msg.to[0],
            'subject': msg.subject,
            'text': msg.text,
        }
        msg_infos.append(msg_info)

        # If message is not in database - add it:
        # filter by the owner as well
        email_exists = db.session.execute(db.select(Email).where(Email.uid == msg.uid).where(Email.owner == owner)).first()
        if not email_exists:
            email = Email(owner=owner, **msg_info)
            email.date = msg.date  # datetime, not string
            db.session.add(email)

            # # TODO: process attachments
            # for att in msg.attachments:
            #     path = f'C:/1/{att.filename}'
            #     # Save_to_disk:
            #     with open(path, 'wb') as f:
            #         f.write(att.payload)
            #     attachment = Attachment(filename=att.filename, 
            #                             content_type=att.content_type, 
            #                             path=path, 
            #                             email=email)  # TODO: can I add like this? or do I need to add the email_id?
            #     db.session.add(attachment)
    
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
    
    # Return owner's emails and folders:
    data = {'user_folders': user_folders, 'msg_infos': msg_infos}
    return jsonify({'success': True, 'data': data})


def move_to(mailbox, uid, folder):
    server_folder = client_to_server_folder_name(folder, mailbox)
    mailbox.move([uid], server_folder)


def save_to_drafts(mailbox, smtp_msg):
    server_folder = client_to_server_folder_name('drafts', mailbox)
    mailbox.append(smtp_msg, server_folder, dt=None, flag_set=[MailMessageFlags.DRAFT])
    # TODO: also save to the filesystem and database
    # TODO: also save attachments


### Other functions

# # Query only the database
# @app.route('/query_db', methods=['POST'])
# def query_db():
#     ...


# Flask-Mail (smtp) to imap_tools (imap)
def smpt_to_imap_type(smtp_msg):
    """ 
    Converts a `Flask-Mail` message to an `imap_tools` message 
    (need in imap_tools to save email to drafts)
    """
    pass
    # imap_msg = MailMessage()
    # imap_msg.message_id = smtp_msg.message_id
    # imap_msg.subject = smtp_msg.subject
    # imap_msg.date = smtp_msg.date
    # imap_msg.text = smtp_msg.body
    # imap_msg.html = smtp_msg.html
    # imap_msg.attachments = smtp_msg.attachments
    # return imap_msg


def create_smtp_msg(recipient, subject, body, attachments):
    """ 
    Receives input fields needed for the email, and creates it 
    using `Flask-Mail`: smtp (for sending).
    """
    msg = flask_mail.Message()
    msg.subject = subject
    msg.recipients = [recipient]
    msg.body = body
    msg.attachments = attachments
    return msg


# Must be run with app context:
def send(msg):
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    app.config.update(SMPT_CONFIGS[email_provider])
    user_config = {"MAIL_DEFAULT_SENDER": email,
                   "MAIL_USERNAME": email,
                   "MAIL_PASSWORD": password}
    app.config.update(user_config)
    mail = flask_mail.Mail(app)
    mail.send(msg)












### Routes:

@app.route('/')
def index():
    return redirect(url_for('mailbox'))



@app.route('/mailbox', methods=['GET', 'POST'])
def mailbox():
    if not session.get('logged in'):
        return redirect(url_for('login'))
    return render_template('mailbox.html', title='Mailbox')


# # This is the old implementation 
# @app.route('/<folder>/', methods=['GET', 'POST'])
# @app.route('/<folder>/<uuid>', methods=['GET', 'POST'])
# def access_folder(folder, uuid=None):
#     if not session.get('logged in'):
#         return redirect(url_for('login'))
#     # from urllib.parse import unquote_plus  # to convert variables from url-format to normal
#     current_folder = unquote_plus(folder)
#     email = session.get('email')
#     password = session.get('password')
#     email_provider = email.split('@')[-1]
#     host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
#     port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
#     try:
#         with MailBox(host=host, port=port).login(email, password) as mailbox:
#             print('--- Logging in to the server')
#             # Get the folder names on the server:
#             server_folders = mailbox.folder.list()
#             folder_mapping = create_folder_mapping(email_provider, server_folders)
#             user_folders = [folder for folder in folder_mapping if folder not in DEFAULT_FOLDERS]
#             if current_folder not in DEFAULT_FOLDERS + user_folders:
#                 return redirect(url_for('access_folder', folder='inbox', uuid=uuid))

#             # Render the latest N emails in the current folder 
#             # (not to overload our app with ALL the emails)
#             N = 10
#             mailbox.folder.set(folder_mapping[current_folder])
#             msgs = list(mailbox.fetch(limit=N, reverse=True, bulk=True))
#             # return current_folder, folder_mapping, jsonify(msgs)
#             # TODO: show folders and messages in selected folder


#         # if uuid not in emails_of_folder, then uuid = uuid of the first email_of_folder.
#         # if 0 emails_of_folder, this is a special case: the pages will be empty, and need a message.
#         #     # how to select an email? /folder/uuid ?
#         # opened_email = ... find email by uuid. Else None.
        
#         return render_template('access_folder.html', 
#                             title='Email Client',
#                             user_folders=user_folders,
#                             folder=folder,
#                             uuid=uuid,
#                             #    emails_of_folder=emails_of_folder,  # json
#                             #    opened_email=opened_email,  # json
#                             )
        
#     except MailboxLoginError:
#         return redirect(url_for('login'))
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged in'):
        return redirect(url_for('index'))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        # If the form was submitted with data in the correct format:
        email = login_form.email.data
        password = login_form.password.data
        if not are_credentials_valid(email, password):
            flash('Sorry, invalid email or password 😕', category='danger')
            return redirect(url_for('login'))
        # Save valid credentials to session:
        session['email'] = email
        session['password'] = password
        session['logged in'] = True

        # If the user in the database doesn't exist:
        # - create the user
        user = db.session.execute(db.select(User).where(User.username == email)).first()
        if not user:
            user = User(username=email)
            db.session.add(user)
            db.session.commit()
        # TODO:
        # - create the user's default folders: inbox, sent, drafts, trash
        # - fetch all the users emails and folders from the server, and save them also to the database

        return redirect(url_for('index'))
    
    return render_template('login.html', title='Log in', form=login_form)


@app.route('/logout')
def logout():
    session['email'] = None
    session['password'] = None
    session['logged in'] = False
    return redirect(url_for('login'))









# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 
# Optional TODOs:

# relationship 1-to-Many, not m-n

# can organize into a package (not as a module)

# add Check Constraint on email fields: nullable=False if not a draft
# https://dba.stackexchange.com/questions/42469/constraints-based-on-other-columns

# and for importance level for email (from 1 to 5):
# CREATE TABLE YourSchema.YourTable(YourColumn INT NOT NULL CONSTRAINT CHK_YourTable_YourColumn_ValidLimits
# CHECK(YourColumn BETWEEN 1 AND 5),
# SomeOtherColumns VARCHAR(10)
# );



# Insert this into the log-in form: 

# Due to security reasons, email providers do not allow to use your main email 
# password to log into your account with third-party email clients (like this one)
# (They are afraid that the third-party email clients won't be able to protect it from the hackers. 
# If the hackers obtained your password - they could change it and you would lose access to your account forever!). 
# So to solve this, the email providers can generate a special password for third-party apps that doesn't allow to change your main password. 
# So even if the hackers obtain this special password, they won't be able to change your main password, 
# so you will not loose access to your account.

# So to log in here: 
# enable IMAP in your main provider, and generate and use your special password. Here are the instructions: 
# # ukr.net
# https://mail.ukr.net/desktop#security/appPasswords
# https://wiki.ukr.net/ManageIMAPAccess  --  інструкція
# # gmail.com
# Sending: 
# if no 2FA set up - outdated method. If you don't have 2FA set up, set it up, and use the second approach. (outdated method: enable less secure apps, and use the main password: https://myaccount.google.com/lesssecureapps)
# if 2FA is set up - use the generated password: https://support.google.com/accounts/answer/185833

# Receiving: just ? enable IMAP (POP?), and use your normal password? can use the generated?
# Step 1: Check that IMAP is turned on: https://support.google.com/mail/answer/7126229?hl=en#zippy=%2Cstep-check-that-imap-is-turned-on
# https://mail.google.com/mail/u/0/#settings/fwdandpop
# 
# TODO: add pop support

# Note about security of your password with this email client:
# It does't export your password outside of the app.
# If you're worried, you can delete your special password right right after you are done,
# and you check the actual code of this email client on github:
# ...



# Optional TODO: after taking the login email address from the form - str.lower()


