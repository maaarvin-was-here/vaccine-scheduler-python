import sys
from model.Vaccine import Vaccine
from model.Caregiver import Caregiver
from model.Patient import Patient
from util.Util import Util
from db.ConnectionManager import ConnectionManager
import pymssql
import datetime
import random

'''
objects to keep track of the currently logged-in user
Note: it is always true that at most one of currentCaregiver and currentPatient is not null
        since only one user can be logged-in at a time
'''
current_patient = None

current_caregiver = None


def create_patient(tokens):
    # create_patient <username> <password>
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]
    if username_exists_patient(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    try:
        patient = Patient(username, salt=salt, hash=hash)
        try:
            patient.save_to_db()
        except:
            print("Create failed, Cannot save")
            return
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def create_caregiver(tokens):
    # create_caregiver <username> <password>
    # check 1: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    username = tokens[1]
    password = tokens[2]

    # check 2: check if the username has been taken already
    if username_exists_caregiver(username):
        print("Username taken, try again!")
        return

    salt = Util.generate_salt()
    hash = Util.generate_hash(password, salt)

    # create the caregiver
    try:
        caregiver = Caregiver(username, salt=salt, hash=hash)
        # save to caregiver information to our database
        try:
            caregiver.save_to_db()
        except:
            print("Create failed, Cannot save")
            return
        print(" *** Account created successfully *** ")
    except pymssql.Error:
        print("Create failed")
        return


def username_exists_patient(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Patients WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)
        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def username_exists_caregiver(username):
    cm = ConnectionManager()
    conn = cm.create_connection()

    select_username = "SELECT * FROM Caregivers WHERE Username = %s"
    try:
        cursor = conn.cursor(as_dict=True)
        cursor.execute(select_username, username)

        #  returns false if the cursor is not before the first record or if there are no rows in the ResultSet.
        for row in cursor:
            return row['Username'] is not None
    except pymssql.Error:
        print("Error occurred when checking username")
        cm.close_connection()
    cm.close_connection()
    return False


def login_patient(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Re-enter Credentials")
        return

    username = tokens[1]
    password = tokens[2]

    patient = None
    try:
        try:
            patient = Patient(username, password=password).get()
        except:
            print("Get Failed")
            return
    except pymssql.Error:
        print("Error occurred when logging in")

        # check if the login was successful
    if patient is None:
        print("Incorrect credentials, please try again!")
    else:
        print("Patient logged in as: " + username)
        current_patient = patient


def login_caregiver(tokens):
    # login_caregiver <username> <password>
    # check 1: if someone's already logged-in, they need to log out first
    global current_caregiver
    if current_caregiver is not None or current_patient is not None:
        print("Already logged-in!")
        return

    # check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Re-enter Credentials")
        return

    username = tokens[1]
    password = tokens[2]

    caregiver = None
    try:
        try:
            caregiver = Caregiver(username, password=password).get()
        except:
            print("Get Failed")
            return
    except pymssql.Error:
        print("Error occurred when logging in")

        # check if the login was successful
    if caregiver is None:
        print("Please try again!")
    else:
        print("Caregiver logged in as: " + username)
        current_caregiver = caregiver


# shows which caregivers are available on a given day
def search_caregiver_schedule(tokens):
    if len(tokens) != 2:
        print("Please try again!")
        return
    date = tokens[1]

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    # available caregivers
    get_caregivers = "SELECT DISTINCT C.Username FROM Caregivers AS C, Booked AS B WHERE " \
                     "C.Username NOT IN(SELECT B.Username FROM Booked AS B WHERE B.Time = %s)"
    cursor.execute(get_caregivers, date)

    print("Available Caregivers for {}: ".format(date))
    for row in cursor:
        name = row['Username']
        print("     {}".format(name))

    # doses per vaccine
    print("")
    print("Available Vaccine Doses: ")
    get_vaccines = "SELECT Name, Doses FROM Vaccines"
    cursor.execute(get_vaccines)
    for row in cursor:
        name = row['Name']
        doses = row['Doses']
        print("     {} : {}".format(name, doses))
    return


# as a patient, reserve an appointment on a date for a chosen vaccine with a random caregiver assigned.
def reserve(tokens):
    # date, vaccine
    global current_patient
    if current_patient is None:
        print("Must be logged in as a patient!")
        return

    if len(tokens) != 3:
        print("Please try again!")
        return
    date = tokens[1]
    vaccine = tokens[2]

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    # select distinct caregiver.username from caregivers where c.username NOT IN booked

    count_caregivers = "SELECT COUNT(*) AS Count FROM Caregivers C " \
                       "WHERE C.Username NOT IN (SELECT B.Username FROM Booked AS B WHERE B.Time = %s)"
    cursor.execute(count_caregivers, date)
    for row in cursor:
        count = row['Count']
        print(count)

    # error if no available
    if count == 0:
        print("No available appointments!")
        return

    rand_num = random.randint(1, count)
    print(rand_num)

    get_available_caregivers = "SELECT DISTINCT C.Username FROM Caregivers AS C " \
                               "WHERE C.Username NOT IN (SELECT B.Username FROM Booked AS B WHERE B.Time = %s)"
    cursor.execute(get_available_caregivers, date)

    counter = 1
    for row in cursor:
        if counter < rand_num:
            counter += 1
        else:
            selected_caregiver = row['Username']
            break

    # error if no available vaccine doses
    get_vaccines = "SELECT Doses FROM Vaccines WHERE Name = %s"
    cursor.execute(get_vaccines, vaccine)

    doses = 0
    for row in cursor:
        doses += row['Doses']

    print("{} doses available".format(doses))
    if doses == 0:
        print("No more doses for {}, please try again".format(vaccine))
        return

    cursor.execute("SET IDENTITY_INSERT Booked OFF;")
    # insert into booked
    #  (id, time, Username, Patient, v_name)
    insert_app = "INSERT INTO Booked VALUES (%s, %s, %s, %s)"
    t = (date, selected_caregiver, current_patient.username, vaccine)
    cursor.execute(insert_app, t)
    conn.commit()
    print("Appointment Booked with {}!".format(selected_caregiver))

    # vaccine count - 1
    update = "UPDATE Vaccines SET Doses = %d WHERE Name = %s"
    cursor.execute(update, (doses - 1, vaccine))
    conn.commit()

    return


def upload_availability(tokens):
    #  upload_availability <date>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    # check 2: the length for tokens need to be exactly 2 to include all information (with the operation name)
    if len(tokens) != 2:
        print("Please try again!")
        return

    date = str(tokens[1])

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    get_schedule = "SELECT * FROM Booked WHERE Name = %s AND Time = %s"
    cursor.execute(get_schedule, (current_caregiver.username, date))

    name = None
    for row in cursor:
        name = row['Name']

    if name is None:
        print("You are available")
    else:
        print("You are booked on this day")

    # date = tokens[1]
    # assume input is hyphenated in the format mm-dd-yyyy
    # date_tokens = date.split("-")
    # month = int(date_tokens[0])
    # day = int(date_tokens[1])
    # year = int(date_tokens[2])
    # try:
    #    d = datetime.datetime(year, month, day)
    #    try:
    #        current_caregiver.upload_availability(d)
    #        print("Availability uploaded!")
    #    except:
    #        print("Upload Availability Failed")
    # except ValueError:
    #    print("Please enter a valid date!")
    # except pymssql.Error as db_err:
    #    print("Error occurred when uploading availability")


# cancels appointment of currently logged in user based on ID. Not allowed to cancel appointments that do
# not exist or are under a different user
def cancel(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        # HERE
        if len(tokens) != 2:
            print("Please try again!")
            return
        app_id = tokens[1]

        cm = ConnectionManager()
        conn = cm.create_connection()
        cursor = conn.cursor(as_dict=True)

        get_app = "SELECT B.Username, B.Patient FROM Booked B WHERE id = %d"
        cursor.execute(get_app, app_id)

        for row in cursor:
            if current_caregiver is not None:  # caregiver logged in
                user = row['Username']
                if user != current_caregiver.username:
                    print("This appointment is under a different user!")
                    return
            else:  # patient logged in
                user = row['Patient']
                if user != current_patient.username:
                    print("This appointment is under a different user!")
                    return

            delete_statement = "DELETE FROM Booked WHERE id = %s"
            cursor.execute(delete_statement, app_id)
            conn.commit()

            print("Appointment ID{} cancelled".format(app_id))
            return

        print("Appointment does not exist")
        return
    else:
        print("Not currently logged in")
    return


def add_doses(tokens):
    #  add_doses <vaccine> <number>
    #  check 1: check if the current logged-in user is a caregiver
    global current_caregiver
    if current_caregiver is None:
        print("Please login as a caregiver first!")
        return

    #  check 2: the length for tokens need to be exactly 3 to include all information (with the operation name)
    if len(tokens) != 3:
        print("Please try again!")
        return

    vaccine_name = str(tokens[1])
    doses = int(tokens[2])
    vaccine = None
    try:
        try:
            vaccine = Vaccine(vaccine_name, doses).get()
        except:
            print("Failed to get Vaccine!")
            return
    except pymssql.Error:
        print("Error occurred when adding doses")

    # check 3: if getter returns null, it means that we need to create the vaccine and insert it into the Vaccines
    #          table

    if vaccine is None:
        try:
            vaccine = Vaccine(vaccine_name, doses)
            try:
                vaccine.save_to_db()
            except:
                print("Failed To Save")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")
    else:
        # if the vaccine is not null, meaning that the vaccine already exists in our table
        try:
            try:
                vaccine.increase_available_doses(doses)
            except:
                print("Failed to increase available doses!")
                return
        except pymssql.Error:
            print("Error occurred when adding doses")

    print("Doses updated!")

# shows all appointments of current
def show_appointments(tokens):
    global current_caregiver
    global current_patient

    cm = ConnectionManager()
    conn = cm.create_connection()
    cursor = conn.cursor(as_dict=True)

    if current_caregiver is not None:  # caregiver logged in
        print("Current appointments for {}:".format(current_caregiver.username))
        get_apps = "SELECT * FROM Booked B WHERE B.Username = %s"
        cursor.execute(get_apps, current_caregiver.username)
        for row in cursor:
            app_id = row['id']
            v_name = row['v_name']
            date = row['Time']
            other_name = row['Patient']
            print("Appointment ID:{} on {} for the {} vaccine with patient {}".format(app_id, date, v_name, other_name))
    else:  # patient logged in
        print("Current appointments for {}:".format(current_patient.username))
        get_apps = "SELECT * FROM Booked B WHERE B.Patient = %s"
        cursor.execute(get_apps, current_patient.username)
        for row in cursor:
            app_id = row['id']
            v_name = row['v_name']
            date = row['Time']
            other_name = row['Username']
            print(
                "Appointment ID:{} on {} for the {} vaccine with caregiver {}".format(app_id, date, v_name, other_name))

    return

# logs out of current user's session
def logout(tokens):
    global current_caregiver
    global current_patient
    if current_caregiver is not None or current_patient is not None:
        current_caregiver = None
        current_patient = None
        print("Logged Out")
    else:
        print("Not currently logged in")
    return


def start():
    stop = False
    random.seed(a=None, version=2)
    while not stop:
        print()
        print(" *** Please enter one of the following commands *** ")
        print("> create_patient <username> <password>")
        print("> create_caregiver <username> <password>")
        print("> login_patient <username> <password>")
        print("> login_caregiver <username> <password>")
        print("> search_caregiver_schedule <date>")
        print("> reserve <date> <vaccine>")
        print("> upload_availability <date>")
        print("> cancel <appointment_id>")
        print("> add_doses <vaccine> <number>")
        print("> show_appointments")
        print("> logout")
        print("> Quit")
        print()
        response = ""
        print("> Enter: ", end='')

        try:
            response = str(input())
        except ValueError:
            print("Type in a valid argument")
            break

        response = response.lower()
        tokens = response.split(" ")
        if len(tokens) == 0:
            ValueError("Try Again")
            continue
        operation = tokens[0]
        if operation == "create_patient":
            create_patient(tokens)
        elif operation == "create_caregiver":
            create_caregiver(tokens)
        elif operation == "login_patient":
            login_patient(tokens)
        elif operation == "login_caregiver":
            login_caregiver(tokens)
        elif operation == "search_caregiver_schedule":
            search_caregiver_schedule(tokens)
        elif operation == "reserve":
            reserve(tokens)
        elif operation == "upload_availability":
            upload_availability(tokens)
        elif operation == cancel:
            cancel(tokens)
        elif operation == "add_doses":
            add_doses(tokens)
        elif operation == "show_appointments":
            show_appointments(tokens)
        elif operation == "logout":
            logout(tokens)
        elif operation == "quit":
            print("Thank you for using the scheduler, Goodbye!")
            stop = True
        elif operation == "cancel":
            cancel(tokens)
        else:
            print("Invalid Argument")


if __name__ == "__main__":
    '''
    // pre-define the three types of authorized vaccines
    // note: it's a poor practice to hard-code these values, but we will do this ]
    // for the simplicity of this assignment
    // and then construct a map of vaccineName -> vaccineObject
    '''

    # start command line
    print()
    print("Welcome to the COVID-19 Vaccine Reservation Scheduling Application!")

    global Util
    Util = Util()

    start()
