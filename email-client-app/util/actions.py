from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
import imap_tools  # imap_tools.MailMessage
from imap_tools import MailBox, MailMessageFlags, MailboxFolderCreateError
import flask_mail  # flask_mail.Mail, flask_mail.Message, flask_mail.Attachment
from abc import ABC, abstractmethod
from .configs import SMTPConfig, IMAPConfig
from .util import create_folder_mapping, client_to_server_folder_name


### Helpful functions:

def create_smtp_msg(recipient, subject, body, attachments, app):
    """ 
    Can use only after `mail = flask_mail.Mail(app)`.
    Receives input fields needed for the email, and creates it 
    using `Flask-Mail`: smtp (for sending).

    Must be run with app context.
    """
    mail = flask_mail.Mail(app)  # has to be before `flask_mail.Message()`
    smtp_msg = flask_mail.Message()
    smtp_msg.subject = subject
    smtp_msg.recipients = [recipient]
    smtp_msg.body = body
    smtp_msg.attachments = attachments
    return mail, smtp_msg


def create_imap_msg(recipient, subject, body, attachments, app):
    mail, smtp_msg = create_smtp_msg(recipient, subject, body, attachments, app)
    imap_msg = imap_tools.MailMessage.from_bytes(smtp_msg.as_bytes())
    return imap_msg


### Classes:

class ExecuteCommand(ABC):
    """
    Abstract class for executing commands on the server.
    `execute` is the template method, which calls `run_command` (implemented by subclasses).
    """
    def __init__(self, request, session, models, app=None):
        self.request = request
        self.session = session
        self.db, self.Email, self.Folder, self.Attachment, self.User = models
        self.app = app
        self.email = session.get('user_email')
        self.password = session.get('user_password')
        self.email_provider = self.email.split('@')[-1]
        self.host = IMAPConfig.config[self.email_provider]['MAIL_SERVER']
        self.port = IMAPConfig.config[self.email_provider]['MAIL_PORT']
        if app:
            app.config.update(SMTPConfig.config[self.email_provider])
            user_config = {"MAIL_DEFAULT_SENDER": self.email,
                           "MAIL_USERNAME": self.email,
                           "MAIL_PASSWORD": self.password}
            app.config.update(user_config)
    
    def execute(self):
        """Template method"""
        with MailBox(host=self.host, port=self.port).login(self.email, self.password) as mailbox:
            self.get_parameters()
            result = self.run_command(mailbox)
            return result
    
    @abstractmethod
    def get_parameters(self):
        """Abstract method - to be implemented by subclasses"""
        pass

    @abstractmethod
    def run_command(self, mailbox):
        """Abstract method - to be implemented by subclasses"""
        pass


class GetEmails(ExecuteCommand):
    def get_parameters(self):
        self.n = self.request.form.get('n', 10)
    
    def run_command(self, mailbox):
        # db = self.db
        # User = self.User
        # Folder = self.Folder
        # Email = self.Email
        # # Email of the owner of the account:
        # owner_email = self.email
        # owner = db.session.execute(db.select(User).where(User.username == owner_email)).scalar_one()
        # if not owner:
        #     return jsonify({'success': False, 'error': 'User not found in database'})

        # # Fetch all owner's folders from the server
        # user_folders = get_user_folders(mailbox)  # list of user folder names

        # # .. and add them to the local database:
        # for folder_name in user_folders:
        #     folder_object = Folder(name=folder_name, owner=owner)
        #     db.session.add(folder_object)

        # Fetch n owner's emails from the server (from each folder):
        email_messages = {}  # { <folder> : { <uid> : <msg_info> } }
        # folder_mapping = { <client_folder_name> : <server_folder_name> } - for the default folders, and all user folders:
        folder_mapping = create_folder_mapping(self.email_provider, mailbox)
        for client_f_name, server_f_name in folder_mapping.items():
            mailbox.folder.set(server_f_name)
            messages = mailbox.fetch(limit=self.n, bulk=True, reverse=True)
            folder_data = {}
            for msg in messages:
                folder_data[msg.uid] = {
                    'uid': msg.uid,
                    'date': msg.date.isoformat(),  # convert datetime to string
                    'from_': msg.from_,
                    'to': msg.to[0] if msg.to else '',  # msg.to is a list of recipients
                    'subject': msg.subject,
                    'text': msg.text,
                }
            email_messages[client_f_name] = folder_data
        
        # # .. and add them to the local database:
        # msg_infos = []
        # for msg in messages:
        #     # Prepare the message info (to be returned):
        #     msg_info = {
        #         'uid': msg.uid,
        #         'date': msg.date.isoformat(),
        #         'from_': msg.from_,
        #         'to': msg.to[0],
        #         'subject': msg.subject,
        #         'text': msg.text,
        #     }
        #     msg_infos.append(msg_info)

        #     # If message is not in database - add it:
        #     # filter by the owner as well
        #     email_exists = (db.session.execute(db.select(Email)
        #                     .where(Email.uid == msg.uid)
        #                     .where(Email.owner == owner)).first())
        #     if not email_exists:
        #         email = Email(owner=owner, **msg_info)
        #         email.date = msg.date  # datetime, not string
        #         db.session.add(email)
        
        # try:
        #     db.session.commit()
        # except SQLAlchemyError as e:
        #     db.session.rollback()
        #     return jsonify({'success': False, 'error': str(e)})
        
        # Return owner's emails from all the folders:
        return jsonify({'success': True, 'email_messages': email_messages})


class CreateFolder(ExecuteCommand):
    def get_parameters(self):
        self.folder = self.request.form['folder']
    
    def run_command(self, mailbox):
        db = self.db
        folder = self.folder
        Folder = self.Folder
        # Command to the server:
        try:
            mailbox.folder.create(folder)
        except MailboxFolderCreateError as e:
            # could not create folder on the server
            return jsonify({'success': False, 'error': str(e)})

        # Command to the local database:
        try:
            # Get the owner from the database:
            User = self.User
            owner = db.session.execute(db.select(User).where(User.username == self.email)).scalar_one()
            # Add the folder to the database:
            new_folder = Folder(name=folder, owner=owner)
            db.session.add(new_folder)
            db.session.commit()
        except (DataError, IntegrityError) as e:
            # DataError - if folder already exists
            # IntegrityError - if folder name is too long
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)})
        return jsonify({'success': True})


class MoveTo(ExecuteCommand):
    def get_parameters(self):
        self.uid = self.request.form['uid']
        self.folder = self.request.form['folder']
        self.new_folder = self.request.form['new_folder']
    
    def run_command(self, mailbox):
        db = self.db
        server_folder = client_to_server_folder_name(self.folder, mailbox)
        server_new_folder = client_to_server_folder_name(self.new_folder, mailbox)
        mailbox.folder.set(server_folder)
        mailbox.move([self.uid], server_new_folder)
        return jsonify({'success': True})


class SendToBin(MoveTo):
    def get_parameters(self):
        self.uid = self.request.form['uid']
        self.folder = self.request.form['folder']
        self.new_folder = 'bin'


class DeleteEmail(ExecuteCommand):
    def get_parameters(self):
        self.uid = self.request.form['uid']
        self.folder = self.request.form['folder']
    
    def run_command(self, mailbox):
        db = self.db
        server_folder = client_to_server_folder_name(self.folder, mailbox)
        mailbox.folder.set(server_folder)
        mailbox.delete([self.uid])
        return jsonify({'success': True})


class SaveEmail(ExecuteCommand):
    def __init__(self, request, session, models, app):  # `app` is a required parameter
        super().__init__(request, session, models, app)
    
    def get_parameters(self):
        self.save_folder = self.request.form.get('save_folder', 'drafts')
        recipient = self.request.form.get('to', '')
        subject = self.request.form.get('subject', '')
        body = self.request.form.get('text', '')
        attachments = self.request.form.get('attachments', [])
        self.imap_msg = create_imap_msg(recipient, subject, body, attachments, self.app)

    def run_command(self, mailbox):
        server_folder = client_to_server_folder_name(self.save_folder, mailbox)
        typ, data = mailbox.append(self.imap_msg, server_folder, dt=None, flag_set=[MailMessageFlags.DRAFT])
        # # typ, data = 'OK', [b'[APPENDUID 17 11] (Success)']
        try:
            uid = int(data[0].split()[2].strip(b']'))
        except IndexError:
            uid = None
        return jsonify({'success': True, 'uid': uid})


class SendEmail(ExecuteCommand):
    def __init__(self, request, session, models, app):  # `app` is a required parameter
        super().__init__(request, session, models, app)
    
    def get_parameters(self):
        self.recipient = self.request.form['to']
        self.subject = self.request.form.get('subject', '')
        self.body = self.request.form.get('text', '')
        self.attachments = self.request.form.get('attachments', [])

    def run_command(self, mailbox):
        mail, smtp_msg = create_smtp_msg(self.recipient, self.subject, self.body, self.attachments, self.app)
        mail.send(smtp_msg)
        return jsonify({'success': True})



