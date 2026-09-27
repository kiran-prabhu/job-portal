from flask import Flask, render_template, request, redirect
import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


def get_db_connection():
    connection = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST")
    )
    return connection


@app.route("/")
def home():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM companies;")
    company_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs;")
    job_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications;")
    application_count = cursor.fetchone()[0]

    cursor.execute("""
    SELECT status, COUNT(*)
    FROM applications
    GROUP BY status;
    """)

    status_counts = cursor.fetchall()

    cursor.execute("""
        SELECT
            applications.id,
            applications.applicant_name,
            jobs.title,
            companies.name,
            applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN companies ON jobs.company_id = companies.id
        ORDER BY applications.id DESC
        LIMIT 5;
    """)

    recent_applications = cursor.fetchall()
    
    cursor.close()
    connection.close()

    return render_template(
        "home.html",
        company_count=company_count,
        job_count=job_count,
        application_count=application_count,
        status_counts=status_counts,
        recent_applications=recent_applications
    )

@app.route("/companies")
def companies():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM companies
        WHERE name ILIKE %s
        OR location ILIKE %s;
    """, (f"%{search}%", f"%{search}%"))

    companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("companies.html", companies=companies)

@app.route("/companies/<int:company_id>")
def company_details(company_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, location
        FROM companies
        WHERE id = %s;
    """, (company_id,))

    company = cursor.fetchone()

    cursor.execute("""
        SELECT id, title, location
        FROM jobs
        WHERE company_id = %s;
    """, (company_id,))

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    if company is None:
        return "Company not found.", 404

    return render_template("company_details.html", company=company, jobs=jobs)

@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, location
        FROM companies
        WHERE id = %s;
    """, (company_id,))

    company = cursor.fetchone()

    if company is None:
        cursor.close()
        connection.close()
        return "Company not found.", 404

    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()

        if not name or not location:
            cursor.close()
            connection.close()
            return "Company name and location are required.", 400

        cursor.execute("""
            UPDATE companies
            SET name = %s, location = %s
            WHERE id = %s;
        """, (name, location, company_id))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(f"/companies/{company_id}")

    cursor.close()
    connection.close()

    return render_template("edit_company.html", company=company)

@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM jobs WHERE company_id = %s LIMIT 1;",
        (company_id,)
    )

    job = cursor.fetchone()

    if job is not None:
        cursor.close()
        connection.close()
        return "Cannot delete company because it has jobs.", 400

    cursor.execute(
        "DELETE FROM companies WHERE id = %s;",
        (company_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/companies")

@app.route("/companies/add", methods=["GET", "POST"])
def add_company():
    if request.method == "POST":
        name = request.form["name"].strip()
        location = request.form["location"].strip()

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO companies (name, location) VALUES (%s, %s);",
            (name, location)
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/companies")

    return render_template("add_company.html")

@app.route("/jobs/add", methods=["GET", "POST"])
def add_job():
    if request.method == "POST":
        company_id = request.form["company_id"].strip()
        title = request.form["title"].strip()
        location = request.form["location"].strip()

        if not company_id or not title or not location:
            return "All fields are required.", 400

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id FROM companies WHERE id = %s;",
            (company_id,)
        )

        company = cursor.fetchone()

        if company is None:
            cursor.close()
            connection.close()
            return "Company not found.", 404

        cursor.execute(
            """
            INSERT INTO jobs (company_id, title, location)
            VALUES (%s, %s, %s);
            """,
            (company_id, title, location)
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/jobs")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM companies;")
    companies = cursor.fetchall()

    if not companies:
        cursor.close()
        connection.close()
        return "Please add a company before adding a job.", 400

    cursor.close()
    connection.close()

    return render_template("add_job.html", companies=companies)

@app.route("/applications/<int:application_id>")
def application_details(application_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            applications.id,
            applications.applicant_name,
            applications.email,
            jobs.title,
            companies.name,
            applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN companies ON jobs.company_id = companies.id
        WHERE applications.id = %s;
    """, (application_id,))

    application = cursor.fetchone()

    cursor.close()
    connection.close()

    if application is None:
        return "Application not found.", 404

    return render_template("application_details.html", application=application)

@app.route("/applications/<int:application_id>/status", methods=["POST"])
def update_application_status(application_id):
    status = request.form["status"].strip()

    allowed_statuses = ["Applied", "Shortlisted", "Interview", "Rejected", "Hired"]

    if status not in allowed_statuses:
        return "Invalid status.", 400

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE applications
        SET status = %s
        WHERE id = %s;
        """,
        (status, application_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(f"/applications/{application_id}")

@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM applications WHERE id = %s;",
        (application_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/applications")

@app.route("/jobs/<int:job_id>")
def job_details(job_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT jobs.id, jobs.title, jobs.location, companies.name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
        WHERE jobs.id = %s;
    """, (job_id,))

    job = cursor.fetchone()

    cursor.close()
    connection.close()

    if job is None:
        return "Job not found.", 404

    return render_template("job_details.html", job=job)

@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def edit_job(job_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, company_id, title, location
        FROM jobs
        WHERE id = %s;
    """, (job_id,))

    job = cursor.fetchone()

    if job is None:
        cursor.close()
        connection.close()
        return "Job not found.", 404

    if request.method == "POST":
        company_id = request.form["company_id"].strip()
        title = request.form["title"].strip()
        location = request.form["location"].strip()

        if not company_id or not title or not location:
            cursor.close()
            connection.close()
            return "All fields are required.", 400

        cursor.execute(
            "SELECT id FROM companies WHERE id = %s;",
            (company_id,)
        )

        company = cursor.fetchone()

        if company is None:
            cursor.close()
            connection.close()
            return "Company not found.", 404

        cursor.execute("""
            UPDATE jobs
            SET company_id = %s, title = %s, location = %s
            WHERE id = %s;
        """, (company_id, title, location, job_id))

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(f"/jobs/{job_id}")

    cursor.execute("SELECT * FROM companies;")
    companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("edit_job.html", job=job, companies=companies)

@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def delete_job(job_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM applications WHERE job_id = %s LIMIT 1;",
        (job_id,)
    )

    application = cursor.fetchone()

    if application is not None:
        cursor.close()
        connection.close()
        return "Cannot delete job because it has applications.", 400

    cursor.execute(
        "DELETE FROM jobs WHERE id = %s;",
        (job_id,)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/jobs")

@app.route("/jobs/<int:job_id>/apply", methods=["GET", "POST"])
def apply_for_job(job_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id FROM jobs WHERE id = %s;",
        (job_id,)
    )

    job = cursor.fetchone()

    if job is None:
        cursor.close()
        connection.close()
        return "Job not found.", 404

    if request.method == "POST":
        applicant_name = request.form["applicant_name"].strip()
        email = request.form["email"].strip()

        if not applicant_name or not email:
            cursor.close()
            connection.close()
            return "Name and email are required.", 400

        if "@" not in email or "." not in email.split("@")[-1]:
            cursor.close()
            connection.close()
            return "Please enter a valid email address.", 400

        cursor.execute(
            """
            INSERT INTO applications (job_id, applicant_name, email, status)
            VALUES (%s, %s, %s, %s);
            """,
            (job_id, applicant_name, email, "Applied")
        )

        connection.commit()
        cursor.close()
        connection.close()

        return redirect("/applications")

    cursor.close()
    connection.close()

    return render_template("apply.html")

@app.route("/jobs")
def jobs():
    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT jobs.title, jobs.location, companies.name, jobs.id
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id
        WHERE jobs.title ILIKE %s
        OR companies.name ILIKE %s;
    """, (f"%{search}%", f"%{search}%"))

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("jobs.html", jobs=jobs)

@app.route("/applications")
def applications():
    status = request.args.get("status", "").strip()
    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            applications.id,
            applications.applicant_name,
            applications.email,
            jobs.title,
            companies.name,
            applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN companies ON jobs.company_id = companies.id
        WHERE (applications.status = %s OR %s = '')
        AND (
            applications.applicant_name ILIKE %s
            OR applications.email ILIKE %s
        );
    """, (status, status, f"%{search}%", f"%{search}%"))

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("applications.html", applications=applications)

@app.route("/api/companies")
def api_companies():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, location
        FROM companies;
    """)

    companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "companies": [
            {
                "id": company[0],
                "name": company[1],
                "location": company[2]
            }
            for company in companies
        ]
    }

@app.route("/api/jobs")
def api_jobs():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            jobs.id,
            jobs.title,
            jobs.location,
            companies.name
        FROM jobs
        JOIN companies ON jobs.company_id = companies.id;
    """)

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "jobs": [
            {
                "id": job[0],
                "title": job[1],
                "location": job[2],
                "company": job[3]
            }
            for job in jobs
        ]
    }

@app.route("/api/applications")
def api_applications():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            applications.id,
            applications.applicant_name,
            applications.email,
            jobs.title,
            companies.name,
            applications.status
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        JOIN companies ON jobs.company_id = companies.id;
    """)

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "applications": [
            {
                "id": application[0],
                "applicant_name": application[1],
                "email": application[2],
                "job": application[3],
                "company": application[4],
                "status": application[5]
            }
            for application in applications
        ]
    }

@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return {"error": "Resource not found."}, 404

    return "Page not found.", 404

if __name__ == "__main__":
    app.run(debug=True)