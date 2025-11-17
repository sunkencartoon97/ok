document.addEventListener("DOMContentLoaded", () => {
    const messageBox = document.getElementById("cancel-message-box");
    const messageText = document.getElementById("cancel-message-text");

    // Find all cancel buttons on the page
    const cancelButtons = document.querySelectorAll(".cancel-btn");

    cancelButtons.forEach(button => {
        button.addEventListener("click", async () => {
            const pnr = button.getAttribute("data-pnr");

            // --- IMPORTANT ---
            // In a real app, you would show a modal pop-up here:
            // "Are you sure you want to cancel PNR [pnr]?"
            // We will skip that for now and cancel immediately.

            try {
                const response = await fetch("/api/cancel_ticket", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ pnr_number: pnr }),
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Success! Update the UI
                    showMessage(`PNR ${pnr} has been successfully cancelled.`, "success");
                    
                    // 1. Update the status text
                    const statusSpan = document.getElementById(`status-${pnr}`);
                    statusSpan.innerText = "CANCELLED";
                    statusSpan.classList.remove("bg-green-100", "text-green-800");
                    statusSpan.classList.add("bg-red-100", "text-red-800");

                    // 2. Remove the cancel button
                    button.outerHTML = `<span class="text-xs text-gray-500">Cancelled</span>`;

                } else {
                    // Show error
                    showMessage(result.message || `Failed to cancel PNR ${pnr}.`, "error");
                }
            } catch (err) {
                console.error("Cancel error:", err);
                showMessage("An error occurred. Please try again.", "error");
            }
        });
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
        // Hide the message after 3 seconds
        setTimeout(() => {
            messageBox.classList.add("hidden");
        }, 3000);
    }
});