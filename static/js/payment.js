document.addEventListener("DOMContentLoaded", () => {
    const payNowBtn = document.getElementById("pay-now-btn");
    const messageBox = document.getElementById("payment-message-box");
    const messageText = document.getElementById("payment-message-text");

    // 1. Retrieve the booking details from localStorage
    const pendingBookingJSON = localStorage.getItem("pendingBooking");
    if (!pendingBookingJSON) {
        // If no booking info is found, redirect back to the index
        showMessage("No booking details found. Redirecting...", "error");
        setTimeout(() => window.location.href = "/", 2000);
        return;
    }

    const bookingDetails = JSON.parse(pendingBookingJSON);

    // 2. Populate the Order Summary
    document.getElementById("summary-train").innerText = bookingDetails.train_number;
    document.getElementById("summary-date").innerText = bookingDetails.journey_date;
    document.getElementById("summary-passenger").innerText = bookingDetails.name;
    document.getElementById("summary-class").innerText = bookingDetails.seat_class;
    
    // !!! NEW LOGIC ADDED !!!
    if (bookingDetails.preference && bookingDetails.preference !== "ANY") {
        const prefText = bookingDetails.preference.charAt(0).toUpperCase() + bookingDetails.preference.slice(1).toLowerCase();
        // Append the preference to the class
        document.getElementById("summary-class").innerText += ` (${prefText})`;
    }
    // !!! END OF NEW LOGIC !!!

    document.getElementById("summary-total").innerText = `₹${bookingDetails.total_fare.toFixed(2)}`;
    payNowBtn.innerText = `Pay Now (₹${bookingDetails.total_fare.toFixed(2)})`;


    // 3. Handle the "Pay Now" button click
    const paymentForm = document.getElementById("payment-form");
    paymentForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        payNowBtn.disabled = true;
        payNowBtn.innerText = "Processing Payment...";
        payNowBtn.classList.add("opacity-75", "cursor-not-allowed");

        // Simulate a 1-second payment delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        // 4. Now, actually call the booking API
        try {
            const response = await fetch("/api/book_ticket", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                // The entire bookingDetails object (which includes the preference) is sent
                body: JSON.stringify(bookingDetails), 
            });

            const result = await response.json();

            if (response.ok && result.success) {
                // SUCCESS!
                // Clear the pending booking from storage
                localStorage.removeItem("pendingBooking");
                
                // Show success message and redirect to the ticket page
                showMessage("Payment Successful! Booking Confirmed.", "success");
                payNowBtn.innerText = "Success!";
                payNowBtn.classList.remove("bg-green-600", "hover:bg-green-700");
                payNowBtn.classList.add("bg-blue-600");
                
                setTimeout(() => {
                    // Redirect to the seat booking/ticket page with the new PNR
                    window.location.href = `/seat-booking?pnr=${result.pnr}`;
                }, 2000);

            } else {
                // Handle errors (e.g., "Train is Full")
                showMessage(result.message || "Booking failed after payment.", "error");
                payNowBtn.disabled = false;
                payNowBtn.innerText = `Pay Now (₹${bookingDetails.total_fare.toFixed(2)})`;
                payNowBtn.classList.remove("opacity-75", "cursor-not-allowed");
            }
        } catch (err) {
            console.error("Booking API error:", err);
            showMessage("An error occurred. Please try again.", "error");
            payNowBtn.disabled = false;
            payNowBtn.innerText = `Pay Now (₹${bookingDetails.total_fare.toFixed(2)})`;
            payNowBtn.classList.remove("opacity-75", "cursor-not-allowed");
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
});