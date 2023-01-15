from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError, DataError, IntegrityError
from imap_tools import (MailBox, MailMessage, MailMessageFlags,
                        MailboxFolderCreateError)
import flask_mail  # flask_mail.Mail, flask_mail.Message, flask_mail.Attachment
from abc import ABC, abstractmethod
from .configs import SMTPConfig, IMAPConfig
from .util import get_user_folders, client_to_server_folder_name



class ExecuteCommand(ABC):
    """
    Abstract class for executing commands on the server.
    `execute` is the template method, which calls `run_command` (implemented by subclasses).
    """
    def __init__(self, request, session, models) -> None:
        self.request = request
        self.session = session
        self.db, self.Email, self.Folder, self.Attachment, self.User = models
        self.email = session.get('email')
        self.password = session.get('password')
        self.email_provider = self.email.split('@')[-1]
        self.host = IMAPConfig.config[self.email_provider]['MAIL_SERVER']
        self.port = IMAPConfig.config[self.email_provider]['MAIL_PORT']
    
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


class GetFoldersAndNMessages(ExecuteCommand):
    def get_parameters(self):
        self.folder = self.request.form['folder']
        self.n = self.request.form.get('n', 10)
    
    def run_command(self, mailbox):
        db = self.db
        User = self.User
        Folder = self.Folder
        Email = self.Email
        # Email of the owner of the account:
        owner_email = self.email
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
        server_folder = client_to_server_folder_name(self.folder, mailbox)
        mailbox.folder.set(server_folder)
        messages = list(mailbox.fetch(limit=self.n, bulk=True, reverse=True))

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
            email_exists = (db.session.execute(db.select(Email)
                            .where(Email.uid == msg.uid)
                            .where(Email.owner == owner)).first())
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
            new_folder = Folder(name=folder)
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
    
    def run_command(self, mailbox):
        db = self.db
        server_folder = client_to_server_folder_name(self.folder, mailbox)
        mailbox.move([self.uid], server_folder)
        return jsonify({'success': True})


class SaveDraft(ExecuteCommand):
    def get_parameters(self):
        recipient = self.request.form.get('recipient')
        subject = self.request.form.get('subject')
        body = self.request.form.get('body')
        attachments = self.request.form.get('body')
        self.smtp_msg = create_smtp_msg(recipient, subject, body, attachments)

    def run_command(self, mailbox):
        server_folder = client_to_server_folder_name('drafts', mailbox)
        mailbox.append(self.smtp_msg, server_folder, dt=None, flag_set=[MailMessageFlags.DRAFT])
        return jsonify({'success': True})


class SendEmail(ExecuteCommand):
    def get_parameters(self):
        self.recipient = self.request.form['to']
        self.subject = self.request.form.get('subject', '')
        self.body = self.request.form.get('text', '')
        self.attachments = self.request.form.get('attachments', [])

    def run_command(self, mailbox):
        mail = flask_mail.Mail(self.app)  # this has to be before `create_smtp_msg`
        smtp_msg = create_smtp_msg(self.recipient, self.subject, self.body, self.attachments)
        mail.send(smtp_msg)
        return jsonify({'success': True})


### Helpful functions:

def create_smtp_msg(recipient, subject, body, attachments):
    """ 
    Can use only after `mail = flask_mail.Mail(app)`.
    Receives input fields needed for the email, and creates it 
    using `Flask-Mail`: smtp (for sending).

    Must be run with app context.
    """
    smtp_msg = flask_mail.Message()
    smtp_msg.subject = subject
    smtp_msg.recipients = [recipient]
    smtp_msg.body = body
    smtp_msg.attachments = attachments
    return smtp_msg


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


