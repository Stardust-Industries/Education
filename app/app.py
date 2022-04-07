import uuid
import requests
from flask import Flask, render_template, session, request, redirect, url_for
from flask_session import Session  # https://pythonhosted.org/Flask-Session
import msal
import app_config
import sqlite3
import random
import string

app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))
    # print(str(session["user"])) Can use to get fancy user data

    user_data = session["user"]
    user_name = user_data["name"]
    preferred_username = user_data["preferred_username"]  # We can't get personal data
    
    return render_template(
      'home.html',
      user=session["user"],
    )

# App creation script
@app.route('/Create')
def create():
  connection = sqlite3.connect('classes.db', check_same_thread=False)
  cursor = connection.cursor()
  
  def table_name(amount):
    return ''.join(random.choice(string.ascii_letters) for character in range(amount))

  table_name = table_name(10)
  cursor.execute('CREATE TABLE IF NOT EXISTS ' + str(table_name) + ' (User_id TEXT NOT NULL PRIMARY KEY, Name TEXT, Score INT)')  

  cursor.execute('CREATE TABLE IF NOT EXISTS existing_classes (TableName TEXT)')
  cursor.execute('INSERT INTO existing_classes VALUES (?)', (str(table_name), ))
  connection.commit()
  connection.close()
  return "Created class named: " + str(table_name)

  
# For multiple classes
@app.route('/classes/<name>')
def get_url(name):
  connection = sqlite3.connect('classes.db')
  cursor = connection.cursor()
  isValid = False
  
  try:
    cursor.execute('SELECT * FROM ' + name)
    print('It works')
    isValid = True
  except:
    print('Class does not exist')
    isValid = False
  finally:
    connection.commit()
    connection.close()

  if isValid == True:
      if not session.get("user"):
        return redirect(url_for("login"))
      print(str(session["user"])) # Can use to get fancy user data
    
      user_data = session["user"]
      user_name = user_data["name"]
      preferred_username = user_data["preferred_username"]  # We can't get personal data, just username and random stuff, nothing harmful
      print(
          str(user_data) + "\n\n\n" + str(user_name) + "\n" +
          str(preferred_username))
    
      admin = False
      rows = None
      # Database Stuff
      connection = sqlite3.connect('classes.db', check_same_thread=False)
      cursor = connection.cursor()
    
      cursor.execute('SELECT Score FROM ' + name + ' WHERE User_id=?', (preferred_username, ))
      users_score = cursor.fetchall()
    
      for x in users_score:
          y = str(x)
          i = ''.join(y)
          row = i.replace('(', '').replace(')', '').replace(',', '')

      for getScore in cursor.execute('SELECT Score FROM ' + name + ' WHERE User_id=?', (preferred_username, )):
          Score = getScore
          print(Score)
          if preferred_username == 'zjrichman@outlook.com' or preferred_username == 'noahdepalma123@yahoo.com':
              admin = True
              cursor.execute('SELECT * FROM ' + name)
              rows = cursor.fetchall()
              #for row in rows:
                  #print(row)
              print('Admin has entered the building')
          else:
              admin = False
          break
      else:
          row = None
          print("not found")
          print("User Has Not Logged In Before...")
          print("Adding them to database now...")
          cursor.execute("INSERT INTO " + name + " (User_id, Name, Score) VALUES (?, ?, ?)", (preferred_username, str( user_data["name"]), 0))
        
          connection.commit()
          connection.close()
        
    

  else:
    return render_template(
    '404.html'
  )

  return render_template(
    'index.html',
    name=name,
    isValid=isValid,
    row=row,
    rows=rows,
    admin=admin,
    user=session["user"]
  )


# Admin (Zach and Noah)
@app.route('/Admin')
def admin():
  user_data = session["user"]
  preferred_username = user_data["preferred_username"]
  
  if True or preferred_username == 'zjrichman@outlook.com' or preferred_username == '8892766848@student.cms.k12.nc.us':
    connection = sqlite3.connect('classes.db', check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM existing_classes')
    rows = cursor.fetchall()
    return render_template(
      'admin.html',
      rows=rows
    )
  else:
    return 'You commit crime by seeing this page because you not admin.'
  
# Update users
@app.route('/classes/<name>', methods=["POST"])
def update_score(name):
    users_name = request.form['user_id']
    val = request.form["newScoreForUser"]
    print(val)
    if val.isdigit(): # If the inputted digit is a value (Valid)
      connection = sqlite3.connect('classes.db', check_same_thread=False)
      cursor = connection.cursor()
      try:
        print("Changing Values")
        cursor.execute('UPDATE ' + name + ' SET Score = ? WHERE User_id = ?', (val, users_name, ))
      #except:
        #print("Invalid name...")
      finally:
        connection.commit()
        connection.close()
    else:
      print('Not an integer...')

    return redirect(url_for("get_url", name=name))


@app.route("/login")
def login():
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    return render_template("login.html",
                           auth_url=session["flow"]["auth_uri"],
                           version=msal.__version__)


@app.route(app_config.REDIRECT_PATH
           )  # Its absolute URL must match your app's redirect_uri set in AAD
def authorized():
    try:
        cache = _load_cache()
        result = _build_msal_app(cache=cache).acquire_token_by_auth_code_flow(
            session.get("flow", {}), request.args)
        if "error" in result:
            return render_template("auth_error.html", result=result)
        session["user"] = result.get("id_token_claims")
        _save_cache(cache)
    except ValueError:  # Usually caused by CSRF
        pass  # Simply ignore them
    return redirect(url_for("index"))


@app.route("/logout")
def logout():
    session.clear()  # Wipe out user and its token cache from session
    return redirect(  # Also logout from your tenant's web session
        app_config.AUTHORITY + "/oauth2/v2.0/logout" +
        "?post_logout_redirect_uri=" + url_for("login", _external=True))


@app.route("/graphcall")
def graphcall():
    token = _get_token_from_cache(app_config.SCOPE)
    if not token:
        return redirect(url_for("login"))
    graph_data = requests.get(  # Use token to call downstream service
        app_config.ENDPOINT,
        headers={
            'Authorization': 'Bearer ' + token['access_token']
        },
    ).json()
    return render_template('display.html', result=graph_data)


def _load_cache():
    cache = msal.SerializableTokenCache()
    if session.get("token_cache"):
        cache.deserialize(session["token_cache"])
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        session["token_cache"] = cache.serialize()


def _build_msal_app(cache=None, authority=None):
    return msal.ConfidentialClientApplication(
        app_config.CLIENT_ID,
        authority=authority or app_config.AUTHORITY,
        client_credential=app_config.CLIENT_SECRET,
        token_cache=cache)


def _build_auth_code_flow(authority=None, scopes=None):
    return _build_msal_app(authority=authority).initiate_auth_code_flow(
        scopes or [], redirect_uri=url_for("authorized", _external=True))


def _get_token_from_cache(scope=None):
    cache = _load_cache()  # This web app maintains one cache per session
    cca = _build_msal_app(cache=cache)
    accounts = cca.get_accounts()
    if accounts:  # So all account(s) belong to the current signed-in user
        result = cca.acquire_token_silent(scope, account=accounts[0])
        _save_cache(cache)
        return result

# 404 Error Pages
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


app.jinja_env.globals.update(
    _build_auth_code_flow=_build_auth_code_flow)  # Used in template

#if __name__ == "__main__":
app.run(host='0.0.0.0', port=8080, debug=True)