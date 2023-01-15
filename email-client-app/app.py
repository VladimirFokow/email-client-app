from flask import (Flask, render_template, redirect, url_for, flash, jsonify,
                   request, session)
from flask_session import Session
from secrets import token_hex
from util.database import get_models
from util.forms import LoginForm
from util.util import are_credentials_valid
from util.configs import SMTPConfig
from util.actions import (GetFoldersAndNMessages, CreateFolder, MoveTo, 
                          SaveDraft, SendEmail)

app = Flask(__name__)
# Session:
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True  # TODO: does this influence the browser-wide session? test it
# Database:
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # to prevent warning about future changes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emails.db'
# WTForms needs a secret key (to protect against CSRF):
app.config['SECRET_KEY'] = token_hex(16)

models = get_models(app)
db, Email, Folder, Attachment, User = models
Session(app)


# Routes:

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


# Routes for POST requests:

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
    command = request.form['command']
    if command == 'get_folders_and_n_messages':
        return GetFoldersAndNMessages(request, session, models).execute()
    elif command == 'create_folder':
        return CreateFolder(request, session, models).execute()
    elif command == 'move_to':
        return MoveTo(request, session, models).execute()
    elif command == 'save_draft':
        return SaveDraft(request, session, models).execute()


@app.route('/send_email', methods=['POST'])
def send_email():
    """ Send an email """
    email = session.get('email')
    password = session.get('password')
    email_provider = email.split('@')[-1]
    app.config.update(SMTPConfig.config[email_provider])
    user_config = {"MAIL_DEFAULT_SENDER": email,
                    "MAIL_USERNAME": email,
                    "MAIL_PASSWORD": password}
    app.config.update(user_config)
    send_object = SendEmail(request, session, models)
    send_object.app = app
    return send_object.execute()



