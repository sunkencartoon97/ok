document.addEventListener("DOMContentLoaded", () => {
    const resultsContainer = document.getElementById("results-container");
    const loadingSpinner = document.getElementById("loading-spinner");
    
    // Get search params from URL
    const urlParams = new URLSearchParams(window.location.search);
    const fromStation = urlParams.get('from');
    const toStation = urlParams.get('to');
    const searchDate = urlParams.get('date');

    // --- 1. Fetch Train Search Results ---
    async function fetchTrainResults() {
        try {
            const response = await fetch(`/api/search_trains?from=${fromStation}&to=${toStation}`);
            const results = await response.json();

            loadingSpinner.classList.add("hidden");
            if (results && results.length > 0) {
                displayResults(results);
            } else {
                resultsContainer.innerHTML = `<p class="text-center text-gray-600">No trains found for this route.</p>`;
            }
        } catch (err) {
            console.error("Error fetching search results:", err);
            loadingSpinner.classList.add("hidden");
            resultsContainer.innerHTML = `<p class="text-center text-red-600">Error loading results. Please try again.</p>`;
        }
    }

    function displayResults(results) {
        resultsContainer.innerHTML = ""; // Clear
        results.forEach(train => {
            // The C++ result is in 'fastest_path_found'
            const pathInfo = train.fastest_path_found; 

            const trainCard = `
                <div class="bg-white shadow-lg rounded-xl overflow-hidden transition-all duration-300 hover:shadow-2xl">
                    <div class="p-6">
                        <div class="grid grid-cols-1 md:grid-cols-5 gap-4 items-center">
                            <!-- Train Name -->
                            <div class="md:col-span-2">
                                <h2 class="text-2xl font-bold text-blue-600">${train.train_name}</h2>
                                <p class="text-sm text-gray-500">(${train.train_number})</p>
                            </div>
                            <!-- Times -->
                            <div class="text-center">
                                <p class="text-xl font-semibold text-gray-800">${train.departure_time}</p>
                                <p class="text-sm text-gray-600">${fromStation}</p>
                            </div>
                            <div class="text-center text-gray-500">
                                <!-- Path info from C++ -->
                                <p class="text-sm font-medium">${pathInfo}</p>
                                <div class="w-full h-0.5 bg-gray-300 my-1"></div>
                                <p class="text-xs">Direct Route</p>
                            </div>
                            <div class="text-center">
                                <p class="text-xl font-semibold text-gray-800">${train.arrival_time}</p>
                                <p class="text-sm text-gray-600">${toStation}</p>
                            </div>
                        </div>
                    </div>
                    <!-- Footer with Price and Book Button -->
                    <div class="bg-gray-50 p-4 flex justify-between items-center">
                        <div>
                            <p class="text-sm text-gray-600">Starting from</p>
                            <p class="text-2xl font-bold text-green-600">₹${train.base_fare.toFixed(2)}</p>
                        </div>
                        <a href="/book-ticket?train=${train.train_number}&train_name=${train.train_name}&date=${searchDate}&base_fare=${train.base_fare}&class=Sleeper"
                           class="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg shadow-md hover:bg-blue-700 transition-all">
                            Book Now
                        </a>
                    </div>
                </div>
            `;
            resultsContainer.innerHTML += trainCard;
        });
    }

    // --- 2. Handle Map Modal ---
    const mapModal = document.getElementById("map-modal");
    const viewMapBtn = document.getElementById("view-map-btn");
    const closeMapBtn = document.getElementById("close-map-btn");
    const mapContainer = document.getElementById("map-container");
    const mapLoadingText = document.getElementById("map-loading-text");
    let mapLoaded = false;

    viewMapBtn.addEventListener("click", async () => {
        mapModal.classList.remove("hidden");
        
        if (mapLoaded) return; // Don't load map twice

        mapLoadingText.innerText = "Loading map, this may take a moment...";

        try {
            // Call the new API endpoint to get the map HTML
            const response = await fetch(`/api/get_route_map?from=${fromStation}&to=${toStation}`);
            if (!response.ok) {
                throw new Error('Map generation failed');
            }
            
            const mapHtml = await response.text();
            
            // Inject the map HTML into an iframe
            mapLoadingText.classList.add("hidden");
            const iframe = document.createElement('iframe');
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            iframe.srcdoc = mapHtml; // This is the key part
            
            mapContainer.appendChild(iframe);
            mapLoaded = true;

        } catch (err) {
            console.error("Error fetching map:", err);
            mapContainer.innerHTML = `<p class="text-center text-red-600">Could not load map. Please try again.</p>`;
        }
    });

    closeMapBtn.addEventListener("click", () => {
        mapModal.classList.add("hidden");
    });

    // Run the initial search on page load
    fetchTrainResults();
});