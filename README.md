Online Quiz System

Project Overview

This is a comprehensive online quiz system built using Flask, SQLite, and modern frontend technologies. The system allows users to take quizzes across various categories, tracks their progress, and provides detailed analytics. It includes a full-featured support ticket system and an admin panel for content management.

Features
User Management

Registration System: Secure user registration with email verification
Multiple Login Methods: Login via password or email verification code
Profile Management: Users can view and edit their profiles
Account Security: Email verification for sensitive account changes
Account Deletion: Option to delete account with email confirmation

Quiz System

Multiple Categories: Quizzes organized by subject categories
Randomized Questions: Questions and answer options are randomized for each attempt
Configurable Quiz Length: Users can select the number of questions for each quiz
Timed Quizzes: 10-minute countdown timer for each quiz
Progress Tracking: Quiz results are saved for user performance tracking
Real-time Scoring: Immediate feedback on quiz completion

Analytics Dashboard

Personal Progress Charts: Visual representation of user performance over time
Category Performance: Analysis of strengths and weaknesses by category
Score Distribution: Statistical breakdown of user scores
Difficulty Analysis: Performance metrics based on question difficulty
Time Analysis: Response time tracking for performance improvement
Comparative Statistics: User performance compared to system averages

Support Ticket System

Ticket Creation: Users can create support tickets with various issue types
File Attachments: Support for file uploads with tickets (images, documents, etc.)
Ticket Status Tracking: Monitor ticket status (Open, In Progress, Closed)
Ticket History: Complete history of all communications
Ticket Editing: Users can edit ticket details and messages
Ticket Reopening: Closed tickets can be reopened if needed

Admin Panel

Question Management: Add, edit, delete, and view all questions
External Question Import: Import questions from the Open Trivia Database API
User Management: View and analyze user performance
Analytics Dashboard: Comprehensive system statistics and analytics
Ticket Management: Respond to and manage support tickets
Export Functionality: Export analytics data to Excel for further analysis

Technologies Used
Backend

Flask: Python web framework for the application core
SQLAlchemy: ORM for database interactions
Flask-Login: User session management
Werkzeug: Security and password hashing
Flask-Mail: Email sending functionality for verification
SQLite: Lightweight database for data storage
Python dateutil: Enhanced date manipulation

Frontend

Bootstrap 5: Responsive UI framework
Chart.js: Interactive data visualization
JavaScript: Enhanced user interactions and form validations
jQuery: DOM manipulation and AJAX calls
CSS3: Custom styling with animations

Development Tools

Git: Version control
Virtual Environment: Isolated development environment
Requirements.txt: Dependency management

Implementation Details
Data Models

User: Stores user account information and authentication details
Question: Contains quiz questions, categories, and answer options
QuizResult: Records user quiz attempts and scores
Ticket & TicketMessage: Support ticket system with message threading
TicketAttachment: File attachment system for the ticket module
VerificationCode: Email verification system for security operations

Security Features

Password Hashing: Secure password storage using Werkzeug
Email Verification: Two-factor verification for sensitive operations
Form Validation: Client and server-side validation
Session Management: Secure user sessions with Flask-Login
Error Handling: Comprehensive error pages and logging
Input Sanitization: Protection against common web vulnerabilities

Responsive Design

Mobile-Friendly Interface: Fully responsive design works on all devices
Accessibility Features: Semantic HTML and screen-reader support
RTL Support: Full right-to-left language support for Persian/Arabic
Dark Theme: Dark-themed UI for better readability and reduced eye strain

Quiz Engine Features

Randomized Questions: Questions are randomly selected from the database
Randomized Options: Answer options are shuffled for each question
Time Limits: Enforced time limits with automatic submission
Progress Tracking: Visual progress bar during quiz taking
Result Analysis: Detailed breakdown of quiz performance

Components Breakdown
User Interface

Base Template: Common layout with navigation and footer
Home Page: Category selection and quiz overview
Quiz Interface: Interactive quiz taking environment
Profile Dashboard: User statistics and progress charts
Admin Dashboard: System management and analytics

Backend Logic

Authentication System: Registration, login, and session management
Quiz Engine: Question selection, scoring, and result processing
Analytics Engine: Data processing for charts and statistics
Ticket System: Support ticket creation and management
Email System: Verification code generation and delivery

Database Schema

Users Table: User account information
Questions Table: Quiz content with correct and incorrect answers
QuizResults Table: Records of completed quizzes
Tickets & Messages Tables: Support ticket system
VerificationCodes Table: Email verification system


--------------------------------Development Notes----------------------------------------

The application uses Flask's development server by default
For production deployment, use a WSGI server like Gunicorn
Email verification requires proper SMTP settings in app.py
For larger deployments, consider migrating to PostgreSQL
The static folder contains all CSS, JS, and image assets
Templates are organized by feature area (admin, tickets, errors)

--------------------------------Future Improvements--------------------------------------

Internationalization support for multiple languages
Advanced question types (matching, fill-in-the-blank)
Social login integration (Google, GitHub, etc.)
Real-time notifications using WebSockets
Mobile application using the existing backend API
Enhanced admin analytics with machine learning insights
Performance optimizations for large question databases
API endpoints for third-party integrations

License

------This project is licensed under the MIT License - see the LICENSE file for details.
Credits------

------Developed as part of the Quera.org,QBC8-Bootcamps,python-Alpha-Bootcamp,2nd-Group, Fall 2024------





(((((((
------------------------------Directory and File Structure----------------------------

-------See the code version for a better view------

quiz-system/
│
├── app.py                   # Main application file - contains routes and core settings
│
├── static/                  # Static files 
│   ├── css/
│   │   ├── error.css        # Error page styles
│   │   └── style.css        # Main styles
│   │
│   ├── images/
│   │   └── background.jpg   # Site background image
│   │
│   ├── js/
│   │   ├── analytics.js     # Analytics and chart scripts
│   │   └── script.js        # General scripts
│   │
│   └── uploads/             # Uploaded files directory
│       └── tickets/         # Ticket attachment files
│           └── README.md    # Upload directory description
│
├── templates/               # HTML templates
│   ├── admin/               # Admin panel templates
│   │   ├── analytics.html   # Analytics and reporting
│   │   └── questions.html   # Question management
│   │
│   ├── errors/              # Error page templates
│   │   ├── 400.html         # 400 error (Bad Request)
│   │   ├── 403.html         # 403 error (Forbidden)
│   │   ├── 404.html         # 404 error (Not Found)
│   │   ├── 500.html         # 500 error (Server Error)
│   │   ├── error-bear.svg   # Error bear SVG image
│   │   └── generic.html     # Generic error template
│   │
│   ├── tickets/             # Ticket system templates
│   │   ├── edit.html        # Edit ticket
│   │   ├── list.html        # Ticket list
│   │   ├── new.html         # Create new ticket
│   │   └── view.html        # View ticket
│   │
│   ├── base.html            # Base template for all pages
│   ├── edit_profile.html    # Profile edit page
│   ├── index.html           # Home page
│   ├── login.html           # Login page
│   ├── profile.html         # User profile page
│   ├── quiz.html            # Quiz questions page
│   ├── register.html        # Registration page
│   └── verify_email.html    # Email verification page
│
├── logs/                    # Log files directory
│
├── create_admin.py          # Admin user creation script
├── create_db.py             # Database creation script
├── migrate_attachments.py   # Migration script for ticket attachments
├── migrate_tickets.py       # Migration script for tickets
├── requirements.txt         # Project dependencies
├── uninstall.bat            # Uninstallation script (Windows)
└── users.db                 # SQLite database file
))))))))

----------------------------Main Files Description-------------------------------------

app.py: The main application file containing all routes, data models, and core logic. This file implements all core system operations including authentication, quiz management, and ticket system.

static/: Contains static files such as:

css/: Stylesheet files for UI

js/: JavaScript files for user interaction and AJAX functionality

images/: Images and icons used in the site

uploads/: Storage location for user-uploaded files

templates/: HTML templates for rendering web pages, including:

1.Various system sections (login, registration, profile, quiz)
2.Admin section (question management and analytics)
3.Ticket system for support
4.Custom-designed error pages


Helper Scripts:

1.create_admin.py: Creates the initial admin user
2.create_db.py: Creates database tables
3.migrate_attachments.py and migrate_tickets.py: Migration scripts for updating database structure



System Features
This project is an online quiz system with the following features:

User Management:

1.Registration and login
2.Email verification
3.Profile editing
4.Account management


Quiz System:

1.Various question categories
2.Randomized quiz display
3.Calculation and storage of user scores
4.Results display and progress statistics


Analytics Dashboard:

1.User progress charts
2.Category and difficulty level statistics
3.Reporting and user performance analysis


Ticket System:

1.Sending support tickets
2.Responding to tickets
3.File attachments for tickets
4.Ticket status management


Admin Panel:

1.Question management (add, edit, delete)
2.Importing questions from external API
3.User management
4.Viewing and responding to tickets
