"""Configuration details"""

import functools


# For sending
SMTP_CONFIGS = {
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

DEFAULT_FOLDERS = ['inbox', 'sent', 'drafts', 'bin']  # don't change
# (if want to change - make sure everything else continues to work)



def singleton(cls):
    """
    A decorator to make a class a Singleton class.

    Usage:
    ```py
    @singleton
    class A:
        state = []
    
    a = A()
    b = A()

    assert a is b  # True
    ```

    Explanation:

    - `wrapper_singleton()` is really called when you create an instance of the class, e.g. `A()`
    - if you create `A()` again, it will return the same instance
    - `A._instance` contains the real instance of this class
    - fun fact: in Python functions are objects, so we're setting
      an attribute `_instance` on the function `wrapper_singleton`
    """
    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if wrapper_singleton._instance is None:  # (`._instance` is set to `None` below)
            wrapper_singleton._instance = cls(*args, **kwargs)
        return wrapper_singleton._instance
    wrapper_singleton._instance = None
    return wrapper_singleton


@singleton
class SMTPConfig:
    config = SMTP_CONFIGS

@singleton
class IMAPConfig:
    config = IMAP_CONFIGS


