# LU-TODO

Individual Project for COMP639 at Lincoln University.

## Running Locally

Instructions will be added during development.

## Database Setup

Instructions will be added during development.

### Development progress

* Login done
* Sign-up done
* Profile page and management done
* Project management done
* Task function done
* Project share Done

* Admin
- View all users
- search users
- view user profile
- change user role
- change user status
- delete user
- view all shared project and change owner
- delete shared project

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
I was suggested to import pathlib, uuid and werkzug.utils first, and allow the extensions of types of pictures. And I was suggested to build a static file for the future profile pictures. After that, I was suggested to check the index to see if is accepted and if so, a random number index should be generated for the following use.


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
- How can list all the projects?
- Can you teach me the sql language here for listing all the projects?


* How it is used?
I was suggested to list all projects by checking two situations: projects that I own and projects that other users have shared with me. I use JOIN users to get the project owner’s name, and LEFT JOIN project_members to connect projects with their members. Then I use WHERE with OR to keep a project when I am either its owner or one of its members. Since one project may have multiple members and appear more than once after joining the tables, I use DISTINCT to display each project only once.

