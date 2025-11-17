#ifndef CORE_LOGIC_H
#define CORE_LOGIC_H

// --- 1. DEFINE THE BOOKING STRUCTURE ---
// (This part is unchanged)
struct BookingResult {
    int seat_id;
    char status[5];
    char seat_number[10];
    char berth_type[15];
};


// --- 2. DEFINE THE FUNCTION PROTOTYPES ---
#ifdef __cplusplus
extern "C" {
#endif

    // --- SEAT LOGIC ---
    // (This part is unchanged)
    __declspec(dllexport) BookingResult find_best_seat(
        int* occupied_seats, 
        int occupied_count, 
        int total_seats, 
        int seat_id_start,
        const char* preference 
    );


    // --- GRAPH/PATHFINDING LOGIC ---
    
    // !!! NEW FUNCTION: Clears the graph for a new search !!!
    __declspec(dllexport) void clear_graph();

    // !!! UPDATED FUNCTION: Now takes departure and arrival times !!!
    // Times are passed as minutes since midnight (e.g., 10:30 AM = 630)
    __declspec(dllexport) void build_graph_with_time(
        const char* station_a, 
        const char* station_b, 
        int departure_minutes, 
        int arrival_minutes
    );

    // !!! UPDATED FUNCTION: Now finds the *fastest* path !!!
    __declspec(dllexport) const char* find_fastest_path(
        const char* from_station, 
        const char* to_station
    );


#ifdef __cplusplus
}
#endif

#endif // CORE_LOGIC_H