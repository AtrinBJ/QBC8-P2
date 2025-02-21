document.addEventListener('DOMContentLoaded', function () {
    // Function to update character counter
    function updateCounter(inputId, counterId, maxLength) {
        const input = document.getElementById(inputId);
        const counter = document.getElementById(counterId);

        // Check if elements exist
        if (!input || !counter) {
            console.error(`Element with ID ${inputId} or ${counterId} not found.`);
            return;
        }

        // Update counter on input
        input.addEventListener('input', function () {
            const length = input.value.length;
            counter.textContent = `${length}/${maxLength}`;

            // Add visual feedback when limit is exceeded
            counter.style.color = length > maxLength ? 'red' : '#666';
        });

        // Initialize counter on page load
        counter.textContent = `${input.value.length}/${maxLength}`;
    }

    // Set up counters for each field
    updateCounter('username', 'username-counter', 20); // Username: max 20 characters
    updateCounter('email', 'email-counter', 80);      // Email: max 80 characters
    updateCounter('password', 'password-counter', 30); // Password: max 30 characters
    updateCounter('confirm_password', 'confirm-password-counter', 30); // Confirm Password: max 30 characters
});
