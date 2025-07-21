# app.py - Flask backend server for Job Bot
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
import os
from werkzeug.utils import secure_filename
import csv
from models import UserProfile, Application
import subprocess

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
    # Get current user's profile
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    # Fallback if profile isn't completed yet
    if not profile:
        flash("🚨 Please complete your profile first.")
        return redirect(url_for('profile'))

    matched_jobs = []

    try:
        with open("remoteok_jobs.csv", newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                job_title = row['title'].lower()
                job_company = row['company'].lower()
                print(job_title, job_company)  # Debug: See what jobs are being read

                # Looser match: show jobs if either field matches
                if (profile.preferred_title.lower() in job_title) or (profile.preferred_location.lower() in job_company):
                    matched_jobs.append(row)
    except Exception as e:
        print(f"Error reading jobs: {e}")
        flash("❌ Could not load jobs. Make sure remoteok_jobs.csv exists.")
        matched_jobs = []

    return render_template("dashboard.html", profile=profile, jobs=matched_jobs)

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

    # Get all links the user has already applied to (applied or manual)
    applied_links = set(
        app.link for app in Application.query.filter_by(user_id=current_user.id).all()
        if app.status in ["applied", "manual"]
    )

    if request.method == 'POST':
        job_links = request.form.getlist('job_links')
        applied_count = 0
        manual_count = 0

        jobs_to_apply = []
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['link'] in job_links:
                    jobs_to_apply.append(row)

        python_exe = os.path.join(os.getcwd(), 'env', 'Scripts', 'python.exe')
        bot_path = os.path.join(os.getcwd(), 'apply_bot.py')

        for job in jobs_to_apply:
            if job['link'] in applied_links:
                continue  # Skip already-applied jobs
            try:
                result = subprocess.run([python_exe, bot_path, job['link']], capture_output=True, text=True)
                if result.returncode == 0:
                    status = 'applied'
                    reason = None
                else:
                    status = 'manual'
                    reason = result.stdout.strip().split('\n')[-1]  # Last print line from the bot
            except Exception as e:
                status = 'manual'
                reason = f'Error: {e}'

            app_log = Application(
                user_id=current_user.id,
                job_title=job['title'],
                company=job['company'],
                link=job['link'],
                status=status,
                reason=reason
            )
            db.session.add(app_log)
            db.session.commit()

            if status == 'applied': applied_count += 1
            else: manual_count += 1

        flash(f"✅ Applied to {applied_count} job(s). Sent {manual_count} to Manual Apply.")
        return redirect(url_for('dashboard'))

    # ✅ UPDATED: Load ALL jobs (not just profile matches)
    all_jobs = []
    try:
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            all_jobs = list(reader)
    except:
        flash("⚠️ Could not load jobs. Try again later.")

    return render_template('batch_apply.html', jobs=all_jobs, applied_links=applied_links)

@app.route('/applications')
@login_required
def applications():
    user_applied_jobs = Application.query.filter_by(user_id=current_user.id).order_by(Application.timestamp.desc()).all()
    return render_template('applications.html', applications=user_applied_jobs)

@app.route('/manual-jobs')
@login_required
def manual_jobs():
    manual_jobs = Application.query.filter_by(user_id=current_user.id, status='manual').order_by(Application.timestamp.desc()).all()
    return render_template('manual_jobs.html', jobs=manual_jobs)

##########################################
# MAIN
##########################################

if __name__ == "__main__":
    app.run(debug=True) 