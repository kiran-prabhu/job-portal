# Job Portal

A Flask-based job portal and recruitment management system built with Python and PostgreSQL.

The application allows companies and jobs to be managed, applicants to apply for jobs, and applications to be tracked through different recruitment stages.

## Features

### Companies

* Add companies
* View company details
* Edit company information
* Delete companies
* Search companies by name or location
* Prevent deletion of companies that have jobs

### Jobs

* Add jobs
* View job details
* Edit jobs
* Delete jobs
* Search jobs by title or company
* Apply for jobs
* Prevent deletion of jobs that have applications

### Applications

* Submit job applications
* View application details
* Search applications by applicant name or email
* Filter applications by status
* Update application status
* Delete applications

Supported application statuses:

* Applied
* Shortlisted
* Interview
* Rejected
* Hired

### Dashboard

* Company count
* Job count
* Application count
* Application status statistics
* Recent applications

### REST-style API

The application provides JSON endpoints for:

* Companies
* Jobs
* Applications

API 404 responses are returned as JSON.

## Tech Stack

* Python
* Flask
* PostgreSQL
* Psycopg
* HTML
* CSS
* Jinja2
* python-dotenv

## Database Structure

The application uses three related PostgreSQL tables:

```text
companies
    │
    │ 1 → many
    ▼
jobs
    │
    │ 1 → many
    ▼
applications
```

### companies

| Column   | Description      |
| -------- | ---------------- |
| id       | Primary key      |
| name     | Company name     |
| location | Company location |

### jobs

| Column     | Description                       |
| ---------- | --------------------------------- |
| id         | Primary key                       |
| company_id | Foreign key referencing companies |
| title      | Job title                         |
| location   | Job location                      |

### applications

| Column         | Description                  |
| -------------- | ---------------------------- |
| id             | Primary key                  |
| job_id         | Foreign key referencing jobs |
| applicant_name | Applicant name               |
| email          | Applicant email              |
| status         | Application status           |

## Project Structure

```text
job-portal/
├── app.py
├── requirements.txt
├── .env
├── .gitignore
├── static/
│   └── style.css
└── templates/
    ├── home.html
    ├── companies.html
    ├── company_details.html
    ├── add_company.html
    ├── edit_company.html
    ├── jobs.html
    ├── job_details.html
    ├── add_job.html
    ├── edit_job.html
    ├── applications.html
    ├── application_details.html
    └── apply.html
```

## Requirements

* Python 3
* PostgreSQL
* pip
* A virtual environment

## Installation

Clone the repository:

```bash
git clone <repository-url>
cd job-portal
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Database Setup

Create a PostgreSQL database named:

```text
job_portal
```

Create the required tables:

```sql
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    title TEXT NOT NULL,
    location TEXT NOT NULL
);

CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    applicant_name TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL
);
```

## Environment Variables

Create a `.env` file in the project root:

```text
DB_NAME=job_portal
DB_USER=postgres
DB_PASSWORD=your_postgresql_password
DB_HOST=localhost
```

Do not commit `.env` to GitHub.

The `.env` file is already included in `.gitignore`.

## Running the Application

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Start the Flask application:

```bash
python app.py
```

Open the application in your browser:

```text
http://127.0.0.1:5000/
```

## API Endpoints

### Companies

```text
GET /api/companies
```

Returns all companies as JSON.

### Jobs

```text
GET /api/jobs
```

Returns all jobs with their associated company names as JSON.

### Applications

```text
GET /api/applications
```

Returns all applications with their associated job and company information as JSON.

### API 404

Unknown API routes return:

```json
{
    "error": "Resource not found."
}
```

## What I Learned

This project was built to practice:

* Flask routing
* HTML forms and POST requests
* Jinja templates
* PostgreSQL
* SQL CRUD operations
* Primary keys and foreign keys
* Relational database design
* SQL JOIN operations
* Server-side validation
* Search and filtering
* REST-style JSON APIs
* Environment variables
* `.gitignore`
* Python virtual environments
* Basic web application styling
* Git and GitHub workflow

## Future Improvements

Possible future improvements include:

* User authentication
* Admin and applicant accounts
* Pagination
* More advanced application filtering
* File upload for resumes
* Email notifications
* REST API POST/PUT/DELETE endpoints
* Improved UI and responsive design