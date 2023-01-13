from .configs import IMAP_CONFIGS, SUPPORTED_EMAIL_PROVIDERS, DEFAULT_FOLDERS
from imap_tools import MailBox, MailboxLoginError


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


def get_mailbox_folder_mapping(mailbox):
    host = mailbox._get_mailbox_client().host
    if 'ukr.net' in host:
        host = 'ukr.net'
    elif 'gmail.com' in host:
        host = 'gmail.com'
    email_provider = host.split('@')[-1]
    server_folders = mailbox.folder.list()
    folder_mapping = create_folder_mapping(email_provider, server_folders)
    return folder_mapping


def get_user_folders(mailbox):
    """ Return a list of only user folders """
    folder_mapping = get_mailbox_folder_mapping(mailbox)
    user_folders = [folder for folder in folder_mapping if folder not in DEFAULT_FOLDERS]
    return user_folders


def client_to_server_folder_name(client_folder, mailbox):
    """ Convert a single client folder name -> to server folder name """
    folder_mapping = get_mailbox_folder_mapping(mailbox)
    return folder_mapping[client_folder]


def are_credentials_valid(email, password):
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

#######################################################




