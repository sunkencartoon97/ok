USE railway_management_system;

/* Populate the 'Stations' table (Nodes) */
INSERT INTO Stations (station_code, station_name, latitude, longitude) VALUES
('DEL', 'Delhi', 28.6139, 77.2090),
('AGR', 'Agra', 27.1767, 78.0081),
('JAI', 'Jaipur', 26.9124, 75.7873),
('BHO', 'Bhopal', 23.2599, 77.4126),
('AHM', 'Ahmedabad', 23.0225, 72.5714),
('MUM', 'Mumbai', 19.0760, 72.8777),
('GOA', 'Goa', 15.2993, 74.1240),
('HYD', 'Hyderabad', 17.3850, 78.4867),
('CHE', 'Chennai', 13.0827, 80.2707),
('BAN', 'Bangalore', 12.9716, 77.5946),
('COI', 'Coimbatore', 11.0168, 76.9558),
('TRI', 'Trivandrum', 8.5241, 76.9366),
('PUN', 'Pune', 18.5204, 73.8567),
('NAG', 'Nagpur', 21.1458, 79.0882);

/* Populate the 'Routes' table (Edges) with placeholder distances */
INSERT INTO Routes (station_a_code, station_b_code, distance_km) VALUES
('DEL', 'AGR', 233),
('AGR', 'JAI', 241),
('AGR', 'BHO', 508),
('BHO', 'NAG', 390),
('NAG', 'HYD', 500),
('HYD', 'MUM', 709),
('MUM', 'PUN', 149),
('MUM', 'GOA', 590),
('GOA', 'BAN', 559),
('BAN', 'COI', 363),
('COI', 'TRI', 416),
('HYD', 'CHE', 627),
('CHE', 'BAN', 347);