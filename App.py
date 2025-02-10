from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from Database import Admin, Database, Patient       # Interacting with database to query user-related data
from Hash_Password import hash_password, verify_password     # Implementing functions from the password hashing algorithm in Utils.py
from Simulation import run_simulation
from datetime import datetime, timedelta      # Used to set maximum session lifetime
import json
import os
import re

app = Flask(__name__)    # Initialising Flask app 
app.secret_key = os.urandom(16)     # Secret key for securing session cookies; 16 byte random key generated 
app.permanent_session_lifetime = timedelta(minutes=20)        # Defining session lifetime

login_manager = LoginManager()      # Initialising LoginManager to handle user sessions
login_manager.login_view = 'login'      # Redirecting unauthenticated users to 'login' route
login_manager.init_app(app)     # Connect LoginManager to app

# Creating Database instance - Admin and Patient instances inherit Database() methods and attributes through db instance
db_instance = Database()       

admin_instance = Admin(db_instance)
patient_instance = Patient(db_instance)


# User class inherits UserMixin from Flask-Login to manage users' attributes
class User(UserMixin):
    def __init__(self, id, first_name, last_name, username, email, password):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.email = email
        self.password = password

# Loading user details by user ID
@login_manager.user_loader
def load_user(user_id):
    user = admin_instance.get_user_by_id(user_id)  # Fetch user from database by ID
    
    if user:
        # returning an instance of User class
        return User(user['user_id'], user['first_name'], user['last_name'], user['username'], user['email'], user['password'])     
    return None

# Making session permanent before every request
@app.before_request
def session_permanent():
    session.permanent = True        

# Home Page
@app.route('/')
def home():
    return render_template("index.html")

# Registration Page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form.get('first_name')      
        last_name = request.form.get('last_name')      
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')  
        department_no = request.form.get('department_no')

        # Validation of email format
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            flash('Invalid email format. Please include a valid domain such as .com, .co.uk!', 'danger')
            return redirect(url_for('register'))

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", 'danger') 
            return redirect(url_for('register'))        # Reload registration page

        # Checking if user with the username already exists in database
        if admin_instance.get_user_by_username(username):
            flash('Username already exists. Please use a different one!', 'danger')
            return redirect(url_for('register'))
            
        # Checking if user with the email already exists in database
        if admin_instance.get_user_by_email(email):
            flash('Email address already exists. Please use a different one!', 'danger')
            return redirect(url_for('register'))

        hashed_password = hash_password(password)      # using hash_password() from Utils.py
        
        # Adding user to database
        admin_instance.add_user(username, first_name, last_name, email, hashed_password, department_no)
        
        # Fetching newly created user to log them in automatically once registered
        user = admin_instance.get_user_by_username(username)
        if user:
            user_instance = User(user['user_id'], user['first_name'], user['last_name'], user['username'], user['email'], user['password'])
            login_user(user_instance)

            flash("You have been registered successfully!", 'success')
            return redirect(url_for('dashboard'))

    return render_template("register.html")


# Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Fetch user details from database by email
        user = admin_instance.get_user_by_email(email)

        if user:
            if verify_password(user['password'], password):  # Verify hashed password with provided password
                user_instance = User(user['user_id'], user['first_name'], user['last_name'], user['username'], user['email'], user['password'])
                login_user(user_instance)       # Logging user in using the login_user method from Flask-Login 
                session['email'] = user['email']      # Storing email in session

                flash("You have been logged in successfully!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid password provided.", "danger")
        else:
            flash("Incorrect credentials provided.", "danger")

    return render_template("login.html")


# Dashboard (Protected)
@app.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:       # Confirm if user is authenticated
        return render_template("dashboard.html", first_name=current_user.first_name, last_name=current_user.last_name)
    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page


# User Profile (Protected)
@app.route('/profile')
def profile():
    # Displaying user information in profile page
    if current_user.is_authenticated:
        return render_template("profile.html", first_name=current_user.first_name, last_name=current_user.last_name, email=current_user.email, username=current_user.username)    
    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page
        

# Patient Registration (Protected)
@app.route('/patient_reg', methods=['POST', 'GET'])
def patient_reg():
    if current_user.is_authenticated:
        if request.method == 'POST':
            forename = request.form.get('forename')
            surname = request.form.get('surname')
            age = request.form.get('age')
            dob = request.form.get('dob')
            gender = request.form.get('gender')   
            contactno = request.form.get('contactno')
            address = request.form.get('address')
            department_no = request.form.get('department_no')

            # Valid range for age introduced
            if int(age) < 20 or int(age) >= 120:
                flash("Enter age within valid range of 20-120!", "danger")
                return redirect(url_for('patient_reg'))

            # Contact number validated (exactly 10 numbers required)
            if not len(contactno) == 10:
                flash("Enter valid contact number of exactly 10 numeric characters!", "danger")
                return redirect(url_for('patient_reg'))
            

            # Server-side validation for entering valid date of birth
            dob_date = datetime.strptime(dob, '%Y-%m-%d').date()
            today = datetime.today().date()

            if dob_date > today:
                flash("Date of birth cannot be in the future!", "danger")
                return redirect(url_for('patient_reg'))
            
            # Register patient record and store in database
            patient_instance.register(forename, surname, age, dob, gender, contactno, address, department_no)
            flash("Patient has been registered successfully!", "success")
            return redirect(url_for('patient_reg'))
        
        else:
            # Calculate minimum and maximum dates for the date of birth field
            max_date = datetime.today().strftime('%Y-%m-%d')
            min_date = datetime(datetime.today().year - 120, 1, 1).strftime('%Y-%m-%d')

            return render_template('patient_reg.html', user=current_user.username, min_date=min_date, max_date=max_date)
            
    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page
        

# Simulation Page (Protected)
@app.route('/simulation', methods=['GET', 'POST'])
def simulation():
    if current_user.is_authenticated:
        if request.method == 'POST':
            try:

                # Parsing simulation parameters from form data
                parameters = {
                    'hospital_capacity': int(request.form['hospital_capacity']),
                    'num_doctors': int(request.form['num_doctors']),
                    'patient_arrival_rate': int(request.form['patient_arrival_rate']),
                    'sim_duration': int(request.form['sim_duration']),
                    'sim_replications': int(request.form['sim_replications'])
                }

                # Error output on simulation page if any value in parameters <= 0
                if parameters['hospital_capacity'] <= 0:
                    flash("Maximum number of patients per week must be greater than zero!", "danger")
                    return render_template('simulation.html')
                
                elif parameters['num_doctors'] <= 0:
                    flash("Number of doctors must be greater than zero!", "danger")
                    return render_template('simulation.html')
                
                elif parameters['patient_arrival_rate'] <= 0:
                    flash("Patient arrival rate (weekly) must be greater than zero!", "danger")
                    return render_template('simulation.html')
                
                elif parameters['sim_duration'] <= 0:
                    flash("Simulation duration (weeks) must be greater than zero!", "danger")
                    return render_template('simulation.html')
                
                elif parameters['sim_replications'] <= 0:
                    flash("Number of simulation replications must be at least 1!", "danger")
                    return render_template('simulation.html')

                
                # Validating patient arrival rate <= maximum hospital capacity
                if parameters['patient_arrival_rate'] > parameters['hospital_capacity']:
                    flash("Patient arrival rate (weekly) cannot exceed maximum number of patients per week!", "danger")
                    return render_template('simulation.html')
                

                # Run simulation method, encapsulating all simulation logic, used to connect simulation to Flask app
                results = run_simulation(
                    parameters['hospital_capacity'],
                    parameters['num_doctors'],
                    parameters['patient_arrival_rate'],
                    parameters['sim_duration'],
                    parameters['sim_replications']
                )

                # Write simulation results to a JSON file for the Results Page
                with open('Results.json', 'w') as f:
                    json.dump(results, f)
                return redirect(url_for('results'))

            except Exception as e:
                return render_template('simulation.html', error=str(e))

        return render_template('simulation.html', username=current_user.username)

    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page
        

# Results Page (Protected) 
@app.route('/results')
def results():
    if current_user.is_authenticated:
        try:
            # Load simulation results from the JSON file
            with open('Results.json', 'r') as file:
                simulation_results = json.load(file)
            return render_template('results.html', results=simulation_results, username=current_user.username)
        
        except FileNotFoundError:
            return render_template('results.html', error="No results found. Please run a simulation first.")
    
    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page


# Logout (Protected)
@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()       # User automatically logged out using logout_user() method from Flask-Login
        session.clear()     # All session data is cleared
        flash('You have been logged out! Please log in again.', 'info')
        return redirect(url_for('login'))
    else:
        flash("You need to log in first!", "warning")   
        return redirect(url_for('login'))       # Unauthenticated users redirected to login page
        

if __name__ == '__main__':
    app.run(debug=True)     # Running the Flask app in debug mode

