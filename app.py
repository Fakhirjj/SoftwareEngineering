from flask import Flask, render_template, request, redirect, url_for, session
import pyodbc
from model import AirlineFacade

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For session management

# SQL Server connection setup
server = 'FAKHIRPC'
database = 'AirlineFakhir'
username = 'sa'
password = 'Password'
driver = '{ODBC Driver 17 for SQL Server}'

connection_string = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
conn = pyodbc.connect(connection_string)
facade = AirlineFacade(conn)  # Assuming facade abstracts all DB operations

@app.route('/')
def hello():
    return '''
    Welcome to the Airline Management System! <br>
    <a href="/login">Login</a><br>
    <a href="/register">Register</a><br>
    <a href="/bookings/view">View Bookings</a><br>
    '''

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname']
        surname = request.form['surname']

        # Insert new passenger into the Passenger table
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
            session['passenger_id'] = passenger.PASSENGER_ID  # Store passenger_id in session
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

    # Debugging information
    print(f"Origin: {origin}, Destination: {destination}, Date: {date}")
    print(f"Flights found: {flights}")

    return render_template('flight_results.html', flights=flights, passenger_id=passenger_id)

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

        # Redirect to the confirmation page with a success message
        return redirect(url_for('booking_confirmation', success_message="Booking successfully created!"))

    except Exception as e:
        # Log the error and redirect to the results page with an error message
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
    
    bookings = facade.get_bookings(passenger_id)  # Facade retrieves bookings
    return render_template('view_bookings.html', bookings=bookings)

@app.route('/bookings/cancel/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    result = facade.cancel_booking(booking_id)  # Facade handles booking cancellation
    return redirect(url_for('view_bookings'))

if __name__ == '__main__':
    app.run(debug=True)
