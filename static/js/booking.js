document.addEventListener("DOMContentLoaded", () => {
    // Get train details from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const trainNumber = urlParams.get('train');
    const trainName = urlParams.get('train_name') || "Shatabdi Express"; // Fallback name
    const journeyDate = urlParams.get('date');
    const baseFare = parseFloat(urlParams.get('base_fare'));
    const seatClass = urlParams.get('class');

    // Populate the summary box
    document.getElementById('summary-train-name').innerText = `${trainNumber} - ${trainName}`;
    document.getElementById('summary-journey-date').innerText = journeyDate;
    document.getElementById('summary-seat-class').innerText = seatClass;
    document.getElementById('summary-base-fare').innerText = `₹${baseFare.toFixed(2)}`;
    document.getElementById('summary-total-fare').innerText = `₹${baseFare.toFixed(2)}`;

    // Handle form submission
    const bookingForm = document.getElementById("booking-form");
    if (bookingForm) {
        bookingForm.addEventListener("submit", (e) => {
            e.preventDefault();
            
            // --- THIS IS THE NEW LOGIC ---
            // Instead of calling the API, we save the data and redirect.
            
            const passengerName = document.getElementById("passenger-name").value;
            const passengerAge = document.getElementById("passenger-age").value;
            const passengerGender = document.getElementById("passenger-gender").value;
            // !!! NEW LINE ADDED !!!
            const berthPreference = document.getElementById("berth-preference").value;

            // 1. Store all booking data in localStorage
            const bookingDetails = {
                train_number: trainNumber,
                train_name: trainName,
                journey_date: journeyDate,
                seat_class: seatClass,
                total_fare: baseFare,
                name: passengerName,
                age: passengerAge,
                gender: passengerGender,
                // !!! NEW LINE ADDED !!!
                preference: berthPreference 
            };
            
            // We use localStorage to pass this data to the payment page
            localStorage.setItem("pendingBooking", JSON.stringify(bookingDetails));

            // 2. Redirect to the payment page
            window.location.href = "/payment";
        });
    }
});