document.addEventListener("DOMContentLoaded", () => {
    const registerForm = document.getElementById("register-form");
    const messageBox = document.getElementById("message-box");
    const messageText = document.getElementById("message-text");

    if (registerForm) {
        registerForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            // Clear previous messages
            messageBox.classList.add("hidden");
            messageText.innerText = "";

            const username = document.getElementById("username").value;
            const email = document.getElementById("email").value;
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirm-password").value;

            // 1. Frontend validation
            if (password !== confirmPassword) {
                showMessage("Passwords do not match.", "error");
                return;
            }
            if (password.length < 8) {
                showMessage("Password must be at least 8 characters long.", "error");
                return;
            }

            // 2. Send data to the /api/register endpoint
            try {
                const response = await fetch("/api/register", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        username: username,
                        email: email,
                        password: password
                    }),
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    // Success!
                    showMessage("Account created successfully! Redirecting to login...", "success");
                    setTimeout(() => {
                        window.location.href = "/login"; // Redirect to login page
                    }, 2000);
                } else {
                    // Handle errors from the server (e.g., email already exists)
                    showMessage(result.message || "Registration failed.", "error");
                }
            } catch (err) {
                console.error("Registration fetch error:", err);
                showMessage("An error occurred. Please try again.", "error");
            }
        });
    }

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