import sqlite3
import uuid     # Used to generate unique IDs for users and patients


class Database:
    def __init__(self, db_name='nea.db'):
        self.db_name = db_name

    def connect(self):
        connection = sqlite3.connect(self.db_name)
        connection.execute("PRAGMA foreign_keys = ON;")      # Handling foreign keys
        connection.commit()

        connection.row_factory = sqlite3.Row        # Results will be outputted in dictionary format
        return connection


    # General method for executing a SQL query
    def execute(self, query, args=None):
        try:
            connection = self.connect()
            cursor = connection.cursor()

            if args:
                cursor.execute(query, args)
            else:
                cursor.execute(query)

            connection.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")

        finally:
            connection.close()


    # General method for fetching all rows from a query
    def fetchall(self, query, args=None):
        try:
            connection = self.connect()
            cursor = connection.cursor()

            if args:
                cursor.execute(query, args)
            else:
                cursor.execute(query)

            results = cursor.fetchall()
            return results
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")

        finally:
            connection.close()


    # General method for fetching a specific row from a query
    def fetchone(self, query, args=None):
        try:
            connection = self.connect()
            cursor = connection.cursor()

            if args:
                cursor.execute(query, args)
            else:
                cursor.execute(query)

            result = cursor.fetchone()
            return result
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")

        finally:
            connection.close()


    @staticmethod
    def format_rows(rows):
        # Converting all SQLite Row objects to dictionaries for better readability
        return [dict(row) for row in rows]


# CreateTables class used to create all required tables - contains all the database schema
class CreateTables(Database):
    def __init__(self, db):
        self.db = db

    def admin_Data(self):
        try:
            query = '''
                CREATE TABLE IF NOT EXISTS admin_Data (
                    user_id         TEXT NOT NULL PRIMARY KEY,
                    username        VARCHAR(50) NOT NULL,
                    first_name      VARCHAR(50) NOT NULL,
                    last_name       VARCHAR(50) NOT NULL,
                    email           VARCHAR(320) NOT NULL UNIQUE,
                    password        VARCHAR(128) NOT NULL,
                    department_no   INTEGER NOT NULL,
                    FOREIGN KEY (department_no) REFERENCES simulation_Data(department_no)
                );
            '''
            self.db.execute(query)

        except sqlite3.Error as e:
            print(f"Error occurred while creating admin_Data table: {e}")

    def patient_Data(self):
        try:
            query = '''
                CREATE TABLE IF NOT EXISTS patient_Data (
                    patient_id      TEXT NOT NULL PRIMARY KEY,
                    forename        VARCHAR(50) NOT NULL,
                    surname         VARCHAR(50) NOT NULL,
                    age             INTEGER NOT NULL,
                    dob             DATE NOT NULL,
                    gender          VARCHAR(20),
                    contactno       INTEGER NOT NULL,
                    address         VARCHAR(50) NOT NULL,
                    department_no   INTEGER NOT NULL,
                    FOREIGN KEY (department_no) REFERENCES simulation_Data(department_no)
                );
            ''' 
            self.db.execute(query)

        except sqlite3.Error as e:
            print(f"Error occurred while creating patient_Data table: {e}")

    def simulation_Data(self):
        try:
            query = '''
                CREATE TABLE IF NOT EXISTS simulation_Data (
                    department_no		    INTEGER NOT NULL PRIMARY KEY,
                    hospital_capacity	    INTEGER NOT NULL,
                    patient_arrivalrate	    INTEGER NOT NULL,
                    simduration		        INTEGER NOT NULL,
                    doctors			        INTEGER NOT NULL					  
                );
            '''
            self.db.execute(query)

        except sqlite3.Error as e:
            print(f"Error occurred while creating simulation_Data table: {e}")



# Class for User Management
class Admin:
    def __init__(self, db):
        self.db = db

    # Registration route in App.py

    def add_user(self, username, first_name, last_name, email, password, department_no):
        existing_user = self.get_user_by_email(email)
        if existing_user:
            print(f"User with email {email} already exists. Please use different one!\n")
            return
        else:
            print("User has been added and stored successfully in database!")

        user_id = str(uuid.uuid4())     # Unique user ID generated

        query = '''
            INSERT INTO admin_Data (user_id, username, first_name, last_name, email, password, department_no) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        self.db.execute(query, (user_id, username, first_name, last_name, email, password, department_no))

    def get_all_users(self):
        query = 'SELECT * FROM admin_Data'
        return self.db.fetchall(query)

    def get_user_by_id(self, user_id):
        query = 'SELECT * FROM admin_Data WHERE user_id = ?'
        return self.db.fetchone(query, (user_id,))

    def get_user_by_username(self, username):
        query = 'SELECT * FROM admin_Data WHERE username = ?'
        return self.db.fetchone(query, (username,))

    def get_user_by_email(self, email):        
        query = 'SELECT * FROM admin_Data WHERE email = ?'
        return self.db.fetchone(query, (email,))

    def delete_user(self, email):
        query = 'DELETE FROM admin_Data WHERE email = ?'
        self.db.execute(query, (email,))

    def update_email(self, new_email, user_id):
        existing_user = self.get_user_by_email(new_email)
        if existing_user:
            print(f"Email {new_email} is already in use.")
            return
        query = 'UPDATE admin_Data SET email = ? WHERE user_id = ?'
        self.db.execute(query, (new_email, user_id))

    def count_users_by_dept(self):
        query = '''
            SELECT admin_Data.department_no, COUNT(admin_Data.user_id) 
            FROM admin_Data
            INNER JOIN simulation_Data ON admin_Data.department_no = simulation_Data.department_no
            WHERE simulation_Data.department_no = ?
            GROUP BY admin_Data.department_no
        '''
        return self.db.fetchall(query)



# Managing Patient Records
class Patient:
    def __init__(self, db):
        self.db = db

    def register(self, forename, surname, age, dob, gender, contactno, address, department_no):

        patient_id = str(uuid.uuid4())
        
        query = '''
            INSERT INTO patient_Data (patient_id, forename, surname, age, dob, gender, contactno, address, department_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        self.db.execute(query, (patient_id, forename, surname, age, dob, gender, contactno, address, department_no))

    def get_patients(self):
        query = 'SELECT * FROM patient_Data'
        return self.db.fetchall(query)

    def get_patient_by_id(self, patient_id):
        query = 'SELECT * FROM patient_Data WHERE patient_id = ?'
        return self.db.fetchone(query, (patient_id,))

    def delete_patient(self, patient_id):
        query = 'DELETE FROM patient_Data WHERE patient_id = ?'
        self.db.execute(query, (patient_id,))

    def drop_patient_Data(self):
        query = 'DROP TABLE IF EXISTS patient_Data'
        self.db.execute(query)


# Managing Simulation Data
class Simulate:
    def __init__(self, db):
        self.db = db

    def department_exists(self, department_no):
        query = 'SELECT * FROM simulation_Data WHERE department_no = ?'
        return self.db.fetchone(query, (department_no,))

    # Can be used for Simulation Page Route in App.py
    def add_sim_data(self, capacity, arrival_rate, sim_duration, department_no, doctors):
        if not self.department_exists(department_no):
            query = '''
			INSERT INTO simulation_Data 
			(hospital_capacity, patient_arrivalrate, simduration, department_no, doctors)
			VALUES (?, ?, ?, ?, ?)
			'''
            self.db.execute(query, (capacity, arrival_rate, sim_duration, department_no, doctors))
        else:
            print(f"Department number {department_no} already exists.")

    def get_sim_data(self):
        query = 'SELECT * FROM simulation_Data'
        return self.db.fetchall(query)

    def dept_ordered_by_capacity(self):
        query = '''
            SELECT department_no, hospital_capacity
            FROM simulation_Data
            ORDER BY hospital_capacity DESC
        '''
        return self.db.fetchall(query)

    def total_patients_in_dept(self):
        query = '''
            SELECT department_no, COUNT(*) AS total_patients
            FROM patient_Data
            GROUP BY department_no
        '''
        return self.db.fetchall(query)

    def dept_avg_capacity(self):
        query = '''
            SELECT department_no, AVG(hospital_capacity) AS average_capacity
            FROM simulation_Data
            GROUP BY department_no
        '''
        return self.db.fetchall(query)

    def dept_max_capacity(self):
        query = '''
            SELECT MAX(hospital_capacity) AS max_capacity
            FROM simulation_Data
        '''
        return self.db.fetchone(query)

    def dept_min_capacity(self):
        query = '''
            SELECT MIN(hospital_capacity) AS min_capacity
            FROM simulation_Data
        '''
        return self.db.fetchone(query)

    def dept_patient_count_and_total_capacity(self):
        query = '''
            SELECT simulation.department_no AS department_number,
                COUNT(patient.patient_id) AS total_patients,
                SUM(simulation.hospital_capacity) AS total_capacity
            FROM simulation_Data simulation
            LEFT JOIN patient_Data patient ON simulation.department_no = patient.department_no
            WHERE simulation.department_no = ?
            GROUP BY simulation.department_no
        '''
        return self.db.fetchall(query)



# Testing 

if __name__ == '__main__':

    db = Database('nea.db')
    tables = CreateTables(db)
    admin = Admin(db)

# Testing initialisation of database
    try:
        tables.simulation_Data()
        tables.admin_Data()
        tables.patient_Data()

        print("\nTables initialised successfully.\n")

    except Exception as e:
        print(f"Error {e} occurred: Unable to initialise database tables.")

    
    # Validating SQL Injection Attacks
    try:
        # Attempting to inject malicious query
        malicious_email = "testuser123@example.com' OR '1'='1"
        print(f"\nAttempting SQL injection with email: {malicious_email}")
        
        # Testing parameterised query to prevent SQL injection with malicious email
        user = admin.get_user_by_email(malicious_email)
        
        if user:
            print("SQL Injection successful! This is a security risk.")
        else:
            print("SQL Injection failed. Parameterized queries are working correctly!\n")
    
    except Exception as e:
        print(f"An error occurred during SQL injection test: {e}")

