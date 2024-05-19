class Flight:
    def __init__(self, db_connection):
        self.db = db_connection

    def search_flights(self, origin, destination, date):
        cursor = self.db.cursor()
        query = """
        SELECT f.FLIGHTNUM, f.ORIGIN, f.DEST, fs.DEP_TIME, fs.ARR_TIME 
        FROM Flight f
        JOIN Flight_Schedule fs ON f.FLIGHTNUM = fs.FLIGHTNUM 
        WHERE f.ORIGIN = ? AND f.DEST = ? AND fs.DATE = ?
        """
        cursor.execute(query, (origin, destination, date))
        return cursor.fetchall()

class Staff:
    def __init__(self, db_connection):
        self.db = db_connection
    # Add methods for Staff operations

class Airplane:
    def __init__(self, db_connection):
        self.db = db_connection
    # Add methods for Airplane operations

class City:
    def __init__(self, db_connection):
        self.db = db_connection
    # Add methods for City operations

class Booking:
    def __init__(self, db_connection):
        self.db = db_connection

    def get_bookings(self, passenger_id):
        cursor = self.db.cursor()
        query = """
        SELECT b.BookingID, b.FLIGHTNUM, b.NumAdults, b.NumChildren, b.BookingStatus, 
               f.ORIGIN, f.DEST, fs.DATE, fs.DEP_TIME, fs.ARR_TIME
        FROM Bookings b
        JOIN Flight f ON b.FLIGHTNUM = f.FLIGHTNUM
        JOIN Flight_Schedule fs ON f.FLIGHTNUM = fs.FLIGHTNUM
        WHERE b.PASSENGER_ID = ?
        """
        cursor.execute(query, (passenger_id,))
        return cursor.fetchall()
    
    def cancel_booking(self, booking_id):
        cursor = self.db.cursor()
        query = "DELETE FROM Bookings WHERE BookingID = ?"
        cursor.execute(query, (booking_id,))
        self.db.commit()


class AirlineFacade:
    def __init__(self, db_connection):
        self.flights = Flight(db_connection)
        self.staff = Staff(db_connection)
        self.airplanes = Airplane(db_connection)
        self.cities = City(db_connection)
        self.booking = Booking(db_connection)

    def add_new_flight(self, flight_details):
        return self.flights.add_flight(flight_details)

    def get_all_staff(self):
        return self.staff.get_all_staff()

    def search_flights(self, origin, destination, date):
        try:
            return self.flights.search_flights(origin, destination, date)
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def get_bookings(self, passenger_id):
        return self.booking.get_bookings(passenger_id)
    
    def cancel_booking(self, booking_id):
        return self.booking.cancel_booking(booking_id)
