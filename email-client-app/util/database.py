from flask_sqlalchemy import SQLAlchemy

# import os
# DB_USER = os.environ.get("DB_USER")
# DB_PASSWORD = os.environ.get("DB_PASSWORD")

MAX_EMAIL_ADDR_LEN = 254  # RFC 2821
MAX_EMAIL_SUBJ_LEN = 255  # RFC 2822 says it's 998 but most other email clients have it 255 or 256
MAX_FOLDER_NAME_LEN = 32  # max name length of folders in the email client
MAX_FILE_NAME_LEN = 255


def get_models(app):
    db = SQLAlchemy(app)


    # Many-to-Many association table:  # TODO: make it many to one (email belongs only to 1 folder)
    email_folder = db.Table(
        'email_folder', 
        db.Column("email_id", db.Integer, db.ForeignKey("email.id")),
        db.Column("folder_id", db.Integer, db.ForeignKey("folder.id")),
    )


    class Email(db.Model):
        email_id = db.Column('id', db.Integer, primary_key=True)
        owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        uid = db.Column(db.Integer)
        date = db.Column(db.DateTime)
        from_ = db.Column('from', db.String(MAX_EMAIL_ADDR_LEN))
        to = db.Column('to', db.String(MAX_EMAIL_ADDR_LEN))
        subject = db.Column(db.String(MAX_EMAIL_SUBJ_LEN))
        text = db.Column(db.String)  # email body (if not stored in the filesystem)

        # ## path = db.Column(db.String)  # path in the file system: ./<username>/data/emails/<uid>/<email_id>.eml  # (this would store the path of the email file if it was stored in the filesystem)
        folders = db.relationship("Folder", secondary=email_folder, backref="emails")  # also declare a property 'emails' on the 'Folder' class
        attachments = db.relationship("Attachment", backref="email", lazy=True)  # also declare a property 'email' on the 'Attachment' class
        def __repr__(self):
            return (f"<Email(email_id={self.email_id}, "
                    f"owner={self.owner}, "
                    f"uid={self.uid}, "
                    f"date={self.date}, "
                    f"from_={self.from_}, "
                    f"to={self.to}, "
                    f"subject={self.subject}, "
                    f"len(text)={len(self.text) if self.text else None}>")
    

    class Folder(db.Model):
        folder_id = db.Column('id', db.Integer, primary_key=True)
        owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        name = db.Column(db.String(MAX_FOLDER_NAME_LEN), nullable=False)
        def __repr__(self):
            return f"<Folder(folder_id={self.folder_id}, name={self.name})>"


    class Attachment(db.Model):
        attachment_id = db.Column('id', db.Integer, primary_key=True)
        email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
        filename = db.Column(db.String(MAX_FILE_NAME_LEN), nullable=False)
        content_type = db.Column(db.String)  # MIME type of the attachment
        path = db.Column(db.String, nullable=False)  # path in the file system: ./<username>/data/emails/<uid>/attachments/<filename.ext>
        def __repr__(self):
            return (f"<Attachment(attachment_id={self.attachment_id}, "
                    f"email_id={self.email_id}, "
                    f"filename={self.filename}, "
                    f"path={self.path})>")


    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(MAX_EMAIL_ADDR_LEN), unique=True, nullable=False)  # user's email address
        
        emails = db.relationship('Email', backref='owner', lazy=True)  # all ids of this user's emails
        folders = db.relationship('Folder', backref='owner', lazy=True)  # all ids of this user's folders
        def __repr__(self):
            return f"<User(id={self.id}, username={self.username})>"


    with app.app_context():
        db.create_all()  # create table schema in the database 
        # (does not update tables if they are already in the database)
    
    return db, Email, Folder, Attachment, User



