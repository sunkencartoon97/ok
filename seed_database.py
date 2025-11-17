import pymysql.cursors
import os
from dotenv import load_dotenv
import random

# --- 1. CONNECT TO THE DATABASE ---
# (This is the same logic as your new main.py)
load_dotenv()

DB_CONFIG = {
    'host': '127.0.0.1',           
    'user': 'root',                
    'password': os.getenv('DB_PASSWORD'),
    'database': 'railway_management_system',
    'cursorclass': pymysql.cursors.DictCursor
}

def get_db_connection():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        return conn
    except Exception as err:
        print(f"FATAL: Error connecting to MySQL: {err}")
        return None

# --- 2. DATA TO BE GENERATED ---

# Define our mock trains
TRAINS_TO_CREATE = [
    ('12951', 'Mumbai Rajdhani', 1500.00),
    ('12001', 'Shatabdi Express', 800.00),
    ('12859', 'Gitanjali Express', 650.00)
]

# Define the coaches for EACH train
# (Coach Name, Class, Total Berths)
COACH_LAYOUT = [
    ('S1', 'Sleeper', 72),
    ('S2', 'Sleeper', 72),
    ('S3', 'Sleeper', 72),
    ('S4', 'Sleeper', 72),
    ('S5', 'Sleeper', 72),
    ('S6', 'Sleeper', 72),
    ('S7', 'Sleeper', 72),
    ('S8', 'Sleeper', 72),
    ('B1', 'AC3', 64),
    ('B2', 'AC3', 64),
    ('B3', 'AC3', 64),
    ('A1', 'AC2', 48),
    ('H1', 'AC1', 24),
]
# Total seats per train: (8*72) + (3*64) + (1*48) + (1*24) = 872
# Total seats for 3 trains: 872 * 3 = 2,616 (This is > 2000)

def get_berth_type(seat_num, coach_class):
    """Helper function to determine berth type based on seat number."""
    if coach_class == 'Sleeper':
        if seat_num % 8 == 1 or seat_num % 8 == 4: return 'Lower'
        if seat_num % 8 == 2 or seat_num % 8 == 5: return 'Middle'
        if seat_num % 8 == 3 or seat_num % 8 == 6: return 'Upper'
        if seat_num % 8 == 7: return 'Side Lower'
        if seat_num % 8 == 0: return 'Side Upper'
    if coach_class == 'AC3':
        # AC3 has a similar layout but different numbering logic sometimes
        if seat_num % 8 == 1 or seat_num % 8 == 4: return 'Lower'
        if seat_num % 8 == 2 or seat_num % 8 == 5: return 'Middle'
        if seat_num % 8 == 3 or seat_num % 8 == 6: return 'Upper'
        if seat_num % 8 == 7: return 'Side Lower'
        if seat_num % 8 == 0: return 'Side Upper'
    if coach_class == 'AC2':
        if seat_num % 6 == 1 or seat_num % 6 == 3: return 'Lower'
        if seat_num % 6 == 2 or seat_num % 6 == 4: return 'Upper'
        if seat_num % 6 == 5: return 'Side Lower'
        if seat_num % 6 == 0: return 'Side Upper'
    if coach_class == 'AC1':
        return 'Cabin' # AC1 has cabins, not berths
    return 'Window' # Default

# --- 3. SCRIPT FUNCTIONS ---

def clear_inventory_tables(cursor):
    """Clears old data to prevent duplicates."""
    print("Clearing old inventory data...")
    # We must delete in reverse order of creation
    # to avoid foreign key constraint errors.
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")
    cursor.execute("TRUNCATE TABLE Tickets;")
    cursor.execute("TRUNCATE TABLE Seats;")
    cursor.execute("TRUNCATE TABLE Coaches;")
    cursor.execute("TRUNCATE TABLE Trains;")
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")
    print("Old data cleared.")

def generate_inventory_data():
    """Generates and inserts all mock data."""
    conn = get_db_connection()
    if not conn:
        return

    try:
        with conn.cursor() as cursor:
            # Clear old data first
            clear_inventory_tables(cursor)

            seat_data_to_insert = []
            
            # --- Loop 1: Create Trains ---
            print(f"Creating {len(TRAINS_TO_CREATE)} trains...")
            for train_num, train_name, base_fare in TRAINS_TO_CREATE:
                cursor.execute(
                    "INSERT INTO Trains (train_number, train_name, base_fare) VALUES (%s, %s, %s)",
                    (train_num, train_name, base_fare)
                )
                print(f"  Created Train: {train_name} ({train_num})")
                
                # --- Loop 2: Create Coaches for this Train ---
                for coach_name, coach_class, total_berths in COACH_LAYOUT:
                    cursor.execute(
                        "INSERT INTO Coaches (train_number, coach_name, coach_class, total_berths) VALUES (%s, %s, %s, %s)",
                        (train_num, coach_name, coach_class, total_berths)
                    )
                    # Get the 'coach_id' we just created
                    coach_id = cursor.lastrowid
                    
                    # --- Loop 3: Create all Seats for this Coach ---
                    for i in range(1, total_berths + 1):
                        seat_num_str = str(i)
                        berth_type = get_berth_type(i, coach_class)
                        
                        # Add seat to our batch list
                        seat_data_to_insert.append((coach_id, seat_num_str, berth_type))
            
            # --- 4. FAST INSERTION ---
            # Now, insert all 2,616 seats in one single, fast operation
            print(f"\nInserting {len(seat_data_to_insert)} seats into the database...")
            
            seat_query = "INSERT INTO Seats (coach_id, seat_number, berth_type) VALUES (%s, %s, %s)"
            cursor.executemany(seat_query, seat_data_to_insert)

            # Commit all changes
            conn.commit()
            print("Database seeding complete!")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        conn.rollback()
    finally:
        if conn:
            conn.close()

# --- 5. RUN THE SCRIPT ---
if __name__ == "__main__":
    print("Starting database seed script...")
    generate_inventory_data()
    print("Script finished.")