/* ---------------------------------- */
/* --- 1. SETUP & USER TABLES --- */
/* ---------------------------------- */
CREATE DATABASE IF NOT EXISTS railway_management_system;
USE railway_management_system;

CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT 0
);

/* ---------------------------------- */
/* --- 2. GRAPH & ROUTE TABLES --- */
/* ---------------------------------- */

/* The NODES of your graph (the stations) */
CREATE TABLE IF NOT EXISTS Stations (
    station_code VARCHAR(10) PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6)
);

/* The EDGES of your graph (the direct connections) */
/* This is what your C++ route_brain will use */
CREATE TABLE IF NOT EXISTS Routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    station_a_code VARCHAR(10),
    station_b_code VARCHAR(10),
    distance_km INT NOT NULL, /* The "weight" for Dijkstra's algorithm */
    FOREIGN KEY (station_a_code) REFERENCES Stations(station_code),
    FOREIGN KEY (station_b_code) REFERENCES Stations(station_code)
);

/* ---------------------------------- */
/* --- 3. INVENTORY TABLES --- */
/* ---------------------------------- */

/* A list of all your trains */
CREATE TABLE IF NOT EXISTS Trains (
    train_number VARCHAR(10) PRIMARY KEY,
    train_name VARCHAR(100) NOT NULL
);

/* A list of all physical coaches on each train */
CREATE TABLE IF NOT EXISTS Coaches (
    coach_id INT AUTO_INCREMENT PRIMARY KEY,
    train_number VARCHAR(10),
    coach_name VARCHAR(10) NOT NULL, /* e.g., "S4", "B1", "A2" */
    coach_class VARCHAR(20) NOT NULL, /* "Sleeper", "AC3", "AC1" */
    FOREIGN KEY (train_number) REFERENCES Trains(train_number)
);

/* A list of EVERY SINGLE SEAT in your inventory */
CREATE TABLE IF NOT EXISTS Seats (
    seat_id INT AUTO_INCREMENT PRIMARY KEY,
    coach_id INT,
    seat_number VARCHAR(10) NOT NULL, /* e.g., "32" */
    berth_type VARCHAR(20) NOT NULL, /* "Upper", "Middle", "Window" */
    FOREIGN KEY (coach_id) REFERENCES Coaches(coach_id)
);

/* ---------------------------------- */
/* --- 4. BOOKING & TICKET TABLES --- */
/* ---------------------------------- */

/* Stores one PNR per booking, linked to a user and train */
CREATE TABLE IF NOT EXISTS Bookings (
    pnr_number VARCHAR(20) PRIMARY KEY,
    user_id INT,
    train_number VARCHAR(10),
    journey_date DATE NOT NULL,
    booking_status VARCHAR(20) NOT NULL, /* "CONFIRMED", "CANCELLED" */
    total_fare DECIMAL(10, 2),
    booked_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (train_number) REFERENCES Trains(train_number)
);

/* Stores the actual passengers for a PNR */
CREATE TABLE IF NOT EXISTS Passengers (
    passenger_id INT AUTO_INCREMENT PRIMARY KEY,
    pnr_number VARCHAR(20),
    name VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    FOREIGN KEY (pnr_number) REFERENCES Bookings(pnr_number)
);

/*
 This is the "Ticket"
 It links one Passenger to one Seat for one Booking
 This is what controls CNF / RAC / WL status
*/
CREATE TABLE IF NOT EXISTS Tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    passenger_id INT,
    seat_id INT, /* This is NULL if status is WL */
    status VARCHAR(10) NOT NULL, /* "CNF", "RAC", "WL" */
    seat_class VARCHAR(20) NOT NULL, /* "Sleeper", "AC3" */
    FOREIGN KEY (passenger_id) REFERENCES Passengers(passenger_id),
    FOREIGN KEY (seat_id) REFERENCES Seats(seat_id)
);
USE railway_management_system;

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action_type VARCHAR(50),
    details TEXT,
    action_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS maintenance_tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'OPEN',
    issue_description TEXT,
    related_train VARCHAR(50),
    related_station VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);