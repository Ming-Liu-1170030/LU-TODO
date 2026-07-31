

from lutodo import app, user
from lutodo import db
from flask import flash, request, session, url_for, render_template, redirect, flash


@app.route('/projects/<int:project_id>/members/add', methods=['POST'])
def add_project_member(project_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    # Check if user if allowed to add memebrs.
    if session['user_role'] not in ['staff', 'admin']:
        return render_template('access_denied.html'), 403
    # Check if the project belongs to the user resuing the code in task.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id
            FROM projects
            WHERE project_id = %s AND owner_id = %s;
            ''',
            (
                project_id, session['user_id']
            )
        )
        project = cursor.fetchone()
    if project is None:
        flash('Project not found or you do not have permission.', 'danger')
        return redirect(url_for('projects'))

    # Request the member email that is to be added user types in.
    member_email = request.form['member_email'].strip().lower()

    if not member_email:
        flash('Please enter member email address.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))

    # Find and fetch the member id using email in db.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT user_id
            FROM users
            WHERE email = %s;
            ''',
            (member_email,)
        )
        member = cursor.fetchone()

    if member is None:
        flash('No user was found with this email addrss.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))
    # Double-check to make sure user do not add themselves.
    if member['user_id'] == session['user_id']:
        flash('You cannot add yourself as a project member.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))

    # Check in the db to make sure the member is not already member of project.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id
            FROM project_members
            WHERE project_id = %s AND user_id =%s;
            ''',
            (project_id, member['user_id'])
        )
        existing_member = cursor.fetchone()
    if existing_member is not None:
        flash('You have already added this user.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))

    # Insert the member that passed check into project_members.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO project_members (project_id, user_id)
            VALUES (%s, %s);
            ''',
            (project_id, member['user_id'])
        )
    flash('Mmebers added successfully!', 'success')
    return redirect(url_for('view_project', project_id=project_id))

# Remove a member from a project.
@app.route('/projects/<int:project_id>/members/<int:member_id>/remove',methods=['POST'])
def remove_project_member(project_id, member_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))

    # Make sure only staff and admin users can remove project members reusing the code.
    if session['user_role'] not in ('staff', 'admin'):
        return render_template('access_denied.html'), 403

    # Check that the current user owns this project.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id
            FROM projects
            WHERE project_id = %s AND owner_id = %s;
            ''',
            (project_id, session['user_id'])
        )
        project = cursor.fetchone()

    if project is None:
        flash('Project not found or you do not have permission.','danger')
        return redirect(url_for('projects'))

    # Delete only the member relationship but not member themselevs.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM project_members
            WHERE project_id = %s AND user_id = %s
            RETURNING user_id;
            ''',
            (project_id, member_id)
        )
        removed_member = cursor.fetchone()

    if removed_member is None:
        flash('Project member not found.', 'danger')
    else:
        flash('Member removed successfully.', 'success')

    return redirect(url_for('view_project', project_id=project_id))


    


    
        