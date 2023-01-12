from flask_sqlalchemy import SQLAlchemy


def create_database(app):
    db = SQLAlchemy(app)

    MAX_EMAIL_ADDR_LEN = 254  # RFC 2821
    MAX_EMAIL_SUBJ_LEN = 255  # RFC 2822 says it's 998 but most other email clients have it 255 or 256
    MAX_FOLDER_NAME_LEN = 64  # folders in the email client
    MAX_FILE_NAME_LEN = 255


    # import os
    # DB_USER = os.environ.get("DB_USER")
    # DB_PASSWORD = os.environ.get("DB_PASSWORD")


    # class EmailFolder(db.Model):
    #     email_folder_id = db.Column('id', db.Integer, primary_key=True)
    #     email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
    #     folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)


    # Many-to-Many association table:  # TODO: make it many to one (email belongs only to 1 folder)
    email_folder = db.Table(
        'email_folder', 
        db.Column("email_id", db.Integer, db.ForeignKey("email.id")),
        db.Column("folder_id", db.Integer, db.ForeignKey("folder.id")),
    )


    class Email(db.Model):
        email_id = db.Column('id', db.Integer, primary_key=True)  # TODO: replace with uuid?
        path = db.Column(db.String)  
        # path in the file system: ./<email>/data/emails/<uuid>/<email_id>.eml
        time = db.Column(db.Time)
        address_from = db.Column('from', db.String(MAX_EMAIL_ADDR_LEN))
        address_to = db.Column('to', db.String(MAX_EMAIL_ADDR_LEN))
        subject = db.Column(db.String(MAX_EMAIL_SUBJ_LEN))
        importance = db.Column(db.Integer)
        folders = db.relationship("Folder", secondary=email_folder, backref="emails")
        def __repr__(self):
            return (f"<Email(email_id={self.email_id}, "
                    f"path={self.path}, "
                    f"time={self.time}, "
                    f"address_from={self.address_from}, "
                    f"address_to={self.address_to}, "
                    f"subject={self.subject}, "
                    f"importance={self.importance})>")


    class Folder(db.Model):
        folder_id = db.Column('id', db.Integer, primary_key=True)
        name = db.Column(db.String(MAX_FOLDER_NAME_LEN), nullable=False)
        def __repr__(self):
            return f"<Folder(folder_id={self.folder_id}, name={self.name})>"


    class Attachment(db.Model):
        attachment_id = db.Column('id', db.Integer, primary_key=True)
        email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
        filename = db.Column(db.String(MAX_FILE_NAME_LEN), nullable=False)
        path = db.Column(db.String, nullable=False)  
        # path in the file system: ./<email>/data/emails/<uuid>/attachents/<filename>
        def __repr__(self):
            return (f"<Attachment(attachment_id={self.attachment_id}, "
                    f"email_id={self.email_id}, "
                    f"filename={self.filename}, "
                    f"path={self.path})>")


    with app.app_context():
        db.create_all()  # create table schema in the database 
        # (does not update tables if they are already in the database)

    return db, Email, Folder, Attachment



# users = db.session.execute(db.select(User).order_by(User.username)).scalars()

# db.session.add(user)
# db.session.commit()
# user.id

# user = db.get_or_404(User, id)


# user = db.get_or_404(User, id)

# if request.method == "POST":
#     db.session.delete(user)
#     db.session.commit()

