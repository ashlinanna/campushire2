from flask import Flask, render_template, request, redirect, session, flash
from db_config import get_db_connection

app = Flask(__name__)
app.secret_key = "hackathon_secret_key"


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- STUDENT REGISTER ----------------
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        college = request.form['college']
        pin_code = request.form['pin_code']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO students (name, email, password, college, pin_code)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, password, college, pin_code))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Registered Successfully! Please login.")
        return redirect('/student_login')

    return render_template('student_register.html')


# ---------------- STUDENT LOGIN ----------------
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM students
            WHERE LOWER(email) = LOWER(%s)
            AND password = %s
        """, (email, password))

        student = cursor.fetchone()
        print("Student result:", student)

        cursor.close()
        conn.close()

        if student:
            session['student_id'] = student[0]
            session['student_pin'] = student[5]
            return redirect('/view_jobs')
        else:
            flash("Invalid Credentials")

    return render_template('student_login.html')


# ---------------- EMPLOYER REGISTER ----------------
@app.route('/employer_register', methods=['GET', 'POST'])
def employer_register():
    if request.method == 'POST':
        shop_name = request.form['shop_name']
        owner_name = request.form['owner_name']
        email = request.form['email']
        password = request.form['password']
        pin_code = request.form['pin_code']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO employers (shop_name, owner_name, email, password, pin_code)
            VALUES (%s, %s, %s, %s, %s)
        """, (shop_name, owner_name, email, password, pin_code))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Registered Successfully! Please login.")
        return redirect('/employer_login')

    return render_template('employer_register.html')


# ---------------- EMPLOYER LOGIN ----------------
@app.route('/employer_login', methods=['GET', 'POST'])
def employer_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM employers WHERE email = %s AND password = %s",
            (email, password)
        )
        employer = cursor.fetchone()

        cursor.close()
        conn.close()

        if employer:
            session['employer_id'] = employer[0]
            return redirect('/employer_dashboard')
        else:
            flash("Invalid Credentials")

    return render_template('employer_login.html')


# ---------------- EMPLOYER DASHBOARD ----------------
@app.route('/employer_dashboard')
def employer_dashboard():
    if 'employer_id' not in session:
        return redirect('/employer_login')

    return render_template('employer_dashboard.html')


# ---------------- POST JOB ----------------
@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'employer_id' not in session:
        return redirect('/employer_login')

    if request.method == 'POST':
        title = request.form['title']
        salary = request.form['salary']
        timing = request.form['timing']
        description = request.form['description']
        pin_code = request.form['pin_code']

        employer_id = session['employer_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO jobs (employer_id, title, salary, timing, description, pin_code)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (employer_id, title, salary, timing, description, pin_code))
        conn.commit()

        cursor.close()
        conn.close()

        flash("Job Posted Successfully!")
        return redirect('/employer_dashboard')

    return render_template('post_job.html')


# ---------------- VIEW JOBS ----------------
@app.route('/view_jobs')
def view_jobs():
    if 'student_id' not in session:
        return redirect('/student_login')

    conn = get_db_connection()
    cursor = conn.cursor()

    student_id = session['student_id']

    # =========================
    # Fetch All Available Jobs
    # =========================
    cursor.execute("""
        SELECT j.id,
               j.title,
               j.salary,
               j.timing,
               j.description,
               e.shop_name
        FROM jobs j
        JOIN employers e ON j.employer_id = e.id
    """)
    jobs = cursor.fetchall()

    # =========================
    # Fetch Student Applications
    # =========================
    cursor.execute("""
        SELECT a.job_id,
               j.title,
               e.shop_name,
               a.status
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        JOIN employers e ON j.employer_id = e.id
        WHERE a.student_id = %s
    """, (student_id,))

    applications = cursor.fetchall()

    # =========================
    # Create Applied Job ID List
    # =========================
    applied_job_ids = [app[0] for app in applications]

    cursor.close()
    conn.close()

    return render_template(
        "view_jobs.html",
        jobs=jobs,
        applications=applications,
        applied_job_ids=applied_job_ids
    )




# ---------------- APPLY JOB ----------------
@app.route('/apply_job', methods=['POST'])
def apply_job():
    if 'student_id' not in session:
        return redirect('/student_login')

    job_id = request.form['job_id']
    student_id = session['student_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Prevent duplicate applications
    cursor.execute("""
        SELECT * FROM applications
        WHERE student_id = %s AND job_id = %s
    """, (student_id, job_id))

    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO applications (student_id, job_id, status)
            VALUES (%s, %s, 'pending')
        """, (student_id, job_id))
        conn.commit()

    cursor.close()
    conn.close()

    return redirect('/view_jobs')


# ---------------- CANCEL APPLICATION ----------------
@app.route('/cancel_application', methods=['POST'])
def cancel_application():
    if 'student_id' not in session:
        return redirect('/student_login')

    job_id = request.form['job_id']
    student_id = session['student_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM applications
        WHERE student_id = %s AND job_id = %s
    """, (student_id, job_id))
    conn.commit()

    cursor.close()
    conn.close()

    flash("Application Cancelled.")
    return redirect('/view_jobs')


# ---------------- VIEW APPLICANTS ----------------
@app.route('/view_applicants')
def view_applicants():
    if 'employer_id' not in session:
        return redirect('/employer_login')

    employer_id = session['employer_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT applications.id, students.name, students.email,
               jobs.title, applications.status
        FROM applications
        JOIN students ON applications.student_id = students.id
        JOIN jobs ON applications.job_id = jobs.id
        WHERE jobs.employer_id = %s
    """, (employer_id,))

    applicants = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('view_applicants.html', applicants=applicants)


# ---------------- UPDATE STATUS ----------------
@app.route('/update_status', methods=['POST'])
def update_status():
    if 'employer_id' not in session:
        return redirect('/employer_login')

    application_id = request.form['application_id']
    action = request.form['action']  # Approved / Rejected

    conn = get_db_connection()
    cursor = conn.cursor()

    # Update application status
    cursor.execute(
        "UPDATE applications SET status = %s WHERE id = %s",
        (action, application_id)
    )

    # If Approved → Close the job
    if action == "Approved":
        # Get job_id of that application
        cursor.execute(
            "SELECT job_id FROM applications WHERE id = %s",
            (application_id,)
        )
        job_id = cursor.fetchone()[0]

        # Close job
        cursor.execute(
            "UPDATE jobs SET is_open = FALSE WHERE id = %s",
            (job_id,)
        )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/view_applicants')


# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
