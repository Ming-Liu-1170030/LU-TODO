import random
from datetime import date, timedelta
from pathlib import Path

from flask import Flask
from flask_bcrypt import Bcrypt


app = Flask(__name__) # Create a temporary flask app.
bcrypt = Bcrypt(app) # Connect this password tool into flask app.
random.seed(639) # Using course number 639 as random seeds.
# A list for 
users = []
# Generate 50 students with their emails and roles.
for number in range(1, 51):
    users.append({
        'email': f'student{number:02d}@lincolnuni.ac.nz',
        'first_name': f'Student{number:02d}',
        'last_name': 'Test',
        'position': 'Student',
        'password': f'Student{number:02d}!Pass',
        'user_role': 'student',
        'status': 'active'
    })
# Generate 10 staff with their emails and roles.
for number in range(1, 11):
    users.append({
        'email': f'staff{number:02d}@lincoln.ac.nz',
        'first_name': f'Staff{number:02d}',
        'last_name': 'Test',
        'position': 'Lecturer',
        'password': f'Staff{number:02d}!Pass',
        'user_role': 'staff',
        'status': 'active'
    })
# Generate 2 admins with their emails and roles.
for number in range(1, 3):
    users.append({
        'email': f'admin{number:02d}@lincoln.ac.nz',
        'first_name': f'Admin{number:02d}',
        'last_name': 'Test',
        'position': 'Administrator',
        'password': f'Admin{number:02d}!Pass',
        'user_role': 'admin',
        'status': 'active'
    })
print(f'Generated {len(users)} users.')

# Using for loop to create password hash for all users in list.
for user in users:
    user['password_hash'] = (
        bcrypt.generate_password_hash(user['password']).decode()
    )
print('Password hashes generated.')

# Using for loop to generate 100 projects into the project list.
projects = []
for number in range(1, 101):
    owner = users[(number - 1) % len(users)]

    projects.append({
        'project_name': f'Project {number:03d}',
        'description': f'Test description for Project {number:03d}.',
        'owner_email': owner['email']
    })

print(f'Generated {len(projects)} projects.')

# Generate 500 tasks.
tasks = []
priorities = ('low', 'medium', 'high')
today = date.today()

for project in projects:
    for task_number in range(1, 6): # For each project generate 5 tasks, 500 totally.
        overall_number = len(tasks) + 1

        if overall_number % 5 == 0: # For each fifth one, no due_date is set.
            due_date = None
        else:
            due_date = random.choice([None, today + timedelta(days=random.randint(-30, 30))])

        tasks.append({
            'task_name': f'Task {overall_number:03d}',
            'description': (f'Test description for Task {overall_number:03d}.'),
            'priority': random.choice(priorities),
            'due_date': due_date,
            'is_complete': random.choice([True, False]),
            'project_name': project['project_name'],
            'owner_email': project['owner_email']
        })

print(f'Generated {len(tasks)} tasks.')

# Generate membership.
memberships = []
shareable_projects = []
student_members = []

# Get all the project owner email.
for project in projects:
    owner_email = project['owner_email']
# For staff and admin who can share projects, get their shared projects.
    if (owner_email.startswith('staff') or owner_email.startswith('admin')):
        shareable_projects.append(project)
# Get all the student as memebers.
for user in users:
    if user['user_role'] == 'student':
        student_members.append(user)

# Assign all the sharable projects to students.
for project in shareable_projects:
    for member in student_members:
        memberships.append({
            'project_name': project['project_name'],
            'owner_email': project['owner_email'],
            'member_email': member['email']
        })

        if len(memberships) == 100:
            break

    if len(memberships) == 100:
        break

print(f'Generated {len(memberships)} memberships.')

# Ensure sql could read the generation scripts.
def sql_value(value):
    if value is None:
        return 'NULL'

    if isinstance(value, bool):
        if value:
            return 'TRUE'
        return 'FALSE'

    if isinstance(value, date):
        return f"'{value.isoformat()}'"

    escaped_value = str(value).replace("'", "''")
    return f"'{escaped_value}'"

sql_lines = [
    '-- Generated test data for LU-TODO.',
    'BEGIN;',
    (
        'TRUNCATE TABLE project_members, tasks, projects, users '
        'RESTART IDENTITY CASCADE;'
    ),
    ''
]

for user in users:
    sql_lines.append(
        'INSERT INTO users '
        '(password_hash, email, first_name, last_name, position, '
        'profile_picture, user_role, status) VALUES ('
        f"{sql_value(user['password_hash'])}, "
        f"{sql_value(user['email'])}, "
        f"{sql_value(user['first_name'])}, "
        f"{sql_value(user['last_name'])}, "
        f"{sql_value(user['position'])}, "
        f"{sql_value(None)}, "
        f"{sql_value(user['user_role'])}, "
        f"{sql_value(user['status'])}"
        ');'
    )

sql_lines.append('')

for project in projects:
    sql_lines.append(
        'INSERT INTO projects '
        '(owner_id, project_name, description) VALUES ('
        '(SELECT user_id FROM users WHERE email = '
        f"{sql_value(project['owner_email'])}), "
        f"{sql_value(project['project_name'])}, "
        f"{sql_value(project['description'])}"
        ');'
    )

sql_lines.append('')

for task in tasks:
    sql_lines.append(
        'INSERT INTO tasks '
        '(project_id, task_name, description, priority, due_date, '
        'is_complete) VALUES ('
        '('
        'SELECT p.project_id '
        'FROM projects AS p '
        'JOIN users AS u ON p.owner_id = u.user_id '
        f"WHERE p.project_name = {sql_value(task['project_name'])} "
        f"AND u.email = {sql_value(task['owner_email'])}"
        '), '
        f"{sql_value(task['task_name'])}, "
        f"{sql_value(task['description'])}, "
        f"{sql_value(task['priority'])}, "
        f"{sql_value(task['due_date'])}, "
        f"{sql_value(task['is_complete'])}"
        ');'
    )

sql_lines.append('')

for membership in memberships:
    sql_lines.append(
        'INSERT INTO project_members (project_id, user_id) VALUES ('
        '('
        'SELECT p.project_id '
        'FROM projects AS p '
        'JOIN users AS u ON p.owner_id = u.user_id '
        f"WHERE p.project_name = "
        f"{sql_value(membership['project_name'])} "
        f"AND u.email = {sql_value(membership['owner_email'])}"
        '), '
        '('
        'SELECT user_id FROM users '
        f"WHERE email = {sql_value(membership['member_email'])}"
        ')'
        ');'
    )

sql_lines.append('')
sql_lines.append('COMMIT;')

output_path = Path(__file__).with_name('populate_database.sql')

output_path.write_text('\n'.join(sql_lines) + '\n', encoding='utf-8')

print(f'Created {output_path.name}.')