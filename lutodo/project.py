

from asyncio import tasks
import re


from lutodo import app
from lutodo import db
from flask import flash, redirect, render_template, request, session, url_for


# Create project route and reuse code
@app.route('/projects')
def projects():
    if 'loggedin' not in session:
        return redirect(url_for('login'))

# Fetch all and list the projects
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id, project_name, description
            FROM projects
            WHERE owner_id = %s
            ORDER BY project_name
            ''',
            (
                session['user_id'],
            )
        )
        project_list = cursor.fetchall()

    return render_template('projects.html', projects=project_list)

# Create 'create project' route
@app.route('/projects/create', methods=['POST'])
def create_project():
    if 'loggedin' not in session:
        return redirect(url_for('login'))


    project_name = request.form['project_name'].strip()
    description = request.form['description'].strip()
    # Check if project input is empty and existing project
    if not project_name:
        flash('Project name cannot be empty.', 'danger')
        return redirect(url_for('projects'))
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id
            FROM projects
            WHERE owner_id = %s AND project_name = %s;
            ''',
            (session['user_id'], project_name)
        )
        existing_project = cursor.fetchone()

        if existing_project is not None:
            flash('You already have a project with this name', 'danger')
            return redirect(url_for('projects'))

        # Save the project and its description that passed the check
        with db.get_cursor() as cursor:
            cursor.execute(
                '''
                INSERT INTO projects(owner_id, project_name, description)
                VALUES(%s, %s, %s)
                ''',
                (
                    session['user_id'],
                    project_name,
                    description or None
                )
            )
        flash('Project created successfully.', 'success')

        return redirect(url_for('projects'))

# Edit project using the project_id
@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
        if 'loggedin' not in session:
            return redirect(url_for('login'))

        # Select the project that will be edited
        with db.get_cursor() as cursor:
            cursor.execute(
                '''
                SELECT project_id, project_name, description
                FROM projects
                WHERE project_id = %s AND owner_id  = %s;
                ''',
                (project_id, session['user_id'])
            )
            project = cursor.fetchone()

        # Check if project is none.
        if project is None:
            flash('Project not found.', 'danger')
            return redirect(url_for('projects'))

        if request.method == 'GET':
            return render_template('edit_project.html', project=project)
        
        # Validate edited project to ensure it is not empty.
        if request.method == 'POST':
            project_name = request.form['project_name'].strip()
            description = request.form['description'].strip()

            if not project_name:
                flash('Project name cannot be empty', 'danger')
                # Render edit page
                return render_template('edit_project.html', project=project)
            
            # Check db to ensure edited project has unique name
            with db.get_cursor() as cursor:
                cursor.execute(
                    '''
                    SELECT project_id
                    FROM projects
                    WHERE owner_id = %s AND project_name = %s AND project_id<> %s;
                    ''',
                    (session['user_id'], project_name, project_id)
                    )
                existing_project = cursor.fetchone()

            if existing_project is not None:
                flash('You already have a project with this name', 'danger')
                return redirect(url_for('projects'))

            # Save the project and its description that passed the check
            with db.get_cursor() as cursor:
                    cursor.execute(
                    '''
                    UPDATE projects
                    SET project_name = %s,
                        description = %s
                    WHERE project_id = %s AND owner_id = %s;
                    ''',
                    (
                        project_name,
                        description or None,
                        project_id,
                        session['user_id']
                        )
                    )
            flash('Project edited successfully.', 'success')
            return redirect(url_for('projects'))

# Delete project route.
@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    # Delete projects in dd.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM projects
            WHERE project_id = %s AND owner_id = %s RETURNING project_id;           
            ''',
            ( project_id, session['user_id'])
                )
        deleted_project = cursor.fetchone()

    if deleted_project is None:
        flash('Project not found or you do not have permission.', 'danger')
    else:
        flash('Project deleted successfully.', 'success')
    return redirect(url_for('projects'))

# View the project
@app.route('/projects/<int:project_id>')
def view_project(project_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT project_id, project_name, description, owner_id
            FROM projects
            WHERE owner_id = %s AND project_id = %s;
            ''',
            (session['user_id'], project_id)
        )
        project = cursor.fetchone()
    if project is None:
        flash('Project not found or you do not have permission.', 'danger')
        return redirect(url_for('projects'))

    # View the tasks
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT task_id, task_name, description, priority, due_date, is_complete,
                CASE
                    WHEN due_date IS NOT NULL
                        AND due_date < CURRENT_DATE
                        AND is_complete = FALSE
                    THEN TRUE
                    ELSE FALSE
                END AS is_overdue 
            FROM tasks
            WHERE project_id = %s
            ORDER BY task_id;
            ''',
            (project_id,)
        )
        tasks = cursor.fetchall()
    return render_template('project.html', project=project, tasks=tasks)

        
                            

        
        


