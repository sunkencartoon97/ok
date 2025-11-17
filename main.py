from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pymysql.cursors
from datetime import date, datetime, timedelta, time
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import ctypes
import os
import random
from dotenv import load_dotenv

# --- 1. SETUP ---
load_dotenv()
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'super_secret_key_for_session_management' 

# --- 2. LOAD C++ BRAIN (DIAGNOSTIC BLOCK) ---
base_dir = os.path.abspath(os.path.dirname(__file__))

# Try loading .dll first (Windows), then .so (Linux/Mac)
lib_path_win = os.path.join(base_dir, "core_logic", "core_logic.dll")
lib_path_nix = os.path.join(base_dir, "core_logic", "core_logic.so")

core_lib = None
try:
    print(f"DEBUG: Attempting to load C++ module from:")
    print(f"DEBUG: Win path: {lib_path_win}")
    print(f"DEBUG: Nix path: {lib_path_nix}")
    
    if os.path.exists(lib_path_win):
        print("DEBUG: Windows file exists. Trying to load...")
        core_lib = ctypes.CDLL(lib_path_win) # <-- This is where it's failing
        print(f"SUCCESS: C++ Logic Loaded from {lib_path_win}")
        
    elif os.path.exists(lib_path_nix):
        print("DEBUG: Linux/Mac file exists. Trying to load...")
        core_lib = ctypes.CDLL(lib_path_nix)
        print(f"SUCCESS: C++ Logic Loaded from {lib_path_nix}")
        
    else:
        # This is the "Offline" error you *think* you're seeing
        print(f"---!!! CRITICAL ERROR: FILE NOT FOUND !!!---")
        print("   os.path.exists() returned FALSE.")
        print("   The file 'core_logic.dll' or '.so' is not in the 'core_logic' folder.")
        
except OSError as e:
    # This is the "Load Failed" error I *know* you are seeing
    print(f"---!!! CRITICAL ERROR: FILE LOAD FAILED !!!---")
    print(f"   The file was FOUND, but Python could not load it.")
    print(f"   THIS IS THE REAL ERROR: {e}")
    print("   This is almost always a 32-bit vs. 64-bit mismatch between Python and G++.")

except Exception as e:
    print(f"---!!! CRITICAL ERROR: UNKNOWN FAILURE !!!---")
    print(f"   An unexpected error occurred: {e}")

# --- 3. DEFINE C++ INTERFACE ---
class BookingResult(ctypes.Structure):
    _fields_ = [("seat_id", ctypes.c_int),
                ("status", ctypes.c_char * 5),
                ("seat_number", ctypes.c_char * 10),
                ("berth_type", ctypes.c_char * 15)]

if core_lib:
    # --- Seat Allocation Logic ---
    core_lib.find_best_seat.argtypes = [
        ctypes.POINTER(ctypes.c_int), 
        ctypes.c_int, 
        ctypes.c_int, 
        ctypes.c_int,
        ctypes.c_char_p 
    ]
    core_lib.find_best_seat.restype = BookingResult
    
    # --- Pathfinding Logic (NEW SIGNATURES) ---
    core_lib.clear_graph.restype = None
    core_lib.clear_graph.argtypes = []

    core_lib.build_graph_with_time.restype = None
    core_lib.build_graph_with_time.argtypes = [
        ctypes.c_char_p, # station_a
        ctypes.c_char_p, # station_b
        ctypes.c_int,    # departure_minutes
        ctypes.c_int     # arrival_minutes
    ]
    
    core_lib.find_fastest_path.restype = ctypes.c_char_p
    core_lib.find_fastest_path.argtypes = [ctypes.c_char_p, ctypes.c_char_p]


# --- 4. DATABASE CONFIG ---
DB_CONFIG = {
    'host': '127.0.0.1', 'user': 'root', 'password': os.getenv('DB_PASSWORD'), 
    'database': 'railway_management_system', 'cursorclass': pymysql.cursors.DictCursor
}
def get_db_connection():
    try: return pymysql.connect(**DB_CONFIG)
    except Exception as err: print(f"DB Error: {err}"); return None

# --- MIDDLEWARE ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session: return redirect(url_for('login'))
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_admin FROM Users WHERE user_id = %s", (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        if not user or not user['is_admin']: return "Access Denied", 403
        return f(*args, **kwargs)
    return decorated_function

# --- 5. WEB ROUTES ---
@app.route("/")
def index(): return render_template("railway-index.html")
@app.route("/search")
def search(): return render_template("train-search.html")
@app.route("/book-ticket")
@login_required 
def book_ticket_form(): return render_template("book-ticket.html")
@app.route("/pnr")
def pnr(): return render_template("pnr-status.html")

@app.route("/payment")
@login_required
def payment_page():
    return render_template("payment.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, password_hash, is_admin FROM Users WHERE email = %s", (request.form['email'],))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], request.form['password']):
            session['user_id'] = user['user_id']
            if user['is_admin']: return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else: error = "Invalid credentials."
    return render_template("login.html", error=error)

@app.route("/register")
def register_page(): return render_template("register.html")
@app.route("/logout")
def logout(): session.clear(); return redirect(url_for('index'))

@app.route("/seat-booking")
@login_required
def seat_booking():
    pnr = request.args.get('pnr')
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        b.pnr_number, b.total_fare, b.train_number, b.booking_status, 
        t.train_name,
        p.name AS passenger_name, p.age, p.gender, p.seat_class,
        ti.status as ticket_status, ti.berth_type, -- Added berth_type
        s.seat_number, 
        c.coach_name
    FROM Bookings b
    JOIN Passengers p ON b.pnr_number = p.pnr_number
    JOIN Trains t ON b.train_number = t.train_number
    LEFT JOIN Tickets ti ON p.passenger_id = ti.passenger_id
    LEFT JOIN Seats s ON ti.seat_id = s.seat_id
    LEFT JOIN Coaches c ON s.coach_id = c.coach_id
    WHERE b.pnr_number = %s AND b.user_id = %s
    """
    cursor.execute(query, (pnr, session.get('user_id')))
    booking_data = cursor.fetchall() 
    conn.close()
    
    if not booking_data: return "Booking not found", 404
    
    first_passenger_data = booking_data[0]
    
    # Add mock data
    first_passenger_data['departure_time'] = '10:00 AM'
    first_passenger_data['arrival_time'] = '06:00 PM'
    first_passenger_data['from_station'] = 'Start Station'
    first_passenger_data['to_station'] = 'End Station'
    
    return render_template("seat-booking.html", booking=first_passenger_data)


@app.route("/manage-bookings")
@login_required
def manage_bookings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT b.pnr_number, b.journey_date, b.total_fare, b.booking_status, t.train_name, t.train_number FROM Bookings b JOIN Trains t ON b.train_number = t.train_number WHERE b.user_id = %s ORDER BY b.journey_date DESC", (session['user_id'],))
    bookings = cursor.fetchall()
    conn.close()
    return render_template("manage-bookings.html", bookings=bookings)

@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as c FROM Bookings WHERE DATE(booked_on) = CURDATE()")
    today = cursor.fetchone()['c']
    cursor.execute("SELECT SUM(total_fare) as r FROM Bookings WHERE booking_status='CONFIRMED'")
    rev = cursor.fetchone()['r']
    cursor.execute("SELECT COUNT(*) as u FROM Users")
    users = cursor.fetchone()['u']
    stats = {'bookings_today': today, 'total_revenue': rev, 'total_users': users, 'bookings_yesterday': 0}
    conn.close()
    return render_template("admin-dashboard.html", stats=stats, audit=[], tickets=[])

# --- 6. API ROUTES (C++ INTEGRATED) ---

@app.route("/api/register", methods=['POST'])
def api_register():
    data = request.get_json()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        hashed = generate_password_hash(data['password'])
        cursor.execute("INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)", (data['username'], data['email'], hashed))
        conn.commit()
        return jsonify({"success": True})
    except pymysql.err.IntegrityError as e:
        if 1062 in e.args:
            return jsonify({"success": False, "message": "An account with this email already exists."}), 400
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    finally: 
        conn.close()

@app.route("/api/pnr_status")
def api_pnr_status():
    pnr = request.args.get('pnr', '').strip()
    if not pnr:
        return jsonify({"success": False, "message": "PNR number is required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        b.pnr_number, b.journey_date, b.booking_status, b.total_fare,
        t.train_number, t.train_name,
        p.name AS passenger_name, p.age, p.gender,
        ti.status AS ticket_status, ti.berth_type, 
        s.seat_number,
        c.coach_name
    FROM Bookings b
    JOIN Trains t ON b.train_number = t.train_number
    JOIN Passengers p ON b.pnr_number = p.pnr_number
    LEFT JOIN Tickets ti ON p.passenger_id = ti.passenger_id
    LEFT JOIN Seats s ON ti.seat_id = s.seat_id
    LEFT JOIN Coaches c ON s.coach_id = c.coach_id
    WHERE b.pnr_number = %s
    """
    
    try:
        cursor.execute(query, (pnr,))
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"success": False, "message": "PNR not found."}), 404
            
        for row in results:
            row['from_station'] = 'Start Station' # Mock data
            row['to_station'] = 'End Station'     # Mock data
            row['departure_time'] = '10:00 AM'  # Mock data
            row['arrival_time'] = '06:00 PM'    # Mock data
            if isinstance(row.get('journey_date'), date):
                row['journey_date'] = row['journey_date'].strftime('%Y-%m-%d')
        
        return jsonify({"success": True, "details": results})

    except Exception as e:
        print(f"PNR Status Error: {e}")
        conn.close()
        return jsonify({"success": False, "message": "Database error."}), 500

# ---!!! THIS IS THE FINAL UPDATED SEARCH API !!!---
@app.route("/api/search_trains")
def api_search_trains():
    from_s = request.args.get('from', '').strip()
    to_s = request.args.get('to', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    path_str = "Calculation Error"
    
    if core_lib:
        try:
            # 1. DEFINE YOUR REAL COLUMN NAMES
            # (These are from your 'DESCRIBE Routes' command)
            STATION_A_COL = "start_station_code"
            STATION_B_COL = "end_station_code"
            
            # 2. Build the query string with new time columns
            sql_query = f"SELECT {STATION_A_COL}, {STATION_B_COL}, departure_time, arrival_time FROM Routes"
            
            cursor.execute(sql_query)
            
            # 3. Call C++: Clear the old graph
            core_lib.clear_graph()

            # 4. Call C++: Build the new graph
            for r in cursor.fetchall():
                dep_time = r['departure_time']
                arr_time = r['arrival_time']

                # --- CRITICAL: Check for NULL data ---
                if not dep_time or not arr_time:
                    print(f"Warning: Skipping route {r[STATION_A_COL]} -> {r[STATION_B_COL]} due to missing time data.")
                    continue

                # Convert Python's `timedelta` (for TIME) to minutes
                dep_minutes = int(dep_time.total_seconds() / 60)
                arr_minutes = int(arr_time.total_seconds() / 60)

                core_lib.build_graph_with_time(
                    r[STATION_A_COL].encode('utf-8'), 
                    r[STATION_B_COL].encode('utf-8'), 
                    dep_minutes, 
                    arr_minutes
                )
            
            # 5. Call C++: Find the fastest path
            res = core_lib.find_fastest_path(from_s.encode('utf-8'), to_s.encode('utf-8'))
            path_str = res.decode('utf-8')

        except Exception as e:
            print(f"C++ Graph Error: {e}")
            path_str = f"C++ Error: {e}"
    else:
        path_str = "C++ Module is OFFLINE"

    # --- This part is just for mock train results ---
    cursor.execute("SELECT * FROM Trains LIMIT 3") 
    trains = cursor.fetchall()
    results = []
    for t in trains:
        results.append({
            "train_number": t['train_number'],
            "train_name": t['train_name'],
            "departure_time": "10:00 AM", # You would get this from the path
            "arrival_time": "06:00 PM",   # You would get this from the path
            "base_fare": float(t['base_fare']),
            "seat_availability": {"Sleeper": {"available": 50, "rac":0, "wl":0}},
            "fastest_path_found": path_str # <-- Display the real C++ result
        })
    conn.close()
    return jsonify(results)

@app.route("/api/check_seats")
def api_check_seats():
    train_num = request.args.get('train')
    journey_date = request.args.get('date')
    seat_class = request.args.get('class', 'Sleeper')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT SUM(total_berths) as total FROM Coaches WHERE train_number = %s AND coach_class = %s", (train_num, seat_class))
        total = cursor.fetchone()['total'] or 0
        cursor.execute("SELECT COUNT(*) as booked FROM Bookings b JOIN Passengers p ON b.pnr_number = p.pnr_number JOIN Tickets t ON p.passenger_id = t.passenger_id WHERE b.train_number = %s AND b.journey_date = %s AND p.seat_class = %s AND t.status = 'CNF'", (train_num, journey_date, seat_class))
        booked = cursor.fetchone()['booked']
        return jsonify({"success": True, "available_seats": (total - booked)})
    except: return jsonify({"success": False, "message": "Error"}), 500
    finally: conn.close()

@app.route("/api/book_ticket", methods=['POST'])
@login_required
def api_book_ticket():
    if not core_lib:
        return jsonify({"success": False, "message": "System Failure: C++ Core Logic Module is OFFLINE."}), 500

    data = request.get_json()
    user_id = session.get('user_id')
    train_num = data['train_number']
    journey_date = data['journey_date']
    seat_class = data['seat_class']
    preference = data.get('preference', 'ANY') 
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. DATA GATHERING
        cursor.execute("SELECT coach_id, total_berths FROM Coaches WHERE train_number = %s AND coach_class = %s LIMIT 1", (train_num, seat_class))
        coach = cursor.fetchone()
        if not coach: return jsonify({"success": False, "message": "No coaches for this class."})
        
        coach_id = coach['coach_id']
        total_seats = coach['total_berths']
        cursor.execute("SELECT seat_id FROM Seats WHERE coach_id = %s ORDER BY seat_id ASC LIMIT 1", (coach_id,))
        first_seat = cursor.fetchone()
        start_id = first_seat['seat_id'] if first_seat else 0

        cursor.execute("""
        SELECT s.seat_number FROM Tickets ti JOIN Seats s ON ti.seat_id = s.seat_id JOIN Passengers p ON ti.passenger_id = p.passenger_id JOIN Bookings b ON p.pnr_number = b.pnr_number
        WHERE b.train_number = %s AND b.journey_date = %s AND s.coach_id = %s AND ti.status = 'CNF'
        """, (train_num, journey_date, coach_id))
        booked_seats = [int(row['seat_number']) for row in cursor.fetchall()]

        # 2. COMPLEX LOGIC (C++'s Job: Algorithm)
        ArrType = ctypes.c_int * len(booked_seats)
        c_occ = ArrType(*booked_seats)
        
        res = core_lib.find_best_seat(
            c_occ, 
            ctypes.c_int(len(booked_seats)), 
            ctypes.c_int(total_seats), 
            ctypes.c_int(start_id),
            preference.encode('utf-8')
        )
        
        status = res.status.decode('utf-8')
        berth_type = res.berth_type.decode('utf-8') 
        
        if status == "WL":
            return jsonify({"success": False, "message": "Train is Full (Waitlist Assigned)"})

        # 3. DATA PERSISTENCE
        pnr = f"PNR{random.randint(10000,99999)}"
        fare = float(data['total_fare'])
        
        cursor.execute("INSERT INTO Bookings (pnr_number, user_id, train_number, journey_date, booking_status, total_fare) VALUES (%s, %s, %s, %s, 'CONFIRMED', %s)", (pnr, user_id, train_num, journey_date, fare))
        cursor.execute("INSERT INTO Passengers (pnr_number, name, age, gender, seat_class) VALUES (%s, %s, %s, %s, %s)", (pnr, data['name'], data['age'], data['gender'], seat_class))
        pass_id = cursor.lastrowid
        
        # We now have the 'berth_type' column from the SQL fix
        cursor.execute("INSERT INTO Tickets (passenger_id, seat_id, status, seat_class, berth_type) VALUES (%s, %s, 'CNF', %s, %s)", (pass_id, res.seat_id, seat_class, berth_type))
        conn.commit()
        
        return jsonify({"success": True, "pnr": pnr, "total_fare": fare})

    except Exception as e:
        conn.rollback()
        print(f"Booking Failed: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

@app.route("/api/cancel_ticket", methods=['POST'])
@login_required
def api_cancel():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Bookings SET booking_status='CANCELLED' WHERE pnr_number=%s AND user_id=%s", (data['pnr_number'], session['user_id']))
        cursor.execute("UPDATE Tickets SET status='CANCELLED' WHERE passenger_id IN (SELECT passenger_id FROM Passengers WHERE pnr_number=%s)", (data['pnr_number'],))
        conn.commit()
        return jsonify({"success": True})
    except: return jsonify({"success": False})
    finally: conn.close()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')