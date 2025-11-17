document.addEventListener("DOMContentLoaded", () => {
    const pnrInput = document.getElementById("pnr-input");
    const searchBtn = document.getElementById("search-pnr-btn");
    const resultContainer = document.getElementById("ticket-result-container");
    const messageBox = document.getElementById("pnr-message-box");
    const messageText = document.getElementById("pnr-message-text");
    const loadingSpinner = document.getElementById("loading-spinner");

    searchBtn.addEventListener("click", async () => {
        const pnr = pnrInput.value.trim();
        if (!pnr) {
            showMessage("Please enter a PNR number.", "error");
            return;
        }

        // Reset UI
        resultContainer.innerHTML = "";
        resultContainer.classList.add("hidden");
        messageBox.classList.add("hidden");
        loadingSpinner.classList.remove("hidden");

        try {
            const response = await fetch(`/api/pnr_status?pnr=${pnr}`);
            const data = await response.json();

            if (response.ok && data.success) {
                displayTicket(data.details);
            } else {
                showMessage(data.message || "PNR not found.", "error");
            }

        } catch (err) {
            console.error("PNR fetch error:", err);
            showMessage("An error occurred while fetching PNR status.", "error");
        } finally {
            loadingSpinner.classList.add("hidden");
        }
    });

    function showMessage(message, type) {
        messageText.innerText = message;
        if (type === "success") {
            messageBox.classList.remove("bg-red-500", "hidden");
            messageBox.classList.add("bg-green-500");
        } else {
            messageBox.classList.remove("bg-green-500", "hidden");
            messageBox.classList.add("bg-red-500");
        }
    }

    function displayTicket(details) {
        // 'details' is an array of passengers. We'll use the first one for general info.
        const main = details[0];
        
        // Helper function to format status
        const getStatusClass = (status) => {
            if (status === 'CNF') return 'bg-green-500 text-white';
            if (status === 'WL') return 'bg-orange-500 text-white';
            if (status === 'CANCELLED') return 'bg-red-500 text-white';
            return 'bg-gray-400 text-white';
        };

        let passengersHtml = '';
        details.forEach((p, index) => {
            passengersHtml += `
                <tr class="border-b border-gray-200">
                    <td class="px-4 py-3">${index + 1}</td>
                    <td class="px-4 py-3 font-medium">${p.passenger_name}</td>
                    <td class="px-4 py-3">${p.age}</td>
                    <td class="px-4 py-3">${p.gender}</td>
                    <td class="px-4 py-3 font-bold ${getStatusClass(p.ticket_status)}">${p.ticket_status}</td>
                    <td class="px-4 py-3">${p.coach_name} / ${p.seat_number}</td>
                </tr>
            `;
        });

        const ticketHtml = `
            <div class="border-2 border-gray-300 rounded-lg overflow-hidden">
                <!-- Ticket Header -->
                <div class="bg-blue-600 p-4 flex justify-between items-center">
                    <div>
                        <h2 class="text-2xl font-bold text-white">${main.train_number} - ${main.train_name}</h2>
                        <p class="text-blue-100">PNR: <span class="font-bold text-white">${main.pnr_number}</span></p>
                    </div>
                    <div class="text-right">
                        <span class="px-3 py-1 rounded-full text-sm font-medium ${getStatusClass(main.booking_status)}">
                            ${main.booking_status}
                        </span>
                    </div>
                </div>

                <!-- Journey Details -->
                <div class="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <p class="text-sm text-gray-500">From</p>
                        <p class="text-lg font-semibold text-gray-800">${main.from_station}</p>
                        <p class="text-sm text-gray-700">${main.departure_time}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">To</p>
                        <p class="text-lg font-semibold text-gray-800">${main.to_station}</p>
                        <p class="text-sm text-gray-700">${main.arrival_time}</p>
                    </div>
                    <div>
                        <p class="text-sm text-gray-500">Journey Date</p>
                        <p class="text-lg font-semibold text-gray-800">${main.journey_date}</p>
                        <p class="text-sm text-gray-700">Total Fare: <span class="font-bold">₹${main.total_fare}</span></p>
                    </div>
                </div>

                <!-- Passenger Details -->
                <div class="p-6 border-t border-gray-200">
                    <h3 class="text-xl font-semibold text-gray-800 mb-4">Passenger Details</h3>
                    <div class="overflow-x-auto rounded-lg border border-gray-200">
                        <table class="w-full text-left text-sm">
                            <thead class="bg-gray-50">
                                <tr>
                                    <th class="px-4 py-2 font-medium text-gray-600">S.No.</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Name</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Age</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Gender</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Status</th>
                                    <th class="px-4 py-2 font-medium text-gray-600">Seat</th>
                                </tr>
                            </thead>
                            <tbody class="bg-white">
                                ${passengersHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;

        resultContainer.innerHTML = ticketHtml;
        resultContainer.classList.remove("hidden");
    }
});