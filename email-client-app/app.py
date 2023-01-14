from flask import (Flask, render_template, redirect, url_for, flash, jsonify,
                   request, session)
from flask_session import Session
from secrets import token_hex
from imap_tools import (MailBox, MailMessage, MailMessageFlags,
                        MailboxFolderCreateError)
import flask_mail  # flask_mail.Mail, flask_mail.Message, flask_mail.Attachment
from util.database import get_models
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from util.configs import SMTPConfig, IMAPConfig
from util.forms import LoginForm
from util.actions import (get_user_folders,
                          client_to_server_folder_name, 
                          are_credentials_valid)


app = Flask(__name__)
# Session:
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # TODO: does this influence the browser-wide session? test it
# Database:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to prevent warning about future changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
# WTForms needs a secret key (to protect against CSRF):
app.config['SECRET_KEY'] = token_hex(16)


db, Email, Folder, Attachment, User = get_models(app)
Session(app)


@app.route('/send_email', methods=['POST'])
def send_email():
    """ Send an email """
    recipient = request.form['to']
    subject = request.form.get('subject', '')
    body = request.form.get('text', '')
    attachments = request.form.get('attachments', [])
    send(recipient, subject, body, attachments)    
    return jsonify({'success': True})


@app.route('/save_draft', methods=['POST'])
def save_draft():
    return


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
    host = IMAPConfig.config[email_provider]['MAIL_SERVER']
    port = IMAPConfig.config[email_provider]['MAIL_PORT']
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
            recipient = request.form.get('recipient')
            subject = request.form.get('subject')
            body = request.form.get('body')
            attachments = request.form.get('body')
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


### Helpful functions:

# Flask-Mail (smtp) to imap_tools (imap)
def smtp_to_imap_type(smtp_msg):
    """ 
    Converts a `Flask-Mail` message to an `imap_tools` message 
    (need in imap_tools to save email to drafts)
    """
    imap_msg = MailMessage()
    imap_msg.message_id = smtp_msg.message_id
    imap_msg.subject = smtp_msg.subject
    imap_msg.date = smtp_msg.date
    imap_msg.text = smtp_msg.body
    imap_msg.html = smtp_msg.html
    imap_msg.attachments = smtp_msg.attachments
    return imap_msg


# Must be run with app context:
def create_smtp_msg(recipient, subject, body, attachments):
    """ 
    Can use only after `mail = flask_mail.Mail(app)`.
    Receives input fields needed for the email, and creates it 
    using `Flask-Mail`: smtp (for sending).
    """
    smtp_msg = flask_mail.Message()
    smtp_msg.subject = subject
    smtp_msg.recipients = [recipient]
    smtp_msg.body = body
    smtp_msg.attachments = attachments
    return smtp_msg


# Must be run with app context:
def send(recipient, subject, body, attachments):
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    app.config.update(SMTPConfig.config[email_provider])
    user_config = {"MAIL_DEFAULT_SENDER": email,
                   "MAIL_USERNAME": email,
                   "MAIL_PASSWORD": password}
    app.config.update(user_config)
    mail = flask_mail.Mail(app)
    smtp_msg = create_smtp_msg(recipient, subject, body, attachments)
    mail.send(smtp_msg)


### Routes:

@app.route('/')
def index():
    return redirect(url_for('mailbox'))



@app.route('/mailbox', methods=['GET', 'POST'])
def mailbox():
    if not session.get('logged in'):
        return redirect(url_for('login'))
    return render_template('mailbox.html', title='Mailbox')


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

        return redirect(url_for('index'))
    
    return render_template('login.html', title='Log in', form=login_form)


@app.route('/logout')
def logout():
    session['email'] = None
    session['password'] = None
    session['logged in'] = False
    return redirect(url_for('login'))


