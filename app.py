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
from io import StringIO
from flask import Response
from flask import send_from_directory

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
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()

    jobs = []
    try:
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as f:
            import csv
            reader = csv.DictReader(f)
            jobs = list(reader)
    except Exception:
        jobs = []

    if request.method == 'POST':
        titles = request.form.getlist('title')
        locations = request.form.getlist('location')
        title_custom = request.form.get('title_custom', '')
        location_custom = request.form.get('location_custom', '')

        if title_custom:
            titles += [t.strip() for t in title_custom.split(',') if t.strip()]
        if location_custom:
            locations += [l.strip() for l in location_custom.split(',') if l.strip()]

        file = request.files.get('resume')
        filename = profile.resume_filename if profile and profile.resume_filename else None

        def allowed_file(fname):
            return '.' in fname and fname.rsplit('.', 1)[1].lower() in {'pdf','doc','docx'}
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        if profile:
            profile.preferred_title = ','.join(titles)
            profile.preferred_location = ','.join(locations)
            profile.resume_filename = filename
            profile.updated_at = datetime.utcnow()
        else:
            profile = UserProfile(
                user_id=current_user.id,
                preferred_title=','.join(titles),
                preferred_location=','.join(locations),
                resume_filename=filename,
                updated_at=datetime.utcnow()
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


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email')
        password = request.form.get('password')

        if not all([first_name, last_name, email, password]):
            flash("Please fill in all fields.")
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash("❌ Email is already registered.")
            return render_template('register.html')

        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("✅ Registration successful! Welcome.")
        return redirect(url_for('dashboard'))
    return render_template('register.html')


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

    # POST (apply selected jobs): no change needed
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

            # ✅ Add logging to session:
            if status == 'applied':
                msg = f"🤖 Auto-applied to '{job['title']}' at {job['company']}."
                session.setdefault('job_log', []).append(msg)
            elif status == 'manual':
                msg = f"⏭ Skipped '{job['title']}' ➝ added to manual apply."
                session.setdefault('job_log', []).append(msg)
            session.modified = True

            if status == 'applied':
                applied += 1
            else:
                manual += 1

        flash(f"✅ Batch Apply: {applied} job(s) applied, {manual} sent to manual apply.")
        return redirect(url_for('dashboard'))

    # GET: Show all jobs, with filters
    with open("remoteok_jobs.csv", newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_jobs = list(reader)

    # Add filtering logic here!
    title_filter = request.args.get('title', '').strip().lower()
    company_filter = request.args.get('company', '').strip().lower()

    filtered_jobs = []
    for job in all_jobs:
        title_match = not title_filter or title_filter in job['title'].lower()
        company_match = not company_filter or company_filter in job['company'].lower()
        if title_match and company_match:
            filtered_jobs.append(job)

    return render_template("batch_apply.html", jobs=filtered_jobs)

@app.route('/applications', methods=['GET', 'POST'])
@login_required
def applications():
    apps = Application.query.filter_by(user_id=current_user.id).all()
    if request.method == 'POST':
        job_id = request.form.get('job_id', type=int)
        job = Application.query.get(job_id)
        if job and job.user_id == current_user.id and job.status == 'applied_manual':
            job.status = 'manual'
            db.session.commit()
            flash("✅ Job moved back to manual jobs.")
            return redirect(url_for('applications'))
    return render_template('applications.html', applications=apps)



@app.route('/manual-jobs')
@login_required
def manual_jobs():
    manual_jobs_list = Application.query.filter_by(user_id=current_user.id, status='manual').all()
    return render_template('manual_jobs.html', jobs=manual_jobs_list)

@app.route('/mark-done/<int:job_id>', methods=['POST'])
@login_required
def mark_done(job_id):
    job = Application.query.get(job_id)
    if job and job.user_id == current_user.id and job.status == 'manual':
        job.status = 'applied_manual'
        db.session.commit()

        msg = f"✔️ Marked '{job.job_title}' as done from manual."
        session.setdefault('job_log', []).append(msg)
        session.modified = True

    return redirect(url_for('manual_jobs'))

@app.route('/clear-log')
@login_required
def clear_log():
    session['job_log'] = []
    flash("🧹 Log cleared.")
    return redirect(url_for('dashboard'))

@app.route('/export-applications')
@login_required
def export_applications():
    # Filter only actually applied jobs
    applied_jobs = Application.query.filter(
        Application.user_id == current_user.id,
        Application.status.in_(['applied', 'applied_manual'])
    ).order_by(Application.timestamp.desc()).all()

    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Company', 'Link', 'Status', 'Timestamp'])

    for job in applied_jobs:
        writer.writerow([
            job.job_title,
            job.company,
            job.link,
            job.status,
            job.timestamp.strftime('%Y-%m-%d %H:%M')
        ])

    # Return CSV download
    output.seek(0)
    return Response(
        output,
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=applications.csv'}
    )

@app.route('/resume/<filename>')
@login_required
def view_resume(filename):
    # Ensure the user can only access their own resume
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    if profile and profile.resume_filename == filename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    flash("❌ You are not authorized to view this resume.")
    return redirect(url_for('dashboard'))

@app.route('/refresh-jobs')
@login_required
# Optionally, add admin check here if you want to restrict
# @admin_required (if you have such a decorator)
def refresh_jobs():
    try:
        result = subprocess.run(['python', 'scrape_jobs.py'], capture_output=True, text=True)
        if result.returncode == 0:
            flash("✅ Job list refreshed successfully.")
        else:
            flash(f"⚠️ Job refresh failed: {result.stdout or 'Unknown error'}")
    except Exception as e:
        flash(f"❌ Could not refresh jobs: {e}")
    return redirect(url_for('dashboard'))

##########################################
# MAIN
##########################################

if __name__ == "__main__":
    app.run(debug=True) 



from flask_login import login_required, current_user

@app.route('/')
@login_required
def dashboard():
    from datetime import datetime, timedelta
    import csv
    now = datetime.utcnow()
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    matched_jobs = []
    if profile:
        with open('remoteok_jobs.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                title_match = profile.preferred_title.lower() in row['title'].lower() if profile.preferred_title else True
                loc_match = profile.preferred_location.lower() in row['company'].lower() if profile.preferred_location else True
                if title_match or loc_match:
                    matched_jobs.append(row)

    user_apps = Application.query.filter_by(user_id=current_user.id).all()
    applied_auto_count = sum(1 for job in user_apps if job.status == 'applied')
    applied_manual_count = sum(1 for job in user_apps if job.status == 'applied_manual')
    applied_total = applied_auto_count + applied_manual_count
    manual_pending_count = sum(1 for job in user_apps if job.status == 'manual')
    one_week_ago = now - timedelta(days=7)
    applied_this_week = sum(1 for job in user_apps if job.status in ['applied', 'applied_manual'] and job.timestamp > one_week_ago)

    # Recent jobs
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

    # Weekly stats
    week_counts, week_labels = [], []
    for i in range(4, 0, -1):
        start_of_week = now - timedelta(weeks=i)
        end_of_week = now - timedelta(weeks=i-1)
        count = sum(1 for job in user_apps if start_of_week <= job.timestamp < end_of_week and job.status in ('applied', 'applied_manual'))
        week_counts.append(count)
        week_labels.append(f"Week of {start_of_week.strftime('%b %d')}")

    return render_template(
        'dashboard.html',
        jobs=matched_jobs,
        recent_jobs_day=recent_jobs_day,
        recent_jobs_week=recent_jobs_week,
        profile=profile,
        stats={
            'applied_total': applied_total,
            'applied_this_week': applied_this_week,
            'manual_pending': manual_pending_count
        },
        week_counts=week_counts,
        week_labels=week_labels
    )

