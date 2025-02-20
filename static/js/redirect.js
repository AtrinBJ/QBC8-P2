// static/js/redirect.js

// Get the element where we will display the countdown
let countdownElement = document.getElementById("countdown-timer");

// Set the countdown time in seconds (e.g., 5 seconds)
let countdownTime = 8;

// Update the countdown every second
let countdownInterval = setInterval(function() {
    countdownElement.innerText = countdownTime;  // Show the countdown

    // Decrease the countdown by 1
    countdownTime--;

    // If the countdown reaches 0, redirect the user
    if (countdownTime < 0) {
        clearInterval(countdownInterval);  // Clear the interval
        window.location.href = "/accounts/signup";  // Redirect to signup page
    }
}, 1000);  // 1000ms = 1 second
