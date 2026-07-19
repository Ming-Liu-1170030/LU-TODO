CREATE TYPE user_role AS ENUM ('student', 'staff', 'admin');
CREATE TYPE user_status AS ENUM ('active', 'inactive');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high');
CREATE TABLE users (
  user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  password_hash TEXT NOT NULL,
  email VARCHAR(254) NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  position TEXT,
  profile_picture TEXT,
  user_role user_role NOT NULL,
  status user_status NOT NULL
);
CREATE TABLE projects (
  project_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  project_name TEXT NOT NULL,
  description TEXT,
  UNIQUE (owner_id, project_name)
);
CREATE TABLE tasks (
  task_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  task_name TEXT NOT NULL,
  description TEXT,
  priority task_priority NOT NULL,
  due_date DATE,
  is_complete BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE project_members (
  project_id INTEGER NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  PRIMARY KEY (project_id, user_id)
);