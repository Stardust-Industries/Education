# Config
import requests
from flask import Flask, render_template, session, request, redirect, url_for, send_file
from flask_session import Session
import msal
import app_config 
import sqlite3
import random
import string
import qrcode
from datetime import datetime
from markupsafe import escape
import sys
sys.setrecursionlimit(10000)
app = Flask(__name__)
app.config.from_object(app_config)
Session(app)

from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Health check page
@app.route('/check')
def health_check():
  r = requests.get('https://education.stardust-industries.repl.co/')
  status_code = r.status_code
  now = datetime.now()
  current_time = now.strftime("%H:%M:%S")
  
  return render_template(
    'health_check.html',
    status_code=status_code,
    server_time=current_time
  )

@app.route('/check', methods=["POST"])
def check_url():
  url = request.form["url"]
  
  r = requests.get('https://education.stardust-industries.repl.co' + url)
  status_code = r.status_code

  return render_template(
    'health_check.html',
    status_code=status_code
  )

@app.route('/maintenance')
def maintenance():
  return render_template('maintenance.html')
  
# Home page
@app.route("/")
def index():
    if not session.get("user"):
        return redirect(url_for("login"))

    connection = sqlite3.connect('users.db')
    cursor = connection.cursor()

    maintenance = False # Switch to True when a feature is in progress
  
    user_data = session["user"]
    preferred_username = user_data["preferred_username"]

    if maintenance == True:
      if not preferred_username == '5296471849@cms.k12.nc.us' or preferred_username == '8892766848@cms.k12.nc.us':
        return redirect(url_for('maintenance'))

    userName = 'user' + preferred_username.replace('@', 'AT').replace('.', 'DOT')
    i = 0
    try:
      statement = cursor.execute('SELECT * FROM ' + userName)
      allClasses = []
      for classes in statement:
        print(classes)
        i += 1
        classes = classes[i]
        allClasses.append(classes)
      connection.commit()
    except:
      allClasses = []
      None
    return render_template(
      'home.html',
      allClasses=allClasses, 
      user=session["user"],
    ), connection.close()
# Class creation page
@app.route('/Create')
def create_page():
  return render_template(
    'create.html'
  )

@app.route('/Create', methods=["POST"])
def create():
  class_name = escape(request.form["classname"])
  teacher_name = escape(request.form["teachername"])
  grade = escape(request.form["grade"])
  
  connection = sqlite3.connect('classes.db', check_same_thread=False)
  cursor = connection.cursor()

  user_data = session["user"]
  preferred_username = user_data["preferred_username"]
  
  def table_name(amount):
    return ''.join(random.choice(string.ascii_letters) for character in range(amount))

  table_name = table_name(10)
  cursor.execute('CREATE TABLE IF NOT EXISTS ' + str(table_name) + ' (User_id TEXT NOT NULL PRIMARY KEY, Name TEXT, Score INT, Comment TEXT)')  

  cursor.execute('CREATE TABLE IF NOT EXISTS existing_classes (TableName TEXT, Admin_id TEXT, ClassName TEXT, TeacherName TEXT, Grade TEXT)')
  cursor.execute('INSERT INTO existing_classes VALUES (?, ?, ?, ?, ?)', (str(table_name), preferred_username, class_name, teacher_name, grade))
  connection.commit()
  connection.close()
  return redirect('https://education.stardust-industries.repl.co/classes/' + str(table_name))

  
# Class page
@app.route('/classes/<name>')
def get_url(name):
  connection = sqlite3.connect('classes.db')
  cursor = connection.cursor()
  isValid = False
  comment = None
  try:
    cursor.execute('SELECT * FROM ' + name)
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
      preferred_username = user_data["preferred_username"]  # We can't get personal data, just username and random stuff, nothing harmful
    
      admin = False
      rows = None
      # Database Stuff
      connection = sqlite3.connect('classes.db', check_same_thread=False)
      cursor = connection.cursor()
    
      cursor.execute('SELECT Score FROM ' + name + ' WHERE User_id=?', (preferred_username, ))
      users_score = cursor.fetchall()

      for Admin_id in cursor.execute('SELECT Admin_id FROM existing_classes WHERE TableName=?', (name, )):
        print('admin id: ' + str(Admin_id)) 
        admin_id = ''.join(Admin_id)
        print("Admin Id After Filter: " + admin_id)
        
      # For statements for class data (existing_classes table) needed here
      # ClassName TEXT, TeacherName TEXT, Grade TEXT
      for className in cursor.execute('SELECT ClassName FROM existing_classes WHERE TableName=?', (name, )):
        class_name = ''.join(className)
        print(class_name)
      for teacherName in cursor.execute('SELECT TeacherName FROM existing_classes WHERE TableName=?', (name, )):
        teacher_name = ''.join(teacherName)
        teacher_name = str(teacher_name)
        print(teacher_name)
      for grade in cursor.execute('SELECT Grade FROM existing_classes WHERE TableName=?', (name, )): 
        grade = ''.join(grade)
        print(grade)

      for comment in cursor.execute('SELECT Comment FROM ' + name + ' WHERE User_id = ?', (preferred_username, )):
          y = str(comment)
          i = ''.join(y)
          comment = i.replace('(', '').replace(')', '').replace(',', '').replace("'", '')
    
      for x in users_score:
          y = str(x)
          i = ''.join(y)
          row = i.replace('(', '').replace(')', '').replace(',', '')
        
      for getScore in cursor.execute('SELECT Score FROM ' + name + ' WHERE User_id=?', (preferred_username, )):
          Score = getScore
          print(Score)

          user_id = str(preferred_username)
          if admin_id == user_id:
              print("Is Admin")
              admin = True
              cursor.execute('SELECT * FROM ' + name)
              rows = cursor.fetchall()
              print('Admin has entered the building')
          else:
              admin = False
          break
      else:
          row = None
          print("not found")
          print("User Has Not Logged In Before...")
          print("Adding them to database now...")
          cursor.execute("INSERT INTO " + name + " (User_id, Name, Score, Comment) VALUES (?, ?, ?, ?)", (preferred_username, str( user_data["name"]), 0, "No Comment"))

          connection.commit()
          connection.close()

          # Add class to user profile
        
          connection = sqlite3.connect('users.db')
          cursor = connection.cursor()
        
          userName = preferred_username.replace('@', 'AT').replace('.', 'DOT')

          cursor.execute(f'CREATE TABLE IF NOT EXISTS user{userName} (Data TEXT)')
          amount = 1
          data = cursor.execute(f'SELECT * FROM user{userName}')
          for column in data.description:
              amount += 1
              print(column[0])
          
          amount = str(amount)
          addColumn = str("class" + amount)

          # SELECT Score FROM ' + name + ' WHERE User_id=?', (preferred_username, )):
        
          cursor.execute(f'ALTER TABLE user{userName} ADD COLUMN {addColumn} TEXT')
          cursor.execute(f'INSERT INTO user{userName} ({addColumn}) VALUES (?)', (name, ))
        
          connection.commit()
          connection.close()
        
  else:
    return render_template(
    '/error-codes/404.html'
  )

  return render_template(
    'index.html',
    name=name,
    isValid=isValid,
    row=row,
    rows=rows,
    admin=admin,
    user=session["user"],
    grade=grade,
    teacher_name=teacher_name,
    class_name=class_name,
    preferred_username=preferred_username,
    comment=comment
  )

@app.route('/<name>/<username>/qr')
def create_qr_code(name, username):
  
  qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
  )

  qr.add_data('https://education.stardust-industries.repl.co/user/' + name + '/' + username)
  qr.make(fit=True)

  img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
  img.save("qr-code.png")  
  
  return send_file('../qr-code.png', mimetype='image/png')


@app.route('/user/<name>/<username>')
def user_profile(name, username):
  user_data = session["user"]
  preferred_username = user_data["preferred_username"]
  
  connection = sqlite3.connect('classes.db')
  cursor = connection.cursor()

  for Admin_id in cursor.execute('SELECT Admin_id FROM existing_classes WHERE TableName=?', (name, )):
        print('admin id: ' + str(Admin_id)) 
        admin_id = ''.join(Admin_id)
        print("Admin Id After Filter: " + admin_id)

  print(admin_id + " VS " + preferred_username)
  if admin_id == preferred_username:
    print('Is Admin')
    isAdmin = True
    for getScore in cursor.execute('SELECT Score FROM ' + name + ' WHERE User_id=?', (username, )):
      Score = getScore
      print(Score)
    for getComment in cursor.execute('SELECT Comment FROM ' + name + ' WHERE User_id = ?', (username, )):
      comment = getComment
      print(comment)
    y = str(Score)
    i = ''.join(y)
    Score = i.replace('(', '').replace(')', '').replace(',', '')

    return render_template(
      'user_view.html',
      Score=Score,
      isAdmin=isAdmin,
      comment=comment
    )
  else:
    return redirect('https://education.stardust-industries.repl.co/classes/' + name)
    
  connection.commit()
  connection.close()


@app.route('/user/<name>/<username>', methods=["POST"])
def update_score_from_qr(name, username):
    val = request.form['newScore']
    comment = escape(request.form['newComment'])
    print(val)
    if val.isdigit(): # If the inputted digit is a value (Valid)
      connection = sqlite3.connect('classes.db', check_same_thread=False)
      cursor = connection.cursor()
      try:
        print("Changing Values")
        cursor.execute('UPDATE ' + name + ' SET Score = ? WHERE User_id = ?', (val, username, ))
        cursor.execute('UPDATE ' + name + ' SET Comment = ? WHERE User_id = ?', (comment, username) )
      #except:
        #print("Invalid name...")
      finally:
        connection.commit()
        connection.close()
    else:
      print('Not an integer...')

    return redirect('https://education.stardust-industries.repl.co/user/' + name + '/' + username)
  
@app.route('/all_classes')
def all_classes():
  if True:
    connection = sqlite3.connect('classes.db', check_same_thread=False)
    cursor = connection.cursor()

    cursor.execute('SELECT * FROM existing_classes')
    rows = cursor.fetchall()
    return render_template(
      'all_classes.html',
      rows=rows
    )
  else:
    return 'You are not admin'
  
# Update users
@app.route('/classes/<name>', methods=["POST"])
def update_score(name):
    users_name = request.form['user_id']
    val = request.form["newScoreForUser"]
    comment = escape(request.form["newComment"])
    print(val)
    if val.isdigit(): # If the inputted digit is a value (Valid)
      connection = sqlite3.connect('classes.db', check_same_thread=False)
      cursor = connection.cursor()
      try:
        print("Changing Values")
        cursor.execute('UPDATE ' + name + ' SET Score = ? WHERE User_id = ?', (val, users_name, ))
        cursor.execute('UPDATE ' + name + ' SET Comment = ? WHERE User_id = ?',  (comment, users_name, ))
      #except:
        #print("Invalid name...")
      finally:
        connection.commit()
        connection.close()
    else:
      print('Not an integer...')

    return redirect(url_for("get_url", name=name))

@app.route('/classes/')
def classes():
  return render_template('classes-page.html')

@app.route('/LICENSE/')
def license():
	try:
		return send_file('../LICENSE', attachment_filename='LICENSE.txt')
	except Exception as e:
		return str(e)

@app.route('/Courses/<coursename>')
def courses(coursename):
  return render_template(
    f'/courses/{coursename}.html'
  )


@app.route('/Courses/')
def courses_home():
  return render_template(
    '/courses/home.html'
  )
@app.route("/login")
def login():
    if session.get("user"):
        return redirect(url_for("index"))
    # Technically we could use empty list [] as scopes to do just sign in,
    # here we choose to also collect end user consent upfront
    session["flow"] = _build_auth_code_flow(scopes=app_config.SCOPE)
    return render_template("login.html",
                           auth_url=session["flow"]["auth_uri"],
                           version=msal.__version__)


@app.route(app_config.REDIRECT_PATH)  # Its absolute URL must match your app's redirect_uri set in AAD
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
    return render_template('/error-codes/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
  return render_template('/error-codes/500.html'), 500

app.jinja_env.globals.update(
    _build_auth_code_flow=_build_auth_code_flow)  # Used in template

app.run(host='0.0.0.0', port=8080, debug=True)