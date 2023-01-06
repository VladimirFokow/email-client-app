from flask import Flask, render_template, request, redirect
from urllib.parse import unquote_plus  # to convert variable from url format to normal text

app = Flask(__name__)

DEFAULT_FOLDERS = ['inbox', 'sent', 'drafts', 'bin']
USER_FOLDERS = ['Folder 1', 'Folder 2']  # TODO: make empty  # TODO: store them in the db, and access from db at the start

@app.route('/')
def index():
    return redirect('/inbox/')


@app.route('/<folder>/')
@app.route('/<folder>/<uuid>')
def access_folder(folder, uuid=None):
    folder_name = unquote_plus(folder)

    print(folder_name)
    print(f'{uuid=}')

    if folder_name not in DEFAULT_FOLDERS + USER_FOLDERS:
        return redirect('/inbox/')
    # emails_of_folder = db ...(folder_name)  # фильтр emails по названию папки базы данных

    # if uuid not in emails_of_folder, then uuid = uuid of the first email_of_folder.
    # if 0 emails_of_folder, this is a special case: the pages will be empty, and need a message.
    #     # how to select an email? /folder/uuid ?
    # opened_email = ... find email by uuid. Else None.
    return render_template('index.html', 
                           user_folders=USER_FOLDERS,
                           folder=folder,
                           uuid=uuid,
                        #    emails_of_folder=emails_of_folder,  # json
                        #    opened_email=opened_email,  # json
                           )


@app.route('/login')
def log_in():
    return redirect('/inbox/')


@app.route('/logout')
def log_out():
    return redirect('/inbox/')



# TODO: Implement moving emails from one folder to another
# (emails are removed from inbox when moved into a folder. 
# So there can be only in 1 folder at a time)

