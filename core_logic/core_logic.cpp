#include "core_logic.h"
#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <unordered_map>
#include <unordered_set>
#include <map> // Using std::map for Dijkstra's
#include <queue> // Using priority_queue for Dijkstra's
#include <limits> // Using std::numeric_limits
#include <sstream> // To build the result string

// --- Static variables to hold C++ state ---
static BookingResult last_result;
static std::string path_result_str;

// --- Helper for Seat Logic ---
// (This is a standard Indian Railways 72-seat layout)
std::string get_berth_type(int seat_num) {
    int mod = seat_num % 8;
    if (mod == 1 || mod == 4) return "LOWER";
    if (mod == 2 || mod == 5) return "MIDDLE";
    if (mod == 3 || mod == 6) return "UPPER";
    if (mod == 7) return "SIDE_LOWER";
    if (mod == 0) return "SIDE_UPPER"; // Seat 8, 16, etc.
    return "UNKNOWN";
}

// --- 1. SEAT LOGIC IMPLEMENTATION (SMART VERSION) ---
// (This function is unchanged from our last step)
extern "C" __declspec(dllexport) BookingResult find_best_seat(
    int* occupied_seats, 
    int occupied_count, 
    int total_seats, 
    int seat_id_start,
    const char* preference
) {
    std::unordered_set<int> booked_set;
    for(int i = 0; i < occupied_count; ++i) {
        booked_set.insert(occupied_seats[i]);
    }
    std::string pref(preference);
    int found_seat_num = -1;
    if (pref != "ANY") {
        for (int i = 1; i <= total_seats; ++i) {
            if (booked_set.find(i) == booked_set.end()) {
                std::string berth_type = get_berth_type(i);
                bool match = false;
                if (pref == "LOWER" && (berth_type == "LOWER" || berth_type == "SIDE_LOWER")) match = true;
                else if (pref == "MIDDLE" && berth_type == "MIDDLE") match = true;
                else if (pref == "UPPER" && (berth_type == "UPPER" || berth_type == "SIDE_UPPER")) match = true;
                else if (pref == "SIDE" && (berth_type == "SIDE_LOWER" || berth_type == "SIDE_UPPER")) match = true;
                if (match) {
                    found_seat_num = i;
                    break;
                }
            }
        }
    }
    if (found_seat_num == -1) {
        for (int i = 1; i <= total_seats; ++i) {
            if (booked_set.find(i) == booked_set.end()) {
                found_seat_num = i;
                break;
            }
        }
    }
    if (found_seat_num != -1) {
        last_result.seat_id = seat_id_start + (found_seat_num - 1);
        std::string berth_type = get_berth_type(found_seat_num);
        strncpy(last_result.status, "CNF", sizeof(last_result.status) - 1);
        snprintf(last_result.seat_number, sizeof(last_result.seat_number), "%d", found_seat_num);
        strncpy(last_result.berth_type, berth_type.c_str(), sizeof(last_result.berth_type) - 1);
    } else {
        last_result.seat_id = -1;
        strncpy(last_result.status, "WL", sizeof(last_result.status) - 1);
        strncpy(last_result.seat_number, "WL", sizeof(last_result.seat_number) - 1);
        strncpy(last_result.berth_type, "WL", sizeof(last_result.berth_type) - 1);
    }
    return last_result;
}

// --- 2. PATHFINDING IMPLEMENTATION (REAL DIJKSTRA) ---

// Represents an edge in our graph
struct Edge {
    std::string to_station;
    int departure_time; // minutes since midnight
    int arrival_time;   // minutes since midnight
    int travel_time;    // duration in minutes
};

// Our graph: map of "Station Name" -> vector of Edges
static std::map<std::string, std::vector<Edge>> adj;

// Helper: Defines how our priority queue will work
// We want to pull the *fastest* path (lowest time) first
using PII = std::pair<int, std::string>; // Pair of (Total Time, Station Name)
struct CompareDist {
    bool operator()(const PII& a, const PII& b) {
        return a.first > b.first;
    }
};

// --- NEW C++ FUNCTIONS ---

// Clears the graph for a new search
extern "C" __declspec(dllexport) void clear_graph() {
    adj.clear();
}

// Builds the graph with time and duration
extern "C" __declspec(dllexport) void build_graph_with_time(
    const char* station_a, 
    const char* station_b, 
    int departure_minutes, 
    int arrival_minutes
) {
    std::string from(station_a);
    std::string to(station_b);
    int duration = arrival_minutes - departure_minutes;
    
    // Handle overnight trains (e.g., depart 23:00, arrive 02:00)
    if (duration < 0) {
        duration += 1440; // Add 24 hours in minutes
    }
    
    adj[from].push_back({to, departure_minutes, arrival_minutes, duration});
}

// Runs Dijkstra's algorithm to find the fastest path
extern "C" __declspec(dllexport) const char* find_fastest_path(
    const char* from_station, 
    const char* to_station
) {
    std::string start(from_station);
    std::string end(to_station);

    // 1. Initialize data structures for Dijkstra's
    std::priority_queue<PII, std::vector<PII>, CompareDist> pq;
    std::map<std::string, int> dist;
    std::map<std::string, std::string> prev; // To reconstruct the path
    // Store arrival time-of-day for calculating layovers
    std::map<std::string, int> arrival_at_node; 

    // Set all distances to "infinity"
    std::unordered_set<std::string> stations;
    for (auto const& [station, edges] : adj) {
        stations.insert(station);
        for (auto const& edge : edges) {
            stations.insert(edge.to_station);
        }
    }
    for (const auto& station : stations) {
        dist[station] = std::numeric_limits<int>::max();
    }


    // 2. Start at the 'from' station
    if (dist.find(start) == dist.end()) {
        path_result_str = "Error: Starting station '" + start + "' not found in routes.";
        return path_result_str.c_str();
    }
    dist[start] = 0;
    arrival_at_node[start] = 0; // Start at time 0
    pq.push({0, start}); // {total time, station name}

    // 3. Run the algorithm
    while (!pq.empty()) {
        int d = pq.top().first; // Total travel time so far
        std::string u = pq.top().second;
        pq.pop();

        if (d > dist[u]) continue;
        if (u == end) break; // Found the destination

        int u_arrival_time = arrival_at_node[u]; // Get the time of day we arrived at station 'u'

        // Look at all neighbors (v) of the current station (u)
        if (adj.find(u) != adj.end()) {
            for (auto const& edge : adj[u]) {
                std::string v = edge.to_station;
                
                int travel_duration = edge.travel_time; 
                int wait_time = 0;
                
                if (u != start) {
                    // Calculate wait time (layover)
                    wait_time = edge.departure_time - u_arrival_time;
                    if (wait_time < 0) {
                        wait_time += 1440; // Wait for the next day
                    }
                }
                
                int total_time = dist[u] + travel_duration + wait_time;

                if (total_time < dist[v]) {
                    dist[v] = total_time;
                    prev[v] = u;
                    arrival_at_node[v] = edge.arrival_time; // Store the new arrival time
                    pq.push({total_time, v});
                }
            }
        }
    }

    // 4. Reconstruct and return the path
    if (dist.find(end) == dist.end() || dist[end] == std::numeric_limits<int>::max()) {
        path_result_str = "No path found from " + start + " to " + end + ".";
    } else {
        std::string path = "";
        std::string curr = end;
        while (curr != start) {
            path = " -> " + curr + path;
            if (prev.find(curr) == prev.end()) {
                path = "Error: Path reconstruction failed" + path;
                break;
            }
            curr = prev[curr];
        }
        path = start + path;
        
        std::stringstream ss;
        int total_mins = dist[end];
        int total_mins = dist[end];
        int hours = total_mins / 60;
        int mins = total_mins % 60;
        
        ss << "Fastest Path: " << path << " (Total time: " << hours << "h " << mins << "m)";
        path_result_str = ss.str();
    }

    return path_result_str.c_str();
}