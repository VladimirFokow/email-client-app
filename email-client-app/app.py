from flask import Flask, render_template, request, redirect
from urllib.parse import unquote_plus  # url variable to normal text

# TODO: create login
# TODO: replace "Your email" with your actual email

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
    # emails = db ...(folder_name)
    return render_template('dashboard.html', user_folders=USER_FOLDERS)  # and activate the respective folder (change the active property)


