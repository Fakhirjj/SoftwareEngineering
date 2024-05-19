from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from model import AirlineFacade

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQL Server connection setup
server = 'FAKHIRPC'
database = 'AirlineFakhir'
username = 'sa'
password = 'Password'
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
conn = pyodbc.connect(connection_string)
facade = AirlineFacade(conn)

@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/select_role')
def select_role():
    return render_template('select_role.html')

@app.route('/passenger')
def passenger():
    return redirect(url_for('login'))

@app.route('/staff')
def staff_dashboard():
    return render_template('staff_dashboard.html')

@app.route('/pilot')
def pilot():
    return render_template('pilot_dashboard.html')

@app.route('/admin')
def admin():
    return render_template('admin_dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        surname = request.form['surname']

        cursor = conn.cursor()
        cursor.execute("INSERT INTO Passenger (FIRSTNAME, SURNAME) VALUES (?, ?)", (firstname, surname))
        conn.commit()

        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        firstname = request.form['firstname']
        surname = request.form['surname']

        cursor = conn.cursor()
        cursor.execute("SELECT PASSENGER_ID FROM Passenger WHERE FIRSTNAME = ? AND SURNAME = ?", (firstname, surname))
        passenger = cursor.fetchone()
        
        if passenger:
            session['passenger_id'] = passenger.PASSENGER_ID
            return redirect(url_for('search_flights'))
        else:
            return "Invalid login"
    return render_template('login.html')

@app.route('/flights/search', methods=['GET'])
def search_flights():
    passenger_id = session.get('passenger_id')
    if not passenger_id:
        return "No passenger ID provided. Please log in."
    return render_template('search_flights.html', passenger_id=passenger_id)

@app.route('/flights/results', methods=['POST'])
def flight_results():
    origin = request.form['origin']
    destination = request.form['destination']
    date = request.form['date']
    passenger_id = session.get('passenger_id')
    if not passenger_id:
        return "No passenger ID provided. Please log in."

    flights = facade.search_flights(origin, destination, date)

    success_message = request.args.get('success_message')
    error_message = request.args.get('error_message')
    
    return render_template('flight_results.html', flights=flights, passenger_id=passenger_id, success_message=success_message, error_message=error_message)

@app.route('/bookings/create', methods=['POST'])
def create_booking():
    try:
        flight_id = request.form['flight_id']
        num_adults = request.form['num_adults']
        num_children = request.form['num_children']
        passenger_id = session.get('passenger_id')
        if not passenger_id:
            return "No passenger ID provided. Please log in."

        cursor = conn.cursor()
        query = """INSERT INTO Bookings (PASSENGER_ID, FLIGHTNUM, NumAdults, NumChildren, BookingStatus) 
                   VALUES (?, ?, ?, ?, 'Confirmed')"""
        cursor.execute(query, (passenger_id, flight_id, num_adults, num_children))
        conn.commit()

        return redirect(url_for('booking_confirmation', success_message="Booking successfully created!"))

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return redirect(url_for('flight_results', error_message=f"Error occurred: {str(e)}"))

@app.route('/booking/confirmation')
def booking_confirmation():
    success_message = request.args.get('success_message')
    return render_template('booking_confirmation.html', success_message=success_message)

@app.route('/bookings/view')
def view_bookings():
    passenger_id = session.get('passenger_id')
    if not passenger_id:
        return "No passenger ID provided. Please log in."
    
    bookings = facade.get_bookings(passenger_id)
    error_message = request.args.get('error_message')
    return render_template('view_bookings.html', bookings=bookings, error_message=error_message)

@app.route('/bookings/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    try:
        facade.cancel_booking(booking_id)
        return redirect(url_for('view_bookings'))
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return redirect(url_for('view_bookings', error_message=f"Error occurred: {str(e)}"))

@app.route('/staff/flights/create', methods=['GET', 'POST'])
def create_flight():
    if request.method == 'POST':
        origin = request.form['origin']
        destination = request.form['destination']
        airplane_numser = request.form['airplane_numser']
        empnum = request.form['empnum']
        date = request.form['date']
        dep_time = request.form['dep_time']
        arr_time = request.form['arr_time']

        cursor = conn.cursor()

        # Insert into Flight table
        cursor.execute(
            "INSERT INTO Flight (ORIGIN, DEST, AIRPLANE_NUMSER, EMPNUM) OUTPUT INSERTED.FLIGHTNUM VALUES (?, ?, ?, ?)",
            (origin, destination, airplane_numser, empnum)
        )
        flightnum = cursor.fetchone()[0]

        # Insert into Flight_Schedule table
        cursor.execute(
            "INSERT INTO Flight_Schedule (FLIGHTNUM, DATE, DEP_TIME, ARR_TIME) VALUES (?, ?, ?, ?)",
            (flightnum, date, dep_time, arr_time)
        )
        conn.commit()

        return redirect(url_for('staff_dashboard'))
    return render_template('create_flight.html')

@app.route('/staff/flights/assign', methods=['GET', 'POST'])
def assign_staff():
    if request.method == 'POST':
        flightnum = request.form['flightnum']
        empnum = request.form['empnum']
        role = request.form['role']

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Flight_Staff (FLIGHTNUM, EMPNUM, ROLE) VALUES (?, ?, ?)",
            (flightnum, empnum, role)
        )
        conn.commit()

        return redirect(url_for('staff_dashboard'))
    return render_template('assign_staff.html')

@app.route('/staff/flights/view', methods=['GET'])
def view_existing_flights():
    cursor = conn.cursor()
    query = """
    SELECT f.FLIGHTNUM, f.ORIGIN, f.DEST, a.MANUFACTURER, a.MODEL_NUMBER, s.DATE, s.DEP_TIME, s.ARR_TIME
    FROM Flight f
    JOIN Airplane a ON f.AIRPLANE_NUMSER = a.AIRPLANE_NUMSER
    JOIN Flight_Schedule s ON f.FLIGHTNUM = s.FLIGHTNUM
    """
    cursor.execute(query)
    flights = cursor.fetchall()
    
    return render_template('view_flights.html', flights=flights)

if __name__ == '__main__':
    app.run(debug=True)
