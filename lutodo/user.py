

from lutodo import app
from lutodo import db
from flask import redirect, render_template, request, session, url_for
from flask_bcrypt import Bcrypt
import re
from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename

# Create an instance of the Bcrypt class, which we'll be using to hash user
# passwords during login and registration.
flask_bcrypt = Bcrypt(app)
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}

# Default role assigned to new users upon registration.
DEFAULT_USER_ROLE = 'student'

def user_home_url():
    """Generates a URL to the homepage for the currently logged-in user.
    
    If the user is not logged in, this returns the URL for the login page
    instead. If the user appears to be logged in, but the role stored in their
    session cookie is invalid (i.e. not a recognised role), it returns the URL
    for the logout page to clear that invalid session data."""
    if 'loggedin' in session:
        role = session.get('user_role', None)

        if role=='student':
            home_endpoint='student_home'
        elif role=='staff':
            home_endpoint='staff_home'
        elif role=='admin':
            home_endpoint='admin_home'
        else:
            home_endpoint = 'logout'
    else:
        home_endpoint = 'login'
    
    return url_for(home_endpoint)

@app.route('/')
def root():
    """Root endpoint (/)
    
    Methods:
    - get: Redirects guests to the login page, and redirects logged-in users to
        their own role-specific homepage.
    """
    return redirect(user_home_url())

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page endpoint.

    Methods:
    - get: Renders the login page.
    - post: Attempts to log the user in using the credentials supplied via the
        login form, and either:
        - Redirects the user to their role-specific homepage (if successful)
        - Renders the login page again with an error message (if unsuccessful).
    
    If the user is already logged in, both get and post requests will redirect
    to their role-specific homepage.
    """
    if 'loggedin' in session:
         return redirect(user_home_url())

    if request.method=='POST' and 'email' in request.form and 'password' in request.form:
        # Get the login details submitted by the user.
        email = request.form['email']
        password = request.form['password']

        # Attempt to validate the login details against the database.
        with db.get_cursor() as cursor:
            # Try to retrieve the account details for the specified username.
            #
            # Note: we use a Python multiline string (triple quote) here to
            # make the query more readable in source code. This is just a style
            # choice: the line breaks are ignored by PostgreSQL, and it would
            # be equally valid to put the whole SQL statement on one line like
            # we do at the beginning of the `signup` function.
            cursor.execute('''
                           SELECT user_id, email, password_hash, user_role, first_name, 
                           last_name, position, profile_picture, status 
                           FROM users
                           WHERE email = %s;
                           ''', (email,))
            account = cursor.fetchone()
            
            if account is not None:
                if account['status'] == 'inactive':
                    return render_template('login.html',
                                           email=email,
                                           account_inactive=True)

                # We found a matching account: now we need to check whether the
                # password they supplied matches the hash in our database.
                password_hash = account['password_hash']
                
                if flask_bcrypt.check_password_hash(password_hash, password):
                    # Password is correct. Save the user's ID, username, and role
                    # as session data, which we can access from other routes to
                    # determine who's currently logged in.
                    # 
                    # Users can potentially see and edit these details using their
                    # web browser. However, the session cookie is signed with our
                    # app's secret key. That means if they try to edit the cookie
                    # to impersonate another user, the signature will no longer
                    # match and Flask will know the session data is invalid.
                    session['loggedin'] = True
                    session['user_id'] = account['user_id']
                    session['email'] = account['email']
                    session['user_role'] = account['user_role']

                    return redirect(user_home_url())
                else:
                    # Password is incorrect. Re-display the login form, keeping
                    # the username provided by the user so they don't need to
                    # re-enter it. We also set a `password_invalid` flag that
                    # the template uses to display a validation message.
                    return render_template('login.html',
                                           email=email,
                                           password_invalid=True)
            else:
                # We didn't find an account in the database with this username.
                # Re-display the login form, keeping the username so the user
                # can see what they entered (otherwise, they might just keep
                # trying the same thing). We also set a `username_invalid` flag
                # that tells the template to display an appropriate message.
                #
                # Note: In this example app, we tell the user if the user
                # account doesn't exist. Many websites (e.g. Google, Microsoft)
                # do this, but other sites display a single "Invalid username
                # or password" message to prevent an attacker from determining
                # whether a username exists or not. Here, we accept that risk
                # to provide more useful feedback to the user.
                return render_template('login.html', 
                                       email=email,
                                       email_invalid=True)

    # This was a GET request, or an invalid POST (no username and/or password),
    # so we just render the login form with no pre-populated details or flags.
    return render_template('login.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    """Signup (registration) page endpoint.

    Methods:
    - get: Renders the signup page.
    - post: Attempts to create a new user account using the details supplied
        via the signup form, then renders the signup page again with a welcome
        message (if successful) or one or more error message(s) explaining why
        signup could not be completed.

    If the user is already logged in, both get and post requests will redirect
    to their role-specific homepage.
    """
    if 'loggedin' in session:
         return redirect(user_home_url())
    
    if (request.method == 'POST' 
        and 'first_name' in request.form 
        and 'last_name' in request.form 
        and 'position' in request.form
        and 'email' in request.form
        and 'password' in request.form
        and 'confirm_password' in request.form):
        # Get the details submitted via the form on the signup page, and store
        # the values in temporary local variables for ease of access. For some 
        # of them, strip.() will be applied.

        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        position = request.form['position'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        profile_picture = request.files.get('profile_picture')
        profile_picture_filename = None

        # We start by assuming that everything is okay. If we encounter any
        # errors during validation, we'll store an error message in one or more
        # of these variables so we can pass them through to the template.
        first_name_error = None
        last_name_error = None
        position_error = None
        email_error = None
        password_error = None
        confirm_password_error = None
        profile_picture_error = None

        # Check whether there's an account with this username in the database.
        with db.get_cursor() as cursor:
            cursor.execute('SELECT user_id FROM users WHERE email = %s;',
                           (email,))
            account_already_exists = cursor.fetchone() is not None
        
        # Validate the email, ensuring that it's unique (as we just checked
        # above) and meets the naming constraints of our web app.
        if account_already_exists:
            email_error = 'An account already exists with this email.'

        # Validate first_name, last_name and all required inputs.
        if not first_name.strip():
            first_name_error = 'First name cannot be empty.'
        elif len(first_name) > 50:
            first_name_error = 'Your first name cannot exceed 50 characters.'
        if not last_name.strip():
            last_name_error = 'Last name cannot be empty.'
        elif len(last_name) > 50:
            last_name_error = 'Your last name cannot exceed 50 characters.'
        
        # Validate the new user's email address. Note: The regular expression
        # we use here isn't a perfect check for a valid address, but is
        # sufficient for this example. The maximum length is based on RFC 3696,
        # Errata 1690 (https://errata.rfc-editor.org/eid1690/).
        if len(email) > 254:
            # As above, the user should never see this error under normal
            # conditions because we set a maximum input length in the template.
            email_error = 'Your email address cannot exceed 254 characters.'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            email_error = 'Invalid email address.'
        # Validate email address as required in the assessment to 
        # make sure only uni staff or student email is accepted.
        if email.endswith('@lincolnuni.ac.nz'):
            user_role = 'student'
        elif email.endswith('@lincoln.ac.nz'):
            user_role = 'staff'
        else:
            email_error = 'You must use a valid Lincoln University email address.'
                
        # Validate password. Length and content will be validated.
        if len(password) < 8:
            password_error = 'Password must be at least 8 characters long!'
        elif not re.search(r'[A-Z]', password):
            password_error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', password):
            password_error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', password):
            password_error = 'Password must contain at least one number (0-9).'
        elif not re.search(r'[!@#$%^&*]', password):
            password_error = 'Password must contain at least one special character (!@#$%^&*).'

        # Password consistency validation.
        if confirm_password != password:
            confirm_password_error = 'The passwords do not match.'

        # Profile picture name validation and save.
        if profile_picture and profile_picture.filename:
            safe_filename = secure_filename(profile_picture.filename)
            extension = Path(safe_filename).suffix.lower()

            if extension not in ALLOWED_IMAGE_EXTENSIONS:
                profile_picture_error = 'Please upload a PNG, JPG, JPEG, GIF, OR WEBP image.'
            else:
                profile_picture_filename = f'{uuid4().hex}{extension}'

        # Validate the position input.
        if not position.strip():
            position_error = 'Position cannot be empty.'
        elif len(position) > 50:
            position_error = 'Position cannot exceed 50 characters.'
        

        
        if (first_name_error
            or last_name_error 
            or email_error 
            or password_error
            or confirm_password_error
            or profile_picture_error
            or position_error):
            # One or more errors were encountered, so send the user back to the
            # For security reasons, we never send back the password they chose.
            return render_template('signup.html',
                                   first_name = first_name,
                                   last_name = last_name,
                                   email=email,
                                   position = position,
                                   first_name_error=first_name_error,
                                   last_name_error=last_name_error,
                                   email_error=email_error,
                                   password_error=password_error,
                                   confirm_password_error = confirm_password_error,
                                   profile_picture_error = profile_picture_error,
                                   position_error = position_error)
        else:
            # The new account details are valid. Hash the user's new password
            # and create their account in the database.
            password_hash = flask_bcrypt.generate_password_hash(password).decode()

            # Save the profile_pictures that are uploaded and validated.
            if profile_picture_filename:
                # Create an origin tha python accepts.
                upload_folder = Path(app.static_folder) / 'profile_pictures'
                # Check if the folders are there.
                upload_folder.mkdir(parents=True, exist_ok=True)
                # Save into profile_pictures
                profile_picture.save(upload_folder / profile_picture_filename)
            
            # Note: In this example, we just assume the SQL INSERT statement
            # below will run successfully. But what if it doesn't?
            #
            # If the INSERT fails for any reason, the database connector will
            # throw an exception and the user will receive a generic error
            # page. We should implement our own error handling here to deal
            # with that possibility in a way that's more useful to the user.
            with db.get_cursor() as cursor:
                cursor.execute('''
                               INSERT INTO users (
                               first_name, 
                               last_name,
                               email, 
                               password_hash, 
                               position,
                               profile_picture,
                               user_role,
                               status)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                               ''',
                               (first_name,
                                last_name, 
                                email, 
                                password_hash,
                                position,
                                profile_picture_filename,
                                user_role,
                                'active',))
            
            # Now that registration is complete, send the user back to the
            # signup page. We set the `signup_successful` flag to display a
            # post-signup message.
            return render_template('signup.html', signup_successful=True)            

    # This was a GET request, or an invalid POST (no username, email, and/or
    # password). Render the signup page with no pre-populated form fields or
    # error messages.
    return render_template('signup.html')

@app.route('/profile')
def profile():
    """User Profile page endpoint.

    Methods:
    - get: Renders the user profile page for the current user.

    If the user is not logged in, requests will redirect to the login page.
    """
    if 'loggedin' not in session:
         return redirect(url_for('login'))

    # Retrieve user profile from the database.
    with db.get_cursor() as cursor:
        cursor.execute('SELECT username, email, user_role FROM users WHERE user_id = %s;',
                       (session['user_id'],))
        profile = cursor.fetchone()

    return render_template('profile.html', profile=profile)

@app.route('/logout')
def logout():
    """Logout endpoint.

    Methods:
    - get: Logs the current user out (if they were logged in to begin with),
        and redirects them to the login page.
    """
    # Note that nothing actually happens on the server when a user logs out: we
    # just remove the cookie from their web browser. They could technically log
    # back in by manually restoring the cookie we've just deleted. In a high-
    # security web app, you may need additional protections against this (e.g.
    # keeping a record of active sessions on the server side).
    session.pop('loggedin', None)
    session.pop('user_id', None)
    session.pop('email', None)
    session.pop('user_role', None)
    
    return redirect(url_for('login'))