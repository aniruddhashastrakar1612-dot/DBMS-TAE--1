from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import date

app = Flask(__name__)

DATABASE = "travel_agency.db"


# Connect to database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Create tables and insert sample packages
def initialize_database():
    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            package_id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_name TEXT NOT NULL,
            destination TEXT NOT NULL,
            duration INTEGER NOT NULL,
            price REAL NOT NULL,
            available_seats INTEGER NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            email TEXT NOT NULL,
            travel_date TEXT NOT NULL,
            persons INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            FOREIGN KEY (package_id) REFERENCES packages(package_id)
        )
    """)

    # Add sample packages only if table is empty
    count = conn.execute(
        "SELECT COUNT(*) FROM packages"
    ).fetchone()[0]

    if count == 0:
        packages = [
            ("Goa Beach Holiday", "Goa", 4, 12000, 20),
            ("Manali Adventure", "Manali", 5, 15000, 15),
            ("Kerala Backwaters", "Kerala", 6, 18000, 12),
            ("Rajasthan Heritage Tour", "Rajasthan", 7, 22000, 10),
            ("Kashmir Paradise", "Kashmir", 6, 25000, 8)
        ]

        conn.executemany("""
            INSERT INTO packages
            (package_name, destination, duration, price, available_seats)
            VALUES (?, ?, ?, ?, ?)
        """, packages)

    conn.commit()
    conn.close()


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Display all packages
@app.route("/packages")
def packages():
    conn = get_db_connection()
    package_list = conn.execute(
        "SELECT * FROM packages"
    ).fetchall()
    conn.close()

    return render_template(
        "packages.html",
        packages=package_list
    )


# Booking form
@app.route("/book/<int:package_id>", methods=["GET", "POST"])
def book(package_id):

    conn = get_db_connection()

    package = conn.execute(
        "SELECT * FROM packages WHERE package_id = ?",
        (package_id,)
    ).fetchone()

    if package is None:
        conn.close()
        return "Package not found"

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        email = request.form["email"]
        travel_date = request.form["travel_date"]
        persons = int(request.form["persons"])

        # Check date
        if travel_date < str(date.today()):
            conn.close()
            return "Please select a future travel date."

        # Check available seats
        if persons > package["available_seats"]:
            conn.close()
            return "Not enough seats available."

        # Insert booking
        conn.execute("""
            INSERT INTO bookings
            (package_id, customer_name, email, travel_date,
             persons, booking_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            package_id,
            customer_name,
            email,
            travel_date,
            persons,
            str(date.today())
        ))

        # Reduce available seats
        conn.execute("""
            UPDATE packages
            SET available_seats = available_seats - ?
            WHERE package_id = ?
        """, (persons, package_id))

        conn.commit()
        conn.close()

        return redirect(url_for("success"))

    conn.close()

    return render_template(
        "book.html",
        package=package
    )


# Display bookings
@app.route("/bookings")
def bookings():

    conn = get_db_connection()

    booking_list = conn.execute("""
        SELECT bookings.*, packages.package_name,
               packages.destination, packages.price
        FROM bookings
        JOIN packages
        ON bookings.package_id = packages.package_id
        ORDER BY bookings.booking_id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "bookings.html",
        bookings=booking_list
    )


# Success page
@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)