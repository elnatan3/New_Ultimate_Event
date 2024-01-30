import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, abort, jsonify, session
from datetime import datetime
# ...

# Create a flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'your secret key'

app.static_folder = 'static'
app.static_url_path = '/static'


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


@app.route('/create_user', methods=['POST'])
def create_user():
  username = request.form['username']
  password = request.form['password']
  email = request.form['email']

  conn = get_db_connection()

  # Check if the username is already in use
  user = conn.execute('SELECT * FROM Users WHERE username = ?',
                      (username, )).fetchone()
  if user is not None:
    message = 'That username is already taken.'
    conn.close()
    return render_template('existing_user.html', message=message)

  # Insert the new user into the User table
  conn.execute(
    'INSERT INTO Users (username, password, email) VALUES (?, ?, ?)',
    (username, password, email))
  conn.commit()

  # Log the user in automatically
  user = conn.execute(
    'SELECT * FROM Users WHERE username = ? AND password = ?',
    (username, password)).fetchone()
  session['user_id'] = user['UserID']

  conn.close()

  return redirect(url_for('index'))


@app.route('/login', methods=['POST'])
def login():
  username = request.form['username']
  password = request.form['password']
  conn = get_db_connection()

  user = conn.execute(
    'SELECT * FROM Users WHERE username = ? AND password = ?',
    (username, password)).fetchone()

  if user is None:
    message = 'Invalid username or password.'
    conn.close()
    return render_template('existing_user.html', message=message)

  # Create a session variable to store the user's UserID
  session['user_id'] = user['UserID']

  conn.close()
  return redirect(url_for('events'))


@app.route('/logout', methods=['POST'])
def logout():
  session.pop('user_id', None)
  return redirect(url_for('index'))


# Organizer routes
@app.route('/organizer_login')
def existing_organizer():
  return render_template('organizer_login.html')


@app.route('/organizer_login', methods=['GET', 'POST'])
def organizer_login():
  if request.method == 'POST':
    email = request.form['email']
    password = request.form['password']
    conn = get_db_connection()

    organizer = conn.execute(
      'SELECT * FROM Organizers WHERE email = ? AND password = ?',
      (email, password)).fetchone()

    if organizer is None:
      message = 'Invalid email or password.'
      conn.close()
      return render_template('organizer_login.html', message=message)

    session['organizer_id'] = organizer['OrganizerID']
    conn.close()

    return redirect(url_for('organizer'))
  else:
    return render_template('organizer_login.html')


@app.route('/organizer_login/create_organizer', methods=['POST'])
def create_organizer():
  name = request.form['name']
  description = request.form['description']
  email = request.form['email']
  password = request.form['password']

  conn = get_db_connection()

  # Check if the email is already in use
  organizer = conn.execute('SELECT * FROM Organizers WHERE email = ?',
                           (email, )).fetchone()
  if organizer is not None:
    message = 'An account with that email already exists.'
    conn.close()
    return render_template('organizer_login.html', message=message)

  # Insert the new organizer into the Organizers table
  conn.execute(
    'INSERT INTO Organizers (name, description, email, password) VALUES (?, ?, ?, ?)',
    (name, description, email, password))
  conn.commit()

  # Log the organizer in automatically
  organizer = conn.execute(
    'SELECT * FROM Organizers WHERE email = ? AND password = ?',
    (email, password)).fetchone()
  session['organizer_id'] = organizer['OrganizerID']

  conn.close()

  return redirect(url_for('index'))


@app.route('/organizer_logout', methods=['POST'])
def organizer_logout():
  session.pop('organizer_id', None)
  return redirect(url_for('index'))


# Event routes
@app.route('/events', methods=['GET'])
def events():
  if 'user_id' not in session:
    return redirect(url_for('existing_user'))

  conn = get_db_connection()

  # Get the current date and time
  current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

  # Fetch events that are past today's date and time
  events = conn.execute('SELECT * FROM Events WHERE EventDateTime >= ?',
                        (current_datetime, )).fetchall()
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
