from imap_tools import MailBox, AND, MailboxLoginError
from configs import SMPT_CONFIGS, IMAP_CONFIGS, POP_CONFIGS, SUPPORTED_EMAIL_PROVIDERS
from functools import wraps


class ConnectionStorage:
    """
    Class for creating, deleting, storing and providing to different requests
    the same connection to an email server.

    Example:
    >>> conn_storage = ConnectionStorage()
    >>> # mailbox = conn_storage.get_connection()  # mailbox` is `None`
    
    >>> try:
    ...     mailbox = conn_storage.create_connection(email, password)
    ...     # `mailbox` is `imap_tools.mailbox.MailBox` now
    ... except MailboxLoginError:
    ...     pass
    >>> mailbox = conn_storage.get_connection()  
    >>> # `mailbox` is `imap_tools.mailbox.MailBox` now (if no error)
    
    >>> mailbox.close_connection()  # Remember to logout after you're done!
    """
    def __init__(self):
        self.mailbox = None
    

    def logout_beforehand(func):
        """Decorator to delete connection (if exists) before executing the function."""
        @wraps(func)  # to preserve the original function's internal info
        def decorated(self, *args, **kwargs):
            self.close_connection()
            return func(self, *args, **kwargs)
        return decorated


    @logout_beforehand
    def create_connection(self, email, password, folder='INBOX'):
        """ Raises: MailboxLoginError if login failed. """
        if not email:
            raise MailboxLoginError('Empty email.')
        if not password:
            raise MailboxLoginError('Empty password.')
        email_provider = email.split('@')[-1]
        if email_provider not in SUPPORTED_EMAIL_PROVIDERS:
            raise MailboxLoginError(f'Only these email providers are supported: {", ".join(SUPPORTED_EMAIL_PROVIDERS)}')
        host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
        port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
        self.mailbox = MailBox(host=host, port=port).login(email, password, folder)
        print(f'-----> logged in to: {email}')  # TODO: delete this line
        return self.get_connection()


    def get_connection(self):
        return self.mailbox


    def close_connection(self):
        mailbox = self.get_connection()
        if mailbox:
            mailbox.logout()
        self.mailbox = None

    
    # def return_connection(self, conn):
    #     self.connections.append(conn)



    # def credentials_are_valid(email: str | None, password: str | None):
    #     # return True  # TODO: delete. This is for testing only
    #     if not email or not password:
    #         return False
    #     email_provider = email.split('@')[-1]
    #     if email_provider not in ['gmail.com', 'ukr.net']:
    #         return False
    #     host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    #     port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    #     try:
    #         with MailBox(host=host, port=port).login(email, password):
    #             print('--- Logging in to the server')
    #             return True
    #     except MailboxLoginError:
    #         return False




    # def create_folder_mapping(email_provider, server_folders):
    #     """ Create mapping: client folder name -> server folder name """
    #     folder_mapping = {}
    #     if email_provider == 'gmail.com':
    #         for server_folder in server_folders:
    #             name = server_folder.name
    #             flags = server_folder.flags
    #             if name == 'INBOX':
    #                 folder_mapping['inbox'] = 'INBOX'
    #             elif '[Gmail]' in name:
    #                 if '\\Sent' in flags:
    #                     folder_mapping['sent'] = name
    #                 elif '\\Drafts' in flags:
    #                     folder_mapping['drafts'] = name
    #                 elif '\\Trash' in flags:
    #                     folder_mapping['bin'] = name
    #             else:
    #                 folder_mapping[name] = name
    #     elif email_provider == 'ukr.net':
    #         folder_mapping['inbox'] = 'Inbox'
    #         folder_mapping['sent'] = 'Sent'
    #         folder_mapping['drafts'] = 'Drafts'
    #         folder_mapping['bin'] = 'Trash'
    #         UKR_NET_NAMES = ['Inbox', 'Sent', 'Drafts', 'Trash', 'Spam']
    #         for server_folder in server_folders:
    #             name = server_folder.name
    #             if name not in UKR_NET_NAMES:
    #                 folder_mapping[name] = name
    #     return folder_mapping


    # def access_folder(self, email: str | None, password: str | None, current_folder: str):
    #     email_provider = email.split('@')[-1]
    #     if email_provider not in ['gmail.com', 'ukr.net']:
    #         return go_to_login
    #     host = IMAP_CONFIGS[email_provider]['MAIL_SERVER']
    #     port = IMAP_CONFIGS[email_provider]['MAIL_PORT']
    #     try:
    #         with MailBox(host=host, port=port).login(email, password) as mailbox:
    #             print('--- Logging in to the server')
    #             # Get the folder names on the server:
    #             server_folders = mailbox.folder.list()
    #             folder_mapping = create_folder_mapping(email_provider, server_folders)

    #             # Render the latest N emails in the current folder 
    #             # (not to overload our app with ALL the emails)
    #             N = 10
    #             mailbox.folder.set(folder_mapping[current_folder])
    #             msgs = list(mailbox.fetch(limit=N, reverse=True, bulk=True))
    #             # return current_folder, folder_mapping, jsonify(msgs)
    #             # TODO: show folders and messages in selected folder

    #         # # Getting the attachments:
    #         # for msg in msgs:
    #         #     for att in msg.attachments:
    #         #         print(att.filename, att.content_type)
    #         #         with open('C:/1/{}'.format(att.filename), 'wb') as f:
    #         #             f.write(att.payload)

    #         # emails_of_folder = db ...(folder_name)  # фильтр emails по названию папки базы данных

    #         # if uuid not in emails_of_folder, then uuid = uuid of the first email_of_folder.
    #         # if 0 emails_of_folder, this is a special case: the pages will be empty, and need a message.
    #         #     # how to select an email? /folder/uuid ?
    #         # opened_email = ... find email by uuid. Else None.
        


