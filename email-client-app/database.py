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


    # many-to-many association table:
    email_folder = db.Table(
        db.Column("email_id", db.ForeignKey("email.id"), primary_key=True),
        db.Column("folder_id", db.ForeignKey("folder.id"), primary_key=True),
    )


    class Email(db.Model):
        email_id = db.Column('id', db.Integer, primary_key=True)  # TODO: replace with uuid?
        path = db.Column(db.String)  # path in the file system: ./data/emails/<uuid>/<email_id>.eml
        time = db.Column(db.Time)
        address_from = db.Column('from', db.String(MAX_EMAIL_ADDR_LEN))
        address_to = db.Column('to', db.String(MAX_EMAIL_ADDR_LEN))
        subject = db.Column(db.String(MAX_EMAIL_SUBJ_LEN))
        importance = db.Column(db.Integer)
        folders = db.relationship("Folder", secondary=email_folder, backref="emails")


    class Folder(db.Model):
        folder_id = db.Column('id', db.Integer, primary_key=True)
        name = db.Column(db.String(MAX_FOLDER_NAME_LEN), nullable=False)


    class Attachment(db.Model):
        attachment_id = db.Column('id', db.Integer, primary_key=True)
        email_id = db.Column(db.Integer, db.ForeignKey('email.id'), nullable=False)
        filename = db.Column(db.String(MAX_FILE_NAME_LEN), nullable=False)
        path = db.Column(db.String, nullable=False)  # path in the file system: ./data/emails/<uuid>/attachents/<filename>


    with app.app_context():
        db.create_all()  # creates the table schema in the database 
        # (does not update tables if they are already in the database)
        



# users = db.session.execute(db.select(User).order_by(User.username)).scalars()

# db.session.add(user)
# db.session.commit()
# user.id

# user = db.get_or_404(User, id)


# user = db.get_or_404(User, id)

# if request.method == "POST":
#     db.session.delete(user)
#     db.session.commit()

