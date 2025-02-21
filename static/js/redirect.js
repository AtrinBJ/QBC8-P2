// DOM Elements
const countdownElement = document.getElementById('countdown');
const progressBar = document.querySelector('.progress');
const redirectLink = document.querySelector('.redirect-link');

// Configuration
const COUNTDOWN_DURATION = 5; // Countdown duration in seconds
const REDIRECT_URL = "/"; // URL to redirect to

// Initialize Countdown
let seconds = COUNTDOWN_DURATION;

// Update the countdown every second
const timer = setInterval(() => {
    seconds--;
    
    // Update the countdown display
    if (countdownElement) {
        countdownElement.textContent = seconds;
    }

    // Update the progress bar
    if (progressBar) {
        const progressPercentage = seconds / COUNTDOWN_DURATION;
        progressBar.style.transform = `scaleX(${progressPercentage})`;
    }

    // Redirect when countdown reaches 0
    if (seconds <= 0) {
        clearInterval(timer); // Stop the timer

        // Redirect after a short delay
        setTimeout(() => {
            window.location.href = REDIRECT_URL;
        }, 500); // 0.5 second delay for smooth transition
    }
}, 1000); // Run every 1000ms (1 second)

// Manual Redirect (if user clicks the link)
if (redirectLink) {
    redirectLink.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent default link behavior
        clearInterval(timer); // Stop the countdown
        window.location.href = REDIRECT_URL; // Redirect immediately
    });
}