# LU-TODO

Individual Project for COMP639 at Lincoln University.
It is a Flask and PostgreSQL web application for managing projects and tasks. Users can register and log in as students or staff. They can manage their profiles, create projects and tasks, and track task priority, completion and overdue status. Staff and administrators can share projects with other users. Administrators can also manage users and shared projects.

## Running Locally

- Python 3
- PostgreSQL
- The Python packages listed in 'requirements.txt'

## Setup

1. Clone the repository and open the project folder.

2. Create a Python virtual environment:

3. Install dependencies: ```powershell pip install... -r requirements.txt

## Database Setup

1. Create an empty PostgreSQL database for LU-TODO.

2. Update lutodo/connect.py so that it connects to this database.

3. Run create_database.sql against the database. This creates the PostgreSQL types, tables, primary keys, foreign keys and other constraints required by the application.

4. Run populate_database.sql against the same database. This clears existing table data and inserts the required test data:

### Features

* Login 
* Sign-up 
* Profile page and management 
* Project management 
* Task function 
* Project share 
* Admin management

## Navigation Note

## Navigation Note

When I polish my nav-bar UI, I realized that I placed the project list and project creation form together on the same Projects page. Therefore, the "View Projects" and "Create Project" options in the navigation menu lead to the same page, where users can view existing projects and create a new one. This design does not affect any project functionality.

## GenAI Acknowledgement

I have used OpenAI Codex during the development and the details are documented as follows:

### Date used: 26 July 2026

* 1. Prompts:
- Help me check my 'signup' html page and show me the errors.
- What does multipart/form-data mean?


* Other input provided: 
And I upload my written signup.html to Codex.

* How it is used?
A suggestion of missing 'multipart/form-data' is provided by Codex, and I ask what that means and hear back and know that helps to submit image profile picture then I 
add it to my signup.html page.


* 2. Prompts:
- How can I deal with the profile_picture users uploaded?


* Other input provided: 
How can I save the validated pictures into my static folder?


* How it is used?
I was suggested to import pathlib, uuid and werkzug.utils first, and allow the extensions of types of pictures. And I was suggested to build a static file for the future profile pictures. After that, I checked the index to see if is accepted and if so, a random number index should be generated for the following use.


### Date used: 27 July 2026

* 1. Prompts:
- How can I write responsive 'edit' function?

* Other input provided: 
- How can I set alert when edit successfully?

* How it is used?
I was suggested to use JavaScript. At first, id should be added into the html button so that JavaScript can find it. Then using id to help JavaScript find all the buttons and save into variables. And when JavaScript identifies the click, responsive editing function will be open and available, save and cancel will pop up.
I was suggested to import flash and use Jinja and HTML language in the profile.html page to let the message pop up.

### Date used: 31 July 2026

* 1. Prompts:
- How can I delete projects and tasks?
- Why do I need to authorize if the project or task belonging to someone?


* How it is used?
I was suggested to add authorization checks before deleting a task. First, Flask checks whether the user is logged in. Then, it uses the project_id and the current user’s user_id from the session to confirm that the user owns the project. After authorization passes, Flask uses both the task_id and project_id to delete the correct task. This prevents users from changing IDs in the URL and deleting tasks that they do not own.

* 2. Prompts:
- How can I set overdue for tasks?

* How it is used?
I was suggested to use CASE in the SQL query when Flask gets the task information. If the due date is not empty, the date is earlier than the current date, and the task is not complete, a temporary is_overdue value will be set to true. Then I use Jinja in the project.html page to check task.is_overdue and display the overdue status.

### Date used: 1 August 2026

* 1. Prompts:
- How can I list all the projects?
- Can you teach me the sql language here for listing all the projects?


* How it is used?
I was suggested to list all projects by checking two situations: projects that I own and projects that other users have shared with me. I use JOIN users to get the project owner’s name, and LEFT JOIN project_members to connect projects with their members. Then I use WHERE with OR to keep a project when I am either its owner or one of its members. Since one project may have multiple members and appear more than once after joining the tables, I use DISTINCT to display each project only once.

### Date used: 1 August 2026

* 1. Prompts:
- How can I change owner as an admin, tell me the logic steps?
- What does the sql relationships look like? And how do I connect them to retrieve?



* How it is used?
I first create a new route with project ID to identify which shared project the admin selects. The backend checks login, admin role, and whether the project is really shared. Then all staff and admin users are retrieved from the database and sent to HTML as a dropdown list. When admin selects a new owner and submits, Flask receives the new owner ID, checks it is valid and not a student, and makes sure this user does not already own a project with the same name. After all checks pass, the project owner_id is updated in the database. The new owner is also removed from the member table because an owner should not also be a member.

And I was suggested to start from the projects table and give it a short name p. Then I connect projects.owner_id with users.user_id, because I need to find the first name and last name of the project owner. After that, I connect projects.project_id with project_members.project_id, because I need to find which member records belong to each project. Each member creates one matching row, so I use COUNT(pm.user_id) to calculate how many members each project has. I use GROUP BY to put the rows belonging to the same project back together, then use ORDER BY to display the projects in project-name order. Because this uses a normal JOIN with project_members, projects without members are not included.

* 1. Prompts:
- How can I generate all test user data?
- What about the random projects, tasks, and shareable projects?
- Help me generate the code to generate the random projects, tasks, and projects.



* How it is used?

Codex suggested and generated the initial structure of 'generate_test_data.py'. The script uses Python lists, dictionaries, loops, random values and Flask-Bcrypt to generate users, password hashes, projects, tasks and memberships. It also converts the generated data into SQL statements and writes them into 'populate_database.sql'.

I asked Codex to explain the code and simplify some parts that I found difficult, including priority, due-date, completion-status and membership generation. I reviewed and modified the code, ran the script, checked the generated record counts in PostgreSQL, and tested the generated student, staff and admin accounts in the application.


### Date used: 2 August 2026

* 1. Prompts:
- How can I change all the app colour, and apply hover display to all the pages?
- How can I put admin and project function respectively in the nav bar and display them in a drop-down way?


* How it is used?
I was suggested by Codex to create a shared app.css file and was given a basic CSS frame so that I could choose the colours myself. I linked this file after Bootstrap in the base template and other standalone pages, so the same colours can be applied across the whole app. I also added CSS :hover, :focus, and :active rules for buttons, links, and navigation dropdown menus. 

And I was suggested by Codex to use Bootstrap dropdown menus in userbase.html. I grouped the project functions under a Projects menu and the administration functions under an Admin menu. Jinja checks session['user_role'] so the Admin dropdown is only displayed to admin users. I also added a CSS hover rule so the dropdown menu opens when the mouse moves over it on desktop, while it can still be opened by clicking on mobile.

* 2. Prompts:
- I would like to polish my home page and login page, for login page, I want the whole page to be separated into two parts by a vertical bar? How can I do it?

* How it is used?
I was suggested by Codex to use CSS to divide the login page into two equal sections using grid-template-columns: 1fr 1fr. I placed the login form on the white left side and the LU-TODO logo and introduction on the dark blue right side. I also added a media query so the two sections change into a vertical layout on mobile devices. For the home page, I reused the same dark blue, white, button, and text styles to keep the design consistent across the app.