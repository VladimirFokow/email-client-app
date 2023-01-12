"""Configuration details"""

# For sending
SMPT_CONFIGS = {
    'gmail.com': dict(MAIL_SERVER='smtp.gmail.com',
                      MAIL_PORT=465,  # 587 if TLS=True, SSL=False
                      MAIL_USE_TLS=False,
                      MAIL_USE_SSL=True),
    'ukr.net': dict(MAIL_SERVER='smtp.ukr.net',
                    MAIL_PORT=465,
                    MAIL_USE_TLS=False,
                    MAIL_USE_SSL=True),
    'i.ua': dict(MAIL_SERVER='smtp.i.ua',
                 MAIL_PORT=465,
                 MAIL_USE_TLS=False,
                 MAIL_USE_SSL=True)
}

# For receiving
IMAP_CONFIGS = {
    'gmail.com': dict(MAIL_SERVER='imap.gmail.com',
                      MAIL_PORT=993,
                      MAIL_USE_TLS=False,
                      MAIL_USE_SSL=True),
    'ukr.net': dict(MAIL_SERVER='imap.ukr.net',
                    MAIL_PORT=993,
                    MAIL_USE_TLS=False,
                    MAIL_USE_SSL=True),
    'i.ua': dict(MAIL_SERVER='imap.i.ua',
                 MAIL_PORT=995,
                 MAIL_USE_TLS=False,
                 MAIL_USE_SSL=True)
}

POP_CONFIGS = {
    'gmail.com': dict(MAIL_SERVER='pop.gmail.com',
                      MAIL_PORT=995,
                      MAIL_USE_TLS=False,
                      MAIL_USE_SSL=True),
    'ukr.net': dict(MAIL_SERVER='pop3.ukr.net',
                    MAIL_PORT=995,
                    MAIL_USE_TLS=False,
                    MAIL_USE_SSL=True),
    'i.ua': dict(MAIL_SERVER='pop3.i.ua',
                 MAIL_PORT=995,
                 MAIL_USE_TLS=False,
                 MAIL_USE_SSL=True)
}


SUPPORTED_EMAIL_PROVIDERS = ['gmail.com', 'ukr.net']

