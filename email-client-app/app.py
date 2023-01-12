from flask import (Flask, render_template, redirect, url_for, request, 
                   session, jsonify, flash, g)
from flask_session import Session
from urllib.parse import unquote_plus  # to convert variables from url-format to normal
from imap_tools import MailBox, AND, MailboxLoginError
from secrets import token_hex
# import imap_tools
# import imaplib
# import email
from configs import SMPT_CONFIGS, IMAP_CONFIGS, POP_CONFIGS, SUPPORTED_EMAIL_PROVIDERS
from database import create_database
from forms import LoginForm


app = Flask(__name__)

# Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 20 * 60  # seconds after user inactivity

# Database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # prevent warning about future changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'

# WTForms needs a secret key (to protect against CSRF)
app.config['SECRET_KEY'] = token_hex(16)  # '080dc86b48a799f61ab7bde438ca22bb'


db, Email, Folder, Attachment = create_database(app)
Session(app)


def credentials_are_valid(email, password):
    if not email or not password:
        return False
    email_provider = email.split('@')[-1]
    if email_provider not in SUPPORTED_EMAIL_PROVIDERS:
        return False
    host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    try:
        with MailBox(host=host, port=port).login(email, password):
            return True
    except MailboxLoginError:
        return False



def create_folder_mapping(email_provider, server_folders):
    """ Create mapping: client folder name -> server folder name """
    folder_mapping = {}
    if email_provider == 'gmail.com':
        for server_folder in server_folders:
            name = server_folder.name
            flags = server_folder.flags
            if name == 'INBOX':
                folder_mapping['inbox'] = 'INBOX'
            elif '[Gmail]' in name:
                if '\\Sent' in flags:
                    folder_mapping['sent'] = name
                elif '\\Drafts' in flags:
                    folder_mapping['drafts'] = name
                elif '\\Trash' in flags:
                    folder_mapping['bin'] = name
            else:
                folder_mapping[name] = name
    elif email_provider == 'ukr.net':
        folder_mapping['inbox'] = 'Inbox'
        folder_mapping['sent'] = 'Sent'
        folder_mapping['drafts'] = 'Drafts'
        folder_mapping['bin'] = 'Trash'
        UKR_NET_NAMES = ['Inbox', 'Sent', 'Drafts', 'Trash', 'Spam']
        for server_folder in server_folders:
            name = server_folder.name
            if name not in UKR_NET_NAMES:
                folder_mapping[name] = name
    return folder_mapping


###

def query_the_server():
    """ Query the email server """
    return jsonify()


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
    # Current email folder:
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
            DEFAULT_FOLDERS = ['inbox', 'sent', 'drafts', 'bin']
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

        # # Getting the attachments:
        # for msg in msgs:
        #     for att in msg.attachments:
        #         print(att.filename, att.content_type)
        #         with open('C:/1/{}'.format(att.filename), 'wb') as f:
        #             f.write(att.payload)

        # emails_of_folder = db ...(folder_name)  # фильтр emails по названию папки базы данных

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
        if not credentials_are_valid(email, password):
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





# ### Sending emails

# email = session.get('email')
# password = session.get('password')

# app.config.update(SMPT_CONFIGS[email_provider])

# user_config = {"MAIL_DEFAULT_SENDER": user_email,
#                "MAIL_USERNAME": user_email,
#                "MAIL_PASSWORD": user_password}
# app.config.update(user_config)

# mail = Mail(app)


# def create_msg(msg):
#     msg.subject = "Hello"
#     msg.recipients = ["fokow.vladimir@gmail.com"]
#     msg.body = "Hey, sending you this email from my Flask app, lmk if it works"
#     msg.html = '<b>Hey</b>, sending you this email from my <a href="#">Flask app</a>, lmk if it works'
#     # subject – email subject header
#     # recipients – list of email addresses
#     # body – plain text message
#     # html – HTML message
#     # sender – email sender address, or MAIL_DEFAULT_SENDER by default
#     # cc – CC list
#     # bcc – BCC list
#     # attachments – list of Attachment instances
#     # reply_to – reply-to address
#     # date – send date
#     # charset – message character set
#     # extra_headers – A dictionary of additional headers for the message
#     # mail_options – A list of ESMTP options to be used in MAIL FROM command
#     # rcpt_options – A list of ESMTP options to be used in RCPT commands

#     # # Add an attachment:
#     # with app.open_resource("logo.png") as fp:
#     #     msg.attach(filename="logo.png", content_type="logo/png", data=fp.read())  # content_type is mimetype
    
#     return msg


# # Send email:
# if __name__ == '__main__':
#     with app.app_context():
#         msg = create_msg(Message())
#         mail.send(msg)





# TODO: add User table to the db, and user folder to the path where saving the emails

# TODO: Implement moving emails from one folder to another
# (emails are removed from inbox when moved into a folder. 
# So there can be only in 1 folder at a time)



# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- 
# Optional todos:

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


