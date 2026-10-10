from lutodo import app
from lutodo import db
from flask import redirect, request, render_template, session, url_for, flash
from pathlib import Path # This is the tool dealing with file path.

@app.route('/admin/home')
def admin_home():
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['user_role']!='admin':
          return render_template('access_denied.html'), 403
     tasks = db.get_open_tasks_for_user(session['user_id'])
     return render_template('admin_home.html', tasks=tasks)

# List and search users.
@app.route('/admin/users')
# Autherization check.
def admin_users():
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['user_role']!='admin':
          return render_template('access_denied.html'), 403

     # Request the information admin types in.
     search = request.args.get('search', '').strip()

     with db.get_cursor() as cursor:
          if search:
               search_pattern = f'%{search}%'

               cursor.execute(
                    '''
                    SELECT user_id, email, first_name, last_name,
                           position, profile_picture, user_role, status
                    FROM users
                    WHERE   email ILIKE %s
                         OR first_name ILIKE %s
                         OR last_name ILIKE %s
                         OR position ILIKE %s
                    ORDER BY first_name, last_name;
                    ''',
                    (
                         search_pattern,
                         search_pattern,
                         search_pattern,
                         search_pattern,
                     )
                     )
          else:
               cursor.execute(
                    '''
                    SELECT user_id, email, first_name, last_name,
                         position, profile_picture, user_role, status
                    FROM users
                    ORDER BY first_name, last_name;
                    '''
                    )
          users = cursor.fetchall()
     return render_template('admin_users.html', users=users, search=search)

# View and edit users by admin.
@app.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
def admin_user(user_id):
     if 'loggedin' not in session:
          return redirect(url_for('login'))
     elif session['user_role'] != 'admin':
          return render_template('access_denied.html'), 403
     # Using id fetch all detailed information.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               SELECT user_id, email, first_name, last_name,
                    position, profile_picture, user_role, status
               FROM users
               WHERE user_id = %s;
               ''',
               (user_id,)
          )
          user = cursor.fetchone()

     if user is None:
          flash('User not found.', 'danger')
          return redirect(url_for('admin_users'))

     # Change the role and status.
     if request.method == 'POST':
          new_role = request.form['user_role']
          new_status = request.form['status']
          # Set change rules:
          # New_role only allows student, staff and admin.
          if new_role not in ('student', 'staff', 'admin'):
               flash('Invalid user role.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          # Student role cannot be changed.
          if user['user_role'] == 'student' and new_role != 'student':
               flash('Student accounts cannot change role.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          # Staff and admin cannot be changed to stduent.
          if user['user_role'] in ('staff', 'admin') and new_role == 'student':
               flash('Staff or admin accounts cannot become students.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          # Admin cannot change their own roles.
          if user_id == session['user_id'] and new_role != 'admin':
               flash('You cannot change your own admin role.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          # Set status change rules.
          if new_status not in ('active', 'inactive'):
               flash('Invalid user status.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          if user_id == session['user_id'] and new_status != 'active':
               flash('You cannot make your own account inactive.', 'danger')
               return redirect(url_for('admin_user', user_id=user_id))
          # Update database.
          with db.get_cursor() as cursor:
               cursor.execute(
                    '''
                    UPDATE users
                    SET user_role = %s,
                        status = %s
                    WHERE user_id = %s;
                    ''',
                    (
                         new_role,
                         new_status,
                         user_id
                    )
               )

          flash('User updated successfully.', 'success')
          return redirect(url_for('admin_user', user_id=user_id))

     return render_template('admin_user.html', user=user)

# Admin delete users.
@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
def delete_user(user_id):
     # User must be logged in.
     if 'loggedin' not in session:
          return redirect(url_for('login'))

     # Only admins can delete users.
     elif session['user_role'] != 'admin':
          return render_template('access_denied.html'), 403

     # Admin cannot delete their own account.
     elif user_id == session['user_id']:
          flash('You cannot delete your own account.', 'danger')
          return redirect(url_for('admin_user', user_id=user_id))

     # Delete the user from the database.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               DELETE FROM users
               WHERE user_id = %s
               RETURNING profile_picture;
               ''',
               (user_id,)
          )
          deleted_user = cursor.fetchone()

     # No user matched that user_id.
     if deleted_user is None:
          flash('User not found.', 'danger')
          return redirect(url_for('admin_users'))

     # Delete their profile-picture file, if one exists.
     if deleted_user['profile_picture']:
          picture_path = (Path(app.static_folder) / 'profile_pictures' / deleted_user['profile_picture'])

          if picture_path.is_file():
               picture_path.unlink()

     flash('User deleted successfully.', 'success')
     return redirect(url_for('admin_users'))

# View all shared project.
@app.route('/admin/projects')
def admin_projects():
     # User must be logged in.
     if 'loggedin' not in session:
          return redirect(url_for('login'))

     # Only admins can access this page.
     elif session['user_role'] != 'admin':
          return render_template('access_denied.html'), 403

     # Retrieve every shared project.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               SELECT
                    p.project_id,
                    p.project_name,
                    p.description,
                    p.owner_id,
                    u.first_name AS owner_first_name,
                    u.last_name AS owner_last_name,
                    COUNT(pm.user_id) AS member_count
               FROM projects AS p
               JOIN users AS u
                    ON p.owner_id = u.user_id
               JOIN project_members AS pm
                    ON p.project_id = pm.project_id
               GROUP BY
                    p.project_id,
                    p.project_name,
                    p.description,
                    p.owner_id,
                    u.first_name,
                    u.last_name
               ORDER BY p.project_name;
               '''
          )
          shared_projects = cursor.fetchall()

     return render_template('admin_projects.html', shared_projects=shared_projects)

# Change owner.
@app.route('/admin/projects/<int:project_id>', methods=['GET', 'POST'])
def admin_project(project_id):
     # User must be logged in.
     if 'loggedin' not in session:
          return redirect(url_for('login'))

     # Only admins can manage shared projects.
     elif session['user_role'] != 'admin':
          return render_template('access_denied.html'), 403

     # Retrieve the shared project reusing the code.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               SELECT
                    p.project_id,
                    p.project_name,
                    p.description,
                    p.owner_id,
                    u.first_name AS owner_first_name,
                    u.last_name AS owner_last_name
               FROM projects AS p
               JOIN users AS u
                    ON p.owner_id = u.user_id
               WHERE p.project_id = %s
               AND EXISTS (
                    SELECT 1
                    FROM project_members AS pm
                    WHERE pm.project_id = p.project_id
               );
               ''',
               (project_id,)
          )
          project = cursor.fetchone()

     if project is None:
          flash('Shared project not found.', 'danger')
          return redirect(url_for('admin_projects'))

     # Find users who are allowed to own shared projects staff/admin.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               SELECT user_id, email, first_name, last_name, user_role
               FROM users
               WHERE user_role IN ('staff', 'admin')
               ORDER BY first_name, last_name;
               '''
          )
          possible_owners = cursor.fetchall()
     # Validate the information admin typed for safety checks.
     if request.method == 'POST':
          new_owner_id_value = request.form.get('new_owner_id', '')

          # Ensure the submitted ID is a valid integer.
          try:
               new_owner_id = int(new_owner_id_value)
          except ValueError:
               flash('Please select a valid owner.', 'danger')
               return redirect(url_for('admin_project', project_id=project_id))

          # Confirm the selected user is staff or admin.
          with db.get_cursor() as cursor:
               cursor.execute(
                    '''
                    SELECT user_id
                    FROM users
                    WHERE user_id = %s
                    AND user_role IN ('staff', 'admin');
                    ''',
                    (new_owner_id,)
               )
               new_owner = cursor.fetchone()

          if new_owner is None:
               flash('The new owner must be a staff or admin user.', 'danger')
               return redirect(url_for('admin_project', project_id=project_id))

          if new_owner_id == project['owner_id']:
               flash('This user is already the project owner.', 'info')
               return redirect(url_for('admin_project', project_id=project_id))

          # Ensure the new owner does not already have a project
          # with the same name.
          with db.get_cursor() as cursor:
               cursor.execute(
                    '''
                    SELECT project_id
                    FROM projects
                    WHERE owner_id = %s
                    AND project_name = %s
                    AND project_id != %s;
                    ''',
                    (
                         new_owner_id,
                         project['project_name'],
                         project_id
                    )
               )
               conflicting_project = cursor.fetchone()

          if conflicting_project is not None:
               flash('The selected user already owns a project with this name.', 'danger')
               return redirect(url_for('admin_project', project_id=project_id))

          # Change the project owner.
          with db.get_cursor() as cursor:
               cursor.execute(
                    '''
                    UPDATE projects
                    SET owner_id = %s
                    WHERE project_id = %s;
                    ''',
                    (new_owner_id, project_id)
               )

               # The owner should not also appear as a project member.
               cursor.execute(
                    '''
                    DELETE FROM project_members
                    WHERE project_id = %s
                    AND user_id = %s;
                    ''',
                    (project_id, new_owner_id)
               )

          flash('Project owner changed successfully.', 'success')
          return redirect(url_for('admin_projects'))

     return render_template('admin_project.html', project=project, possible_owners=possible_owners)

# Delete shared project.
@app.route('/admin/projects/<int:project_id>/delete', methods=['POST'])
def admin_delete_project(project_id):
     # User must be logged in.
     if 'loggedin' not in session:
          return redirect(url_for('login'))

     # Only admins can delete shared projects.
     elif session['user_role'] != 'admin':
          return render_template('access_denied.html'), 403

     # Delete only if the project is currently shared.
     with db.get_cursor() as cursor:
          cursor.execute(
               '''
               DELETE FROM projects
               WHERE project_id = %s
               AND EXISTS (
                    SELECT 1
                    FROM project_members
                    WHERE project_members.project_id =
                         projects.project_id
               )
               RETURNING project_id;
               ''',
               (project_id,)
          )
          deleted_project = cursor.fetchone()

     if deleted_project is None:
          flash('Shared project not found.', 'danger')
          return redirect(url_for('admin_projects'))

     flash('Shared project deleted successfully.', 'success')
     return redirect(url_for('admin_projects'))
