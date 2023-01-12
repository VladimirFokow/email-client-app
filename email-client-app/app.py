from flask import (Flask, render_template, redirect, url_for, flash, jsonify,
                   request, session)
from flask_session import Session
from secrets import token_hex
from urllib.parse import unquote_plus  # to convert variables from url-format to normal
from imap_tools import MailBox, MailboxLoginError, MailMessage
from flask_mail import Mail, Message
from util.database import create_database
from util.configs import SMPT_CONFIGS, IMAP_CONFIGS, DEFAULT_FOLDERS
from util.forms import LoginForm
from util.actions import (create_folder_mapping, client_to_server_folder_name,
                          are_credentials_valid)


app = Flask(__name__)
# Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
# Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # prevent warning about future changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
# WTForms needs a secret key (to protect against CSRF)
app.config['SECRET_KEY'] = token_hex(16)


db, Email, Folder, Attachment = create_database(app)
Session(app)


@app.route('/query_the_server', methods=['POST'])
def query_the_server():
    """ 
    Query the email server.
    This function is called by AJAX requests, with these required arguments:
    - command: name of the function to do the action. Commands:
    'get_n_messages', 'create_folder', ...

    Arguments that depend on the command:
    - folder
    - uid
    - 
    """
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    command = request.form['command']
    try:
        mailbox = MailBox(host=host, port=port).login(email, password)
        if command == 'create_folder':
            folder = request.form['folder']
            return create_folder(mailbox, folder)
        elif command == 'get_n_messages':
            folder = request.form['folder']
            return get_n_messages(mailbox, folder)
        elif command == 'move_to':
            uid = request.form['uid']
            return move_to(mailbox, uid, folder)
        elif command == 'save_draft':
            # uid = request.form['uid']
            return save_draft(mailbox, uid, folder)
    except:
        return -1  # status code that there was an error
    finally:
        mailbox.logout()


def create_folder(mailbox, folder):
    mailbox.folder.create(folder)


def get_n_messages(mailbox, folder, n=10):
    mailbox.folder.set(folder)
    messages = list(mailbox.fetch(limit=n, bulk=True, reverse=True))
    for msg in messages:
        # If message is not in database, add it
        if not Email.query.filter_by(message_id=msg.message_id).first():
            email = Email(message_id=msg.message_id, subject=msg.subject, 
                          date=msg.date, text=msg.text, html=msg.html, 
                          folder=folder)
            db.session.add(email)
            db.session.commit()
            # Add attachments
            for attachment in msg.attachments:
                attachment = Attachment(filename=attachment.filename, 
                                        content_type=attachment.content_type, 
                                        data=attachment.payload, 
                                        email=email)
                db.session.add(attachment)
                db.session.commit()
                # Save attachment to disk
                attachment.save_to_disk()
    
    # # Getting the attachments:
    # for msg in msgs:
    #     for att in msg.attachments:
    #         print(att.filename, att.content_type)
    #         with open('C:/1/{}'.format(att.filename), 'wb') as f:
    #             f.write(att.payload)


def move_to(mailbox, uid, folder):
    server_folder = client_to_server_folder_name(folder, mailbox)
    mailbox.move([uid], server_folder)


def save_draft(mailbox, email):
    # JS: sends all input fields
    msg = create_msg() # construct email file
    # save to the filesystem and database
    server_folder = client_to_server_folder_name('drafts', mailbox)
    mailbox.append(msg, 'INBOX', dt=None, flag_set=[imap_tools.MailMessageFlags.SEEN]) # issue command
# subject, recipient, body, attachments

### 

def send(**kwargs):
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    app.config.update(SMPT_CONFIGS[email_provider])
    user_config = {"MAIL_DEFAULT_SENDER": email,
                   "MAIL_USERNAME": email,
                   "MAIL_PASSWORD": password}
    app.config.update(user_config)
    mail = Mail(app)
    msg = create_msg(**kwargs)
    mail.send(msg)



def create_msg(subject, recipient, body, attachments):
    """ Receives input fields needed for the email and constructs it """
    msg = Message()
    msg.subject = subject
    msg.recipients = [recipient]
    msg.body = body
    # msg.attachments = attachments

    # Add an attachment:
    with app.open_resource("logo.png") as fp:
        msg.attach(filename="logo.png", content_type="logo/png", data=fp.read())  # content_type is mimetype
    
    return msg











###

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('logged in'):
        return redirect(url_for('login'))
    ...
    # return redirect(url_for('access_folder', folder='inbox'))


# These routes will be changed
@app.route('/<folder>/', methods=['GET', 'POST'])
@app.route('/<folder>/<uuid>', methods=['GET', 'POST'])
def access_folder(folder, uuid=None):
    if not session.get('logged in'):
        return redirect(url_for('login'))
    current_folder = unquote_plus(folder)
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    try:
        with MailBox(host=host, port=port).login(email, password) as mailbox:
            print('--- Logging in to the server')
            # Get the folder names on the server:
            server_folders = mailbox.folder.list()
            folder_mapping = create_folder_mapping(email_provider, server_folders)
            user_folders = [folder for folder in folder_mapping if folder not in DEFAULT_FOLDERS]
            if current_folder not in DEFAULT_FOLDERS + user_folders:
                return redirect(url_for('access_folder', folder='inbox', uuid=uuid))

            # Render the latest N emails in the current folder 
            # (not to overload our app with ALL the emails)
            N = 10
            mailbox.folder.set(folder_mapping[current_folder])
            msgs = list(mailbox.fetch(limit=N, reverse=True, bulk=True))
            # return current_folder, folder_mapping, jsonify(msgs)
            # TODO: show folders and messages in selected folder


        # if uuid not in emails_of_folder, then uuid = uuid of the first email_of_folder.
        # if 0 emails_of_folder, this is a special case: the pages will be empty, and need a message.
        #     # how to select an email? /folder/uuid ?
        # opened_email = ... find email by uuid. Else None.
        
        return render_template('access_folder.html', 
                            title='Email Client',
                            user_folders=user_folders,
                            folder=folder,
                            uuid=uuid,
                            #    emails_of_folder=emails_of_folder,  # json
                            #    opened_email=opened_email,  # json
                            )
        
    except MailboxLoginError:
        return redirect(url_for('login'))
    


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged in'):
        return redirect(url_for('access_folder', folder='inbox'))
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
        return redirect(url_for('access_folder', folder='inbox'))
    
    return render_template('login.html', title='Log in', form=login_form)


@app.route('/logout')
def logout():
    session['email'] = None
    session['password'] = None
    session['logged in'] = False
    return redirect(url_for('login'))








# TODO: Json will render messages from database only



# TODO: add User table to the db, and user folder to the path where saving the emails


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 
# Optional TODOs:

# relationship 1-to-Many, not m-n

# can organize into a package (not as a module)

# add Check Constraint on email fields: nullable=False if not a draft
# https://dba.stackexchange.com/questions/42469/constraints-based-on-other-columns

# and for importance from 1 to 5:
# CREATE TABLE YourSchema.YourTable(YourColumn INT NOT NULL CONSTRAINT CHK_YourTable_YourColumn_ValidLimits
# CHECK(YourColumn BETWEEN 1 AND 5),
# SomeOtherColumns VARCHAR(10)
# );










# Insert this to the log in form: 

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



# TODO: after taking the login email address from the form - str.lower()


