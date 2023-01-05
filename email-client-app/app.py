from flask import Flask, render_template, request, redirect
from urllib.parse import unquote_plus  # to convert variable from url format to normal text

app = Flask(__name__)

DEFAULT_FOLDERS = ['inbox', 'sent', 'drafts', 'bin']
USER_FOLDERS = ['Folder 1', 'Folder 2']  # TODO: make empty  # TODO: store them in the db, and access from db at the start

@app.route('/')
def index():
    return redirect('/inbox/')


@app.route('/<folder>/')
def access_folder(folder):
    folder_name = unquote_plus(folder)
    print(folder_name)
    if folder_name not in DEFAULT_FOLDERS + USER_FOLDERS:
        return redirect('/inbox/')
    # emails = db ...(folder_name)  # фильтр emails по названию папки базы данных
    # how to select an email? /folder/uuid ?
    # TODO: pass user_email, received after authentication, and display it
    return render_template('index.html', user_folders=USER_FOLDERS)  # and activate the respective folder (change the active property)



# TODO: create a login mechanism

# TODO: Implement moving emails from one folder to another
# (emails are removed from inbox when moved into a folder. So they can be only in 1 folder at a time)


