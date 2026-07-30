

from lutodo import app, project
from lutodo import db
from flask import flash, redirect, render_template, request, session, url_for
from datetime import date

# Create tasks
@app.route('/projects/<int:project_id>/tasks/create', methods = ['POST'])
def create_task(project_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
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

    # Check if the project belong to the current user
    if project is None:
        flash('Project not found or you do not have permission.', 'danger')
        return redirect(url_for('projects'))

    # Get task information that passed checks
    task_name = request.form['task_name'].strip()
    description = request.form['description'].strip()
    priority = request.form['priority'].strip()
    due_date = request.form['due_date'].strip()

    # Validate the task name.
    if not task_name:
        flash('Task name cannot be empty.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))
    # Validate priority
    if priority not in ('low', 'medium', 'high'):
        flash('Please select a valid priority.', 'danger')
        return redirect(url_for('view_project', project_id=project_id))
    # Validate the optional due date
    if due_date:
        try:
            due_date = date.fromisoformat(due_date)
        except ValueError:
            flash('Please enter a valid due date.', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
    else:
        due_date = None

    # Insert the validated information into database.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            INSERT INTO tasks(project_id, task_name, description, priority, due_date)
            VALUES(%s, %s, %s, %s, %s)
            ''',
            (project_id, task_name, description or None, priority, due_date)
        )
        flash('Task created successfully.', 'success')
        return redirect(url_for('view_project', project_id=project_id))

# Edit task
@app.route('/projects/<int:project_id>/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_task(project_id, task_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    # Check if the project belongs to the user.
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
    
    # Fetch task details for check and edit
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            SELECT task_id, task_name, description, priority, due_date, is_complete
            FROM tasks
            WHERE project_id = %s AND task_id = %s;
            ''',
            (
                project_id, task_id
            )
        )
        task = cursor.fetchone()
    if task is None:
        flash('Task not found or you do not have permission', 'danger')
        return redirect(url_for('view_project', project_id=project_id))

    if request.method == 'POST':
        task_name = request.form['task_name'].strip()
        description = request.form['description'].strip()
        priority = request.form['priority'].strip()
        due_date = request.form['due_date'].strip()
        is_complete = 'is_complete' in request.form
        # Validate the task name reusing the code in create_task.
        if not task_name:
            flash('Task name cannot be empty.', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
        # Validate priority
        if priority not in ('low', 'medium', 'high'):
            flash('Please select a valid priority.', 'danger')
            return redirect(url_for('view_project', project_id=project_id))
        # Validate the optional due date
        if due_date:
            try:
                due_date = date.fromisoformat(due_date)
            except ValueError:
                flash('Please enter a valid due date.', 'danger')
                return redirect(url_for('view_project', project_id=project_id))
        else:
            due_date = None

        # Update the db with all passed editing.
        with db.get_cursor() as cursor:
            cursor.execute(
                '''
                UPDATE tasks
                SET task_name = %s, description = %s, priority = %s, due_date = %s, is_complete = %s
                WHERE task_id = %s AND project_id = %s;
                ''',
                (
                    task_name, description or None, priority, due_date, is_complete,
                    task_id, project_id
                )
            )
        flash('Task updated successfully.', 'success')
        return redirect(url_for('view_project', project_id=project_id))
    # Show the details on the page.
    return render_template('edit_task.html', task=task, task_id=task_id, project_id=project_id)

# Delete task.
@app.route('/projects/<int:project_id>/tasks/<int:task_id>/delete', methods = ['POST'])
def delete_task(project_id, task_id):
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    # Check current owner owns project
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
    # Delete task in db.
    with db.get_cursor() as cursor:
        cursor.execute(
            '''
            DELETE FROM tasks
            WHERE task_id = %s AND project_id = %s RETURNING task_id;           
            ''',
            ( task_id, project_id)
                )
        deleted_task = cursor.fetchone()

    if deleted_task is None:
        flash('Project not found.', 'danger')
    else:
        flash('Task deleted successfully.', 'success')
    return redirect(url_for('view_project', project_id=project_id))




        
    


    
    
    
            


