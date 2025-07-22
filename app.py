# app.py - Flask backend server for Job Bot
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import os
from werkzeug.utils import secure_filename
import csv
from models import UserProfile, Application
import subprocess
from datetime import datetime, timedelta

# STEP 1: CREATE Flask app
app = Flask(__name__)

# STEP 2: App configurations
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Setup upload folder
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from models import UserProfile, db

    profile = UserProfile.query.filter_by(user_id=current_user.id).first()

    # Load jobs for select options
    jobs = []
    try:
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            jobs = list(reader)
    except Exception:
        jobs = []

    if request.method == 'POST':
        titles = request.form.getlist('title')
        locations = request.form.getlist('location')
        file = request.files.get('resume')

        preferred_titles = ','.join(titles)
        preferred_locations = ','.join(locations)

        filename = profile.resume_filename if profile else None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if profile:
            profile.preferred_title = preferred_titles
            profile.preferred_location = preferred_locations
            profile.resume_filename = filename
        else:
            profile = UserProfile(
                user_id=current_user.id,
                preferred_title=preferred_titles,
                preferred_location=preferred_locations,
                resume_filename=filename
            )
            db.session.add(profile)

        db.session.commit()
        flash("✅ Profile updated successfully!")
        return redirect(url_for('profile'))

    return render_template("profile.html", profile=profile, jobs=jobs)

# STEP 3: Init db and login

db.init_app(app)

# Login Manager Setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

##########################################
# ROUTES
##########################################

@app.route('/')
@login_required
def dashboard():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    matched_jobs = []
    if profile:
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title_match = profile.preferred_title.lower() in row['title'].lower() \
                                if profile.preferred_title else True
                loc_match = profile.preferred_location.lower() in row['company'].lower() \
                                if profile.preferred_location else True
                if title_match or loc_match:
                    matched_jobs.append(row)

    # 🧠 Gather Stats
    user_apps = Application.query.filter_by(user_id=current_user.id).all()
    applied_auto_count = sum(1 for job in user_apps if job.status == 'applied')
    applied_manual_count = sum(1 for job in user_apps if job.status == 'applied_manual')
    applied_total = applied_auto_count + applied_manual_count
    manual_pending_count = sum(1 for job in user_apps if job.status == 'manual')
    now = datetime.utcnow()
    one_week_ago = now - timedelta(days=7)
    applied_this_week = sum(1 for job in user_apps if job.status in ['applied', 'applied_manual'] and job.timestamp > one_week_ago)

    # NEW: Load all jobs and filter for recent ones
    recent_jobs_day, recent_jobs_week = [], []
    one_day_ago = now - timedelta(days=1)
    with open('remoteok_jobs.csv', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for job in reader:
            try:
                job_date = datetime.strptime(job['date'], '%Y-%m-%d')
                if job_date >= one_day_ago:
                    recent_jobs_day.append(job)
                if job_date >= one_week_ago:
                    recent_jobs_week.append(job)
            except Exception:
                continue

    return render_template(
        'dashboard.html',
        jobs=matched_jobs,
        recent_jobs_day=recent_jobs_day,
        recent_jobs_week=recent_jobs_week,
        stats={
            'applied_total': applied_total,
            'applied_this_week': applied_this_week,
            'manual_pending': manual_pending_count
        }
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered, try logging in.", 'warning')
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully. Please log in.", 'success')
        return redirect(url_for('login'))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        print(f"[DEBUG] Checking user: {email}, result: {user}")
        if user:
            print(f"[DEBUG] Stored password: {user.password}")
        if not user or not check_password_hash(user.password, password):
            flash("Invalid login credentials", 'danger')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template("login.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/apply', methods=['POST'])
@login_required
def apply():
    job_link = request.form.get('link')

    if not job_link:
        flash("❌ Invalid job link.")
        return redirect(url_for('dashboard'))

    try:
        # Use the full path to the virtualenv's Python interpreter
        subprocess.run([
            r'C:\Users\sudha\OneDrive\Desktop\Punna Sudha Kalyan\Projects\Job-Bot-Cursor\env\Scripts\python.exe',
            'apply_bot.py',
            job_link
        ], check=True)
        flash(f"✅ Applied to job successfully: {job_link}")
    except subprocess.CalledProcessError as e:
        flash("❌ Failed to apply using bot. Check logs.")

    return redirect(url_for('dashboard'))

@app.route('/batch-apply', methods=['GET', 'POST'])
@login_required
def batch_apply():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    applied_links = set(app.link for app in Application.query.filter_by(user_id=current_user.id).all())
    bot_path = os.path.join(os.getcwd(), 'apply_bot.py')
    python_path = os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe')

    if request.method == 'POST':
        selected_links = request.form.getlist('job_links')
        applied, manual = 0, 0
        jobs_to_apply = []

        # Load all jobs first
        with open("remoteok_jobs.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['link'] in selected_links and row['link'] not in applied_links:
                    jobs_to_apply.append(row)

        for job in jobs_to_apply:
            try:
                result = subprocess.run([python_path, bot_path, job['link']],
                                        capture_output=True, text=True)
                status = 'applied' if result.returncode == 0 else 'manual'
            except:
                status = 'manual'

            app_entry = Application(
                user_id=current_user.id,
                job_title=job['title'],
                company=job['company'],
                link=job['link'],
                status=status
            )
            db.session.add(app_entry)
            db.session.commit()

            if status == 'applied':
                applied += 1
            else:
                manual += 1

        flash(f"✅ Batch Apply: {applied} job(s) applied, {manual} sent to manual apply.")
        return redirect(url_for('dashboard'))

    # GET: Show all jobs
    with open("remoteok_jobs.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_jobs = list(reader)

    return render_template("batch_apply.html", jobs=all_jobs)

@app.route('/applications', methods=['GET', 'POST'])
@login_required
def applications():
    if request.method == 'POST':
        job_id = request.form.get('job_id')
        job = Application.query.get(job_id)
        if job and job.user_id == current_user.id and job.status == 'applied_manual':
            job.status = 'manual'
            db.session.commit()
            session.setdefault('job_log', []).append(f"🗑 Removed '{job.job_title}' from applied.")
            session.modified = True
        return redirect(url_for('applications'))

    apps = Application.query.filter(Application.user_id == current_user.id).order_by(Application.timestamp.desc()).all()
    return render_template('applications.html', applications=apps)

@app.route('/manual-jobs', methods=['GET', 'POST'])
@login_required
def manual_jobs():
    if request.method == 'POST':
        job_id = request.form.get('job_id')
        job = Application.query.get(job_id)
        if job and job.user_id == current_user.id and job.status == 'manual':
            job.status = 'applied_manual'
            db.session.commit()
            if 'job_log' not in session:
                session['job_log'] = []
            session['job_log'].append(f"✔️ Marked '{job.job_title}' as done from manual.")
            session.modified = True  # Force save
        return redirect(url_for('manual_jobs'))

    manual_jobs_list = Application.query.filter_by(user_id=current_user.id, status='manual') \
                                        .order_by(Application.timestamp.desc()).all()
    return render_template('manual_jobs.html', jobs=manual_jobs_list)

@app.route('/clear-log')
@login_required
def clear_log():
    session['job_log'] = []
    flash("🧹 Log cleared.")
    return redirect(url_for('dashboard'))

##########################################
# MAIN
##########################################

if __name__ == "__main__":
    app.run(debug=True) 