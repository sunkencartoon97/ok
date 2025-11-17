// main.js
// This file contains global JavaScript functionalities for the site.
// It handles redirecting the homepage search form.

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('search-form');

    if (searchForm) {
        searchForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const from = document.getElementById('from').value;
            const to = document.getElementById('to').value;
            const date = document.getElementById('date').value;

            // Redirects the user to the search page, passing the inputs as query parameters.
            window.location.href = `/search?from=${from}&to=${to}&date=${date}`;
        });
    }
});