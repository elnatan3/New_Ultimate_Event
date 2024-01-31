import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, abort, jsonify, session
from datetime import datetime
import pyrebase
# ...

# Create a flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'your secret key'

app.static_folder = 'static'
app.static_url_path = '/static'

# Firebase Configuration
config = {
  "apiKey": "AIzaSyB_idEt5ShUCgrDIvG8I5LqoB91w-rRdm8",
  "authDomain": "ultimate-ad427.firebaseapp.com",
  "projectId": "ultimate-ad427",
  "storageBucket": "ultimate-ad427.appspot.com",
  "messagingSenderId": "344399457714",
  "appId": "1:344399457714:web:02187d4dba9367d436c8ab",
  "measurementId": "G-RQKSY235B3",
  "databaseURL": "https//ultimate-ad427.firebaseapp.com"
}
# https://ultimate-ad427.firebaseio.com

firebase = pyrebase.initialize_app(config)
auth = firebase.auth()


def get_db_connection():
  conn = sqlite3.connect('database.db')
  conn.row_factory = sqlite3.Row
  return conn


@app.route('/')
def index():
  if 'user_id' in session:
    return redirect(url_for('events'))
  elif 'organizer_id' in session:
    return redirect(url_for('organizer'))
  else:
    return render_template('index.html')


@app.route('/welcome')
def welcome():
  return render_template('welcome.html')


@app.route('/existing_user/new_user')
def new_user():
  return render_template('create_user.html')


@app.route('/organizer_login/new_organizer')
def new_organizer():
  return render_template('create_organizer.html')


# User routes
@app.route('/existing_user')
def existing_user():
  return render_template('existing_user.html')


def extract_email_domain(email):
  return email.split('@')[-1]


@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if len(password) < 6:
            flash('Password should be at least 6 characters long.', 'error')
            return redirect(url_for('create_user'))

    
        email_domain = extract_email_domain(email)
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE username = ? OR email = ?', (username, email)).fetchone()
        organizer = conn.execute('SELECT * FROM Organizers WHERE name = ? OR email = ?', (username, email)).fetchone()

        if user or organizer:
            flash('That username or email is already taken.', 'error')
            conn.close()
            return redirect(url_for('create_user'))

        try:
            firebase_user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(firebase_user['idToken'])
            # auth.create_user_with_email_and_password(email, password)
            # auth.sign_in_with_email_and_password(email,password)
            flash('Account created successfully. Please check your email and verify.', 'success')
        except Exception as e:
            flash(f'Failed to create account:', 'error')
        # Insert the new user into the User table
        conn.execute('INSERT INTO Users (username, email, EmailDomain) VALUES (?, ?, ?)',
                         (username, email, email_domain))     
        conn.commit()
        conn.close()
        return redirect(url_for('existing_user'))

    return render_template('create_user.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Authenticate with Firebase
            firebase_user = auth.sign_in_with_email_and_password(email, password)

            # Get Firebase user data to check email verification status
            user_data = auth.get_account_info(firebase_user['idToken'])
            email_verified = user_data['users'][0]['emailVerified']

            if not email_verified:
                flash('Your email address has not been verified.', 'error')
                return redirect(url_for('existing_user'))

            # Set user session or additional login logic
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()

            if user is None:
                flash('User not found.', 'error')
                conn.close()
                return redirect(url_for('existing_user'))

            # Update local database if email is verified in Firebase
            conn.commit()
            session['user_id'] = user['UserID']
            flash('Logged in successfully', 'success')
            return redirect(url_for('events'))

        except Exception as e:
            print("Login failed:", e)
            flash('Login failed. Please check your email and password.', 'error')

    return redirect(url_for('existing_user'))




@app.route('/logout', methods=['POST'])
def logout():
  session.pop('user_id', None)
  return redirect(url_for('index'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ?', (email,)).fetchone()
        organizer = conn.execute('SELECT * FROM Organizers WHERE email = ?', (email,)).fetchone()

        if user or organizer:
            try:
                # Send password reset email
                auth.send_password_reset_email(email)
                flash('A password reset link has been sent to your email address.', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
        else:
            flash('Email address not found.', 'error')

        conn.close()
        return render_template('welcome.html')

    return render_template('reset_password.html')



# Organizer routes
@app.route('/organizer_login')
def existing_organizer():
  return render_template('organizer_login.html')


@app.route('/organizer_login', methods=['GET', 'POST'])
def organizer_login():
  if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            # Authenticate with Firebase
            firebase_user = auth.sign_in_with_email_and_password(email, password)

            # Get Firebase user data to check email verification status
            user_data = auth.get_account_info(firebase_user['idToken'])
            email_verified = user_data['users'][0]['emailVerified']

            if not email_verified:
                flash('Your email address has not been verified.', 'error')
                return redirect(url_for('existing_organizer'))
            # Set user session or additional login logic
            conn = get_db_connection()
            organizer = conn.execute('SELECT * FROM Organizers WHERE email = ?', (email,)).fetchone()

            if organizer is None:
                flash('Organizer not found.', 'error')
                conn.close()
                return redirect(url_for('existing_organizer'))

            # Update local database if email is verified in Firebase
            conn.commit()
            session['organizer_id'] = organizer['OrganizerID']
            flash('Logged in successfully', 'success')
            return redirect(url_for('organizer'))

        except Exception as e:
            print("Login failed:", e)
            flash('Login failed. Please check your email and password.', 'error')
  return redirect(url_for('existing_organizer'))


@app.route('/organizer_login/create_organizer', methods=['POST'])
def create_organizer():
  if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        email = request.form['email']
        password = request.form['password']

        if len(password) < 6:
            flash('Password should be at least 6 characters long.', 'error')
            return redirect(url_for('create_organizer'))

    
        email_domain = extract_email_domain(email)
        conn = get_db_connection()
        organizer = conn.execute('SELECT * FROM Organizers WHERE name = ? OR email = ?', (name, email)).fetchone()
        user = conn.execute('SELECT * FROM Users WHERE username = ? OR email = ?', (name, email)).fetchone()
        if organizer or user:
            flash('That username or email is already taken.', 'error')
            conn.close()
            return redirect(url_for('create_organizer'))

        try:
            firebase_user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(firebase_user['idToken'])
            # auth.create_user_with_email_and_password(email, password)
            # auth.sign_in_with_email_and_password(email,password)
            flash('Account created successfully. Please verify your email.', 'success')
        except Exception as e:
            flash(f'Failed to create account: {str(e)}', 'error')
        # Insert the new user into the User table
        conn.execute('INSERT INTO Organizers (name, description, email, password, EmailDomain) VALUES (?, ?, ?, ?, ?)',(name, description, email, password, email_domain))     
        conn.commit()
        conn.close()
        return redirect(url_for('existing_organizer'))

  return render_template('create_organizer.html')


@app.route('/organizer_logout', methods=['POST'])
def organizer_logout():
  session.pop('organizer_id', None)
  return redirect(url_for('index'))


@app.route('/events', methods=['GET'])
def events():
    if 'user_id' not in session:
        return redirect(url_for('existing_user'))

    conn = get_db_connection()
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Get the user's email domain
    user_id = session['user_id']
    user = conn.execute('SELECT * FROM Users WHERE UserID = ?', (user_id,)).fetchone()
    user_email_domain = user['EmailDomain']

    # Fetch events where the organizer's email domain matches the user's email domain
    # Updated query to fetch organizer's email
    events = conn.execute('''
        SELECT e.*, o.email as OrganizerEmail FROM Events e
        INNER JOIN OrganizerEvent oe ON e.EventID = oe.EventID
        INNER JOIN Organizers o ON oe.OrganizerID = o.OrganizerID
        WHERE e.EventDateTime >= ? AND o.EmailDomain = ?
        ''', (current_datetime, user_email_domain)).fetchall()

    conn.close()
    return render_template('events.html', events=events)



@app.route('/upcoming_events')
def upcoming_events():
  if 'user_id' not in session:
    return redirect(url_for('existing_user'))

  user_id = session['user_id']

  conn = get_db_connection()
  current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  upcoming_events = conn.execute(
    'SELECT e.* FROM Events e INNER JOIN UserEvent ue ON e.EventID = ue.EventID WHERE ue.UserID = ? AND e.EventDateTime > ?',
    (user_id, current_datetime)).fetchall()
  conn.close()

  return render_template('upcoming_events.html', events=upcoming_events)


@app.route('/remove_event/<int:event_id>', methods=['POST'])
def remove_event(event_id):
  if 'user_id' not in session:
    return redirect(url_for('existing_user'))

  user_id = session['user_id']

  conn = get_db_connection()

  # Check if the user is registered for the event
  registered_event = conn.execute(
    'SELECT * FROM UserEvent WHERE UserID = ? AND EventID = ?',
    (user_id, event_id)).fetchone()

  if registered_event:
    # Remove the event registration for the user
    conn.execute('DELETE FROM UserEvent WHERE UserID = ? AND EventID = ?',
                 (user_id, event_id))
    conn.commit()
    flash('Event removed successfully.', 'success')
  else:
    flash('Event not found.', 'error')

  conn.close()

  return redirect(url_for('upcoming_events'))


@app.route('/previous_events')
def previous_events():
  if 'user_id' not in session:
    return redirect(url_for('existing_user'))

  user_id = session['user_id']

  conn = get_db_connection()
  current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  previous_events = conn.execute(
    'SELECT e.* FROM Events e INNER JOIN UserEvent ue ON e.EventID = ue.EventID WHERE ue.UserID = ? AND e.EventDateTime < ?',
    (user_id, current_datetime)).fetchall()
  conn.close()

  return render_template('previous_events.html', events=previous_events)


@app.route('/events/register/<int:event_id>', methods=['POST'])
def register_event(event_id):
  if 'user_id' not in session:
    return redirect(url_for('existing_user'))

  user_id = session['user_id']

  conn = get_db_connection()

  # Check if the user is already registered for the event
  registered_event = conn.execute(
    'SELECT * FROM UserEvent WHERE UserID = ? AND EventID = ?',
    (user_id, event_id)).fetchone()

  if registered_event:
    flash('You are already registered for this event.', 'error')
  else:
    # Register the user for the event
    conn.execute('INSERT INTO UserEvent (UserID, EventID) VALUES (?, ?)',
                 (user_id, event_id))
    conn.commit()
    flash('Event registration successful.', 'success')

  conn.close()

  return redirect(url_for('events'))


# Organizer routes
@app.route('/organizer')
def organizer():
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  organizer_id = session['organizer_id']

  conn = get_db_connection()
  organizer = conn.execute('SELECT * FROM Organizers WHERE OrganizerID = ?',
                           (organizer_id, )).fetchone()
  conn.close()

  if organizer:
    return render_template('organizer_profile.html', organizer=organizer)
  else:
    flash('Organizer not found.', 'error')
    return redirect(url_for('organizer_login'))


@app.route('/organizer/profile')
def organizer_profile():
  if 'organizer_id' in session:
    organizer_id = session['organizer_id']
    conn = get_db_connection()
    organizer = conn.execute('SELECT * FROM Organizers WHERE OrganizerID = ?',
                             (organizer_id, )).fetchone()
    conn.close()

    if organizer:
      return render_template('organizer_profile.html', organizer=organizer)
    else:
      flash('Organizer not found.', 'error')

  return redirect(url_for('organizer_login'))


@app.route('/create_event', methods=['GET', 'POST'])
def create_event():
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  if request.method == 'POST':
    name = request.form.get('name')
    description = request.form.get('description')
    event_datetime_str = request.form.get('event_datetime')

    if not name or not description or not event_datetime_str:
      flash('Please fill in all the fields.', 'error')
      return redirect(url_for('create_event'))

    try:
      event_datetime = datetime.strptime(event_datetime_str, '%Y-%m-%dT%H:%M')
      current_datetime = datetime.now()

      if event_datetime <= current_datetime:
        flash('Please select a date and time after the current date and time.',
              'error')
        return redirect(url_for('create_event'))

      organizer_id = session['organizer_id']
      conn = get_db_connection()

      # Insert event into the Events table
      cursor = conn.cursor()
      cursor.execute(
        "INSERT INTO Events (Name, Description, EventDateTime, OrganizerID) VALUES (?, ?, ?, ?)",
        (name, description, event_datetime_str, organizer_id))
      event_id = cursor.lastrowid

      # Insert entry into the OrganizerEvent table
      cursor.execute(
        "INSERT INTO OrganizerEvent (OrganizerID, EventID) VALUES (?, ?)",
        (organizer_id, event_id))

      flash('Event created successfully!', 'success')

      conn.commit()
      conn.close()

      return redirect(url_for('upcoming_events_organizer'))

    except ValueError:
      flash('Invalid date and time format.', 'error')
      return render_template('create_event.html')

  return render_template('create_event.html')


@app.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  if request.method == 'POST':
    name = request.form.get('name')
    description = request.form.get('description')
    event_datetime_str = request.form.get('event_datetime')

    if not name or not description or not event_datetime_str:
      flash('Please fill in all the fields.', 'error')
      return redirect(url_for('edit_event', event_id=event_id))

    try:
      event_datetime = datetime.strptime(event_datetime_str, '%Y-%m-%dT%H:%M')
      current_datetime = datetime.now()

      if event_datetime <= current_datetime:
        flash('Please select a date and time after the current date and time.',
              'error')
        return redirect(url_for('edit_event', event_id=event_id))

      conn = get_db_connection()
      event = conn.execute("SELECT * FROM Events WHERE EventID = ?",
                           (event_id, )).fetchone()

      if event is None:
        flash('Event not found.', 'error')
        return redirect(url_for('upcoming_events_organizer'))

      conn.execute(
        "UPDATE Events SET Name = ?, Description = ?, EventDateTime = ? WHERE EventID = ?",
        (name, description, event_datetime_str, event_id))
      flash('Event updated successfully!', 'success')

      conn.commit()
      conn.close()

      return redirect(url_for('upcoming_events_organizer'))

    except ValueError:
      flash('Invalid date and time format.', 'error')
      return render_template('edit_event.html', event=event)

  conn = get_db_connection()
  event = conn.execute("SELECT * FROM Events WHERE EventID = ?",
                       (event_id, )).fetchone()
  conn.close()

  if event is None:
    flash('Event not found.', 'error')
    return redirect(url_for('upcoming_events_organizer'))

  return render_template('edit_event.html', event=event)


@app.route('/organizer/upcoming_events')
def upcoming_events_organizer():
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  organizer_id = session['organizer_id']

  conn = get_db_connection()
  current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  upcoming_events = conn.execute(
    '''
      SELECT e.*, COUNT(ue.UserID) AS RegisteredUsers
      FROM Events e
      LEFT JOIN UserEvent ue ON e.EventID = ue.EventID
      INNER JOIN OrganizerEvent oe ON e.EventID = oe.EventID
      WHERE e.EventDateTime > ? AND oe.OrganizerID = ?
      GROUP BY e.EventID
      ''', (current_datetime, organizer_id)).fetchall()
  conn.close()

  return render_template('upcoming_events_organizer.html',
                         events=upcoming_events)


@app.route('/organizer/remove_event/<int:event_id>', methods=['POST'])
def remove_event_organizer(event_id):
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  organizer_id = session['organizer_id']

  conn = get_db_connection()

  # Check if the event belongs to the organizer
  event = conn.execute(
    'SELECT * FROM Events e INNER JOIN OrganizerEvent oe ON e.EventID = oe.EventID WHERE e.EventID = ? AND oe.OrganizerID = ?',
    (event_id, organizer_id)).fetchone()

  if event:
    # Remove the event
    conn.execute('DELETE FROM Events WHERE EventID = ?', (event_id, ))
    conn.commit()
    flash('Event removed successfully.', 'success')
  else:
    flash('Event not found.', 'error')

  conn.close()

  return redirect(url_for('upcoming_events_organizer'))


@app.route('/organizer/previous_events')
def previous_events_organizer():
  if 'organizer_id' not in session:
    return redirect(url_for('organizer_login'))

  organizer_id = session['organizer_id']

  conn = get_db_connection()
  current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  previous_events = conn.execute(
    '''
        SELECT e.*, COUNT(ue.UserID) AS RegisteredUsers
        FROM Events e
        LEFT JOIN UserEvent ue ON e.EventID = ue.EventID
        INNER JOIN OrganizerEvent oe ON e.EventID = oe.EventID
        WHERE e.EventDateTime < ? AND oe.OrganizerID = ?
        GROUP BY e.EventID
        ''', (current_datetime, organizer_id)).fetchall()
  conn.close()

  return render_template('previous_events_organizer.html',
                         events=previous_events)


@app.route('/organizer/view_registered_users/<event_id>')
def view_registered_users(event_id):
  conn = get_db_connection()
  registered_users = conn.execute(
    '''
        SELECT u.Username
        FROM Users u
        INNER JOIN UserEvent ue ON u.UserID = ue.UserID
        WHERE ue.EventID = ?
        ''', (event_id, )).fetchall()
  conn.close()

  return render_template('registered_users.html', users=registered_users)


if __name__ == '__main__':
  # Run the Flask app
  app.run(host='0.0.0.0', debug=True, port=8080)
