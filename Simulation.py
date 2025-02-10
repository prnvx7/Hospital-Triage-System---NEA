import simpy
import random

# Encoded a function that connects and runs the simulation on my Flask app on App.py
def run_simulation(hospital_capacity, num_doctors, patient_arrival_rate, sim_duration, sim_replications):

    # Initialising severity levels and distribution
    SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH"]
    SEVERITY_DISTRIBUTION = [0.33, 0.33, 0.33]


    class Patient:
        def __init__(self, severity, arrival_week):
            self.severity = severity            # random severity level assigned to each Patient object
            self.arrival_week = arrival_week    # week patient enters the system
            self.wait = None


    class Hospital:
        def __init__(self, env, num_doctors, mode):
            self.env = env      # initialising the SimPy environment for Hospital
            self.no_of_doctors = simpy.Resource(env, num_doctors)   # Doctors are SimPy resources used by Patient objects
            self.patients_treated = []      # list that stores treated patients
            self.outpatients = 0        # initalising current patients in hospital to 0 before each run 
            
            self.priorityQueue = []     # Priority queue which manages the flow of patients (high, medium and low triage precedence)
            self.mode = mode        # Initialising modes for each of the 3 triage scenarios
            self.low_sev_dict = {6: [], 5: [], 4: [], 3: [], 2: [], 1: []}      # deferral period for low severity patients
            self.med_sev_dict = {3: [], 2: [], 1: []}       # deferral period for medium severity patients

        
        # Ensure the number of patients in hospital do not overtake the maximum capacity
        def patient_intake(self):
            return patient_arrival_rate <= hospital_capacity
        
        # Calculating wait time of patient by subtracting the week they entered from the current environment week
        def calc_treatment_time(self, env, patient):
            patient.wait = env.now - patient.arrival_week

        def add_patient(self, patients):     # Parameters taken into function: SimPy env and list of patients from a week, n
            
            # Temporary lists initialised to store low and medium severity patients until all high severity patients have been triaged
            medList = []
            lowList = []

            for patient in patients:
                if patient.severity == SEVERITY_LEVELS[2]:      # High severity patients

                    medPos = next(
                        (i for i, p in enumerate(self.priorityQueue) if p.severity == SEVERITY_LEVELS[1]),
                        None
                    )

                    '''
                    Checking priority queue to return the first index of a medium severity patient in queue if they exist;
                    If NO medium severity patient exists in the queue, high severity patient is appended to the queue.
                    '''

                    if medPos is None:
                        self.priorityQueue.append(patient)      # No medium severity patient found - high severity added to rear of queue
                    else:
                        self.priorityQueue.insert(medPos, patient)      # High severity inserted to queue in front of first medium severity patient


                # Medium severity patients stored in medList temporarily before triage begins
                elif patient.severity == SEVERITY_LEVELS[1]:
                    medList.append(patient)

                # Low severity patients stored in lowList temporarily before triage begins
                else:
                    lowList.append(patient)


            # Low severity pathway implemented
            if self.mode >= 2:
                for i in range(1, 7):       # looping through low severity dictionary from rear to front
                    if i == 1:
                        for patient in self.low_sev_dict[i]:
                            self.priorityQueue.append(patient)      # low severity patient added to queue after deferral period completed

                    # If patient is still yet to complete their deferral period, they are shifted to the next week in dictionary
                    else:
                        self.low_sev_dict[i - 1] = self.low_sev_dict[i]

                self.low_sev_dict[6] = lowList      # patients stored in lowList temporarily are added to the low severity dictionary


            # Medium severity pathway implemented - SAME PROCEDURE AS FOR LOW SEVERITY PATHWAY
            if self.mode == 3:
                for i in range(1, 4):
                    if i == 1:
                        for patient in self.med_sev_dict[i]:
                            self.priorityQueue.append(patient)       # once deferral period finished, added to priority queue

                    else:
                        self.med_sev_dict[i - 1] = self.med_sev_dict[i]     # shifted to next week of deferral period

                self.med_sev_dict[3] = medList      # patients in medList are added to the medium severity dictionary


# Generator function used to instantiate patient objects with different severities using random distributions

    def patient_generator(env, hospital):
        for week in range(sim_duration):
            temporaryPatientList = []       # stores list of patients arriving at current week for every week in the simulation duration

            for _ in range(patient_arrival_rate):

                # Validation check for current patients being less than maximum capacity
                if hospital.patient_intake():
                    
                    severity = random.choices(SEVERITY_LEVELS, SEVERITY_DISTRIBUTION)[0]    # severity level randomly distributed using Python 'random' module and severity distributions
                    patient = Patient(severity, week)       # Patient object instantiated

                    if patient.severity == SEVERITY_LEVELS[0]:

                        # Test given to low severity patients - percentage randomly decided for determining result

                        low_sev_testStat = random.randint(0, 50)       # 50% probabilty of testing positive/negative
                        test_result = (random.random() * 100) < low_sev_testStat    # test result checked against low severity test statistic

                        # Patient tested positive
                        if test_result:
                            temporaryPatientList.append(patient)    # added to temporary patient list

                    # Any medium or high severity patients are stored in the temporary patient list - they do not require a test
                    else:
                        temporaryPatientList.append(patient)

            hospital.add_patient(temporaryPatientList)      # add_patient() implements triage algorithms and manages flow of patients using priority queue
            
            yield env.timeout(1)    # Simulation shifts to next week


    def first_come_first_serve(env, hospital):
        while True:
            if hospital.priorityQueue:      # while priority queue is not empty

                for patient in hospital.priorityQueue:
                    env.process(process_patient(env, hospital, patient))    # patients in the priority queue are processed individually
                
                hospital.priorityQueue.clear()      # priority queue cleared before each simulation replication

            yield env.timeout(1)    # Simulation shifts to next week


    def process_patient(env, hospital, patient):
        with hospital.no_of_doctors.request() as request:
            yield request       # patient waits until a doctor is allocated to the patient
            
            hospital.calc_treatment_time(env, patient)      # Patient wait time calculated
            hospital.patients_treated.append(patient)       # Patient added to list of triaged patients
            hospital.outpatients -= 1       # Patient exits system


    # Results of each simulation run are written into this list; this list is outputted onto a JSON file which is connected to my Flask app
    # This is how the user is able to view the simulation results on the Flask application

    results = []

    # For each of the 3 modes (first come first serve, low severity pathway and medium severity pathway)

    for mode in range(1, 4):
        mode_results = {
            "mode": mode,            # display the mode being implemented
            "simulations": [],       # display results for each simulation run
            "average_wait_time": 0      # average wait time for each mode displayed
        }

        total_avg_wait_time = 0

        # Running each replication 
        for n in range(sim_replications):
            env = simpy.Environment()       # creating SimPy environment to run simulation
            hospital = Hospital(env, num_doctors, mode)     # instantiating Hospital with SimPy env, SimPy resource (doctor) and triage path
            
            env.process(patient_generator(env, hospital))       # Simulating the arrival of patients and testing for low severity patients
            env.process(first_come_first_serve(env, hospital))      # Implementing the first come first serve triage pathway (mode 1)

            env.run(until=sim_duration)     # simulation runs until the last week of data is outputted

            total_patients = patient_arrival_rate * sim_duration        # fixed number of patients arriving weekly times the number of weeks of data

            # calculating total wait time of all patients 
            total_wait = sum([p.wait + 1 if p.severity == "HIGH" else p.wait for p in hospital.patients_treated])

            # calculating average wait time
            avg_wait = total_wait / total_patients if total_patients > 0 else 0

            # Simulation outputs
            simulation_result = {
                "simulation": n + 1,        # Simulation replication
                "total_patients": total_patients,       
                "total_patients_treated": len(hospital.patients_treated),       # Returns number of patients in treated list
                "patients_not_positive": total_patients - len(hospital.patients_treated),       # Total patients - patients treated
                "average_wait_time": round(avg_wait, 2)     # Average wait times rounded to 2 decimal places
            }

            mode_results["simulations"].append(simulation_result)       # for each simulation run in a mode, the above simulation results are outputted
            
            total_avg_wait_time += avg_wait     # total average wait time calculated for mode 'x' by adding average wait times of all simulation replications

        # Average wait time for each mode is outputted by dividing the total average by the number of simulation replications
        mode_results["average_wait_time"] = round(float(total_avg_wait_time / sim_replications), 2)     

        results.append(mode_results)       # outputs stored in results list
        
    return results      # outputted in JSON file; file handling used to display contents in JSON file to Flask app


