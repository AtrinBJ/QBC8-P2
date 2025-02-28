// متغیرهای سراسری برای مدیریت کوییز
let currentQuestion = 1;
let totalQuestions = 0;
let startTime = Date.now();
let timer;
let isQuizActive = false; // متغیر برای تشخیص فعال بودن کوییز

// اجرای کد پس از لود کامل صفحه
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded");
    const quizForm = document.getElementById('quizForm');

    // فقط در صفحه کوییز اجرا شود
    if (quizForm) {
        console.log("Quiz form found - initializing quiz...");
        totalQuestions = parseInt(quizForm.dataset.totalQuestions) || 0;
        console.log("Total questions:", totalQuestions);
        isQuizActive = true; // کوییز فعال است

        // افزودن Event Listener به لینک‌های خروج
        setupExitConfirmation();

        // نمایش اولین سوال
        showQuestion(1);

        // افزودن Event Listener به دکمه‌های بعدی و قبلی
        document.querySelectorAll('.nav-btn').forEach(button => {
            button.addEventListener('click', function () {
                const direction = this.getAttribute('data-direction');
                const targetQuestion = parseInt(this.getAttribute('data-question'));

                if (isNaN(targetQuestion)) {
                    console.error("Invalid question number");
                    return;
                }

                if (direction === 'next') {
                    // بررسی انتخاب گزینه در سوال فعلی قبل از رفتن به سوال بعد
                    const currentCard = document.getElementById(`question-${currentQuestion}`);
                    if (currentCard) {
                        const selectedOption = currentCard.querySelector('input[type="radio"]:checked');
                        if (!selectedOption) {
                            alert('لطفاً یک گزینه را انتخاب کنید');
                            return;
                        }
                    }
                }

                showQuestion(targetQuestion);
            });
        });

        // افزودن Event Listener به دکمه پایان کوییز
        const finishQuizBtn = document.getElementById('finishQuiz');
        if (finishQuizBtn) {
            console.log("Finish quiz button found");
            finishQuizBtn.addEventListener('click', confirmSubmit);
        } else {
            console.warn("Finish quiz button NOT found!");
        }

        // شروع تایمر برای کوییز (۱۰ دقیقه)
        startTimer(600);
    } else {
        console.log("Not on quiz page - skipping quiz initialization");
    }
});

// تابع جدید برای تنظیم تأیید خروج
function setupExitConfirmation() {
    console.log("Setting up exit confirmation");

    // تنظیم listener برای قبل از بستن صفحه
    window.addEventListener('beforeunload', function(e) {
        if (isQuizActive) {
            e.preventDefault();
            e.returnValue = 'آیا مطمئن هستید که می‌خواهید از کوییز خارج شوید؟ اطلاعات کوییز ذخیره نخواهد شد.';
            return e.returnValue;
        }
    });

    // تنظیم listener برای لینک‌های خروج و ناوبری
    document.querySelectorAll('a[href]:not([href^="#"])').forEach(link => {
        console.log("Adding event listener to link:", link.href);

        link.addEventListener('click', function(event) {
            if (isQuizActive) {
                event.preventDefault();
                const targetHref = this.href;

                // بررسی آیا لینک logout است
                const isLogout = targetHref.includes('logout');

                if (confirm('آیا مطمئن هستید که می‌خواهید از کوییز خارج شوید؟ اطلاعات کوییز ذخیره نخواهد شد.')) {
                    // اگر لینک logout بود به profile هدایت کنیم
                    if (isLogout) {
                        console.log("Logout link detected, redirecting to profile instead");
                        window.location.href = '/profile';
                    } else {
                        // در غیر این صورت به آدرس اصلی هدایت می‌شود
                        window.location.href = targetHref;
                    }
                }
            }
        });
    });

    // به طور خاص برای لینک logout
    const logoutLinks = document.querySelectorAll('a[href*="logout"]');
    logoutLinks.forEach(link => {
        console.log("Found logout link:", link.href);
    });
}

// تابع نمایش سوال مشخص شده
function showQuestion(num) {
    console.log(`Showing question ${num}`);

    // بررسی معتبر بودن شماره سوال
    if (num < 1 || num > totalQuestions) {
        console.error(`Invalid question number: ${num}`);
        return false;
    }

    // مخفی کردن همه سوالات
    document.querySelectorAll('.question-card').forEach(card => {
        card.style.display = 'none';
    });

    // نمایش سوال مورد نظر
    const nextCard = document.getElementById(`question-${num}`);
    if (nextCard) {
        nextCard.style.display = 'block';
        const currentQuestionElement = document.getElementById('currentQuestion');
        if (currentQuestionElement) {
            currentQuestionElement.textContent = num;
        }

        const progressBar = document.getElementById('progressBar');
        if (progressBar) {
            progressBar.style.width = `${(num / totalQuestions) * 100}%`;
        }

        currentQuestion = num;
        return true;
    } else {
        console.error(`Question element #question-${num} not found`);
        return false;
    }
}

// تابع تایید ارسال کوییز
function confirmSubmit() {
    console.log("Confirm submit called");

    // بررسی پاسخ به همه سوالات
    let unansweredQuestions = [];
    for (let i = 1; i <= totalQuestions; i++) {
        const questionCard = document.getElementById(`question-${i}`);
        if (questionCard) {
            const selectedOption = questionCard.querySelector('input[type="radio"]:checked');
            if (!selectedOption) {
                unansweredQuestions.push(i);
            }
        }
    }

    if (unansweredQuestions.length > 0) {
        alert(`لطفاً به تمام سوالات پاسخ دهید. سوالات بدون پاسخ: ${unansweredQuestions.join(', ')}`);
        return;
    }

    if (confirm('آیا مطمئن هستید که می‌خواهید کوییز را به پایان برسانید؟')) {
        console.log("User confirmed submission");
        submitQuiz(false);
    }
}

// تابع ارسال نتایج کوییز
async function submitQuiz(isTimeout = false) {
    console.log("Submit quiz called");
    clearInterval(timer);
    isQuizActive = false; // کوییز دیگر فعال نیست

    const form = document.getElementById('quizForm');
    if (!form) {
        console.error("Quiz form not found!");
        alert("خطا: فرم کوییز پیدا نشد");
        return;
    }

    console.log("Form data:", form.dataset);
    const category = form.dataset.category;
    if (!category) {
        console.error("Category not found in form data");
        alert("خطا: دسته‌بندی کوییز یافت نشد");
        return;
    }

    // جمع‌آوری پاسخ‌ها
    const answers = {};
    let answered = 0;

    // استفاده از querySelector برای پیدا کردن همه radio buttons انتخاب شده
    const selectedOptions = form.querySelectorAll('input[type="radio"]:checked');
    console.log("Selected options:", selectedOptions.length);

    selectedOptions.forEach(option => {
        const name = option.getAttribute('name');
        const value = option.value;
        console.log("Option:", name, value);

        // استخراج شناسه سوال از name (به فرمت question-123)
        const questionId = name.split('-')[1];
        if (questionId) {
            answers[questionId] = value;
            answered++;
        }
    });

    console.log("Collected answers:", answers);
    console.log("Questions answered:", answered, "of", totalQuestions);

    // بررسی تکمیل همه سوالات
    if (!isTimeout && answered < totalQuestions) {
        alert(`لطفاً به تمام سوالات پاسخ دهید. ${totalQuestions - answered} سوال بدون پاسخ مانده است.`);
        isQuizActive = true; // کوییز همچنان فعال است
        return;
    }

    // آماده‌سازی داده برای ارسال
    const submitData = {
        category: category,
        answers: answers,
        time_taken: Math.floor((Date.now() - startTime) / 1000)
    };

    console.log("Data to submit:", submitData);

    try {
        console.log("Sending request to server...");
        const response = await fetch('/submit_quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(submitData)
        });

        console.log("Server response:", response);

        if (!response.ok) {
            console.error("Server returned error:", response.status);
            alert(`خطا از سمت سرور: ${response.status}`);
            isQuizActive = true; // کوییز همچنان فعال است در صورت خطا
            return;
        }

        const result = await response.json();
        console.log("Response data:", result);

        if (result.success) {
            showResult(result.score, result.correct_count, result.total_questions, isTimeout);
        } else {
            alert('خطا در ثبت نتایج: ' + (result.error || 'خطای نامشخص'));
            isQuizActive = true; // کوییز همچنان فعال است در صورت خطا
        }
    } catch (error) {
        console.error('Connection error:', error);
        alert('خطا در ارتباط با سرور: ' + error.message);
        isQuizActive = true; // کوییز همچنان فعال است در صورت خطا
    }
}

// تابع نمایش نتیجه کوییز
function showResult(score, correctAnswers, totalQCount, isTimeout) {
    console.log("Showing result:", score, correctAnswers, totalQCount, isTimeout);

    // بررسی وجود مودال نتیجه
    const resultModal = document.getElementById('resultModal');

    if (!resultModal) {
        console.log("Result modal not found - creating one");

        // ایجاد مودال نتیجه به صورت پویا
        const modalHTML = `
        <div class="modal fade" id="resultModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">نتیجه کوییز</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body text-center">
                        <div id="resultIcon" class="mb-3"></div>
                        <h3>نمره شما: <span id="scorePercentage">${score}</span>%</h3>
                        <p>پاسخ‌های صحیح: <span id="correctAnswers">${correctAnswers}</span> از ${totalQCount || totalQuestions}</p>
                        <div id="resultMessage" class="mt-3"></div>
                    </div>
                    <div class="modal-footer">
                        <a href="/profile" class="btn btn-primary">مشاهده پروفایل</a>
                    </div>
                </div>
            </div>
        </div>`;

        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer.firstChild);

        setTimeout(updateModalContent, 100, score, correctAnswers, totalQCount, isTimeout);
    } else {
        updateModalContent(score, correctAnswers, totalQCount, isTimeout);
    }
}

// تابع به‌روزرسانی محتوای مودال
function updateModalContent(score, correctAnswers, totalQCount, isTimeout) {
    console.log("Updating modal content");

    // به‌روزرسانی محتوای مودال
    const scoreElement = document.getElementById('scorePercentage');
    const correctAnswersElement = document.getElementById('correctAnswers');
    const resultIcon = document.getElementById('resultIcon');
    const resultMessage = document.getElementById('resultMessage');

    if (scoreElement) scoreElement.textContent = score;
    if (correctAnswersElement) correctAnswersElement.textContent = correctAnswers;

    // تعیین وضعیت نتیجه
    if (resultIcon && resultMessage) {
        if (score >= 80) {
            resultIcon.innerHTML = '<i class="bi bi-emoji-smile display-1 text-success"></i>';
            resultMessage.className = 'alert alert-success';
            resultMessage.textContent = 'عالی! عملکرد شما فوق‌العاده بود.';
        } else if (score >= 60) {
            resultIcon.innerHTML = '<i class="bi bi-emoji-neutral display-1 text-warning"></i>';
            resultMessage.className = 'alert alert-warning';
            resultMessage.textContent = 'خوب! اما جای پیشرفت دارید.';
        } else {
            resultIcon.innerHTML = '<i class="bi bi-emoji-frown display-1 text-danger"></i>';
            resultMessage.className = 'alert alert-danger';
            resultMessage.textContent = 'نیاز به تمرین بیشتر دارید.';
        }

        // اضافه کردن پیام مربوط به اتمام زمان
        if (isTimeout) {
            resultMessage.textContent = 'زمان کوییز به پایان رسید. ' + resultMessage.textContent;
        }
    }

    // نمایش مودال نتیجه
    try {
        const resultModal = document.getElementById('resultModal');
        if (resultModal) {
            const bsModal = new bootstrap.Modal(resultModal);
            bsModal.show();

            // هدایت خودکار به صفحه پروفایل بعد از 5 ثانیه
            setTimeout(() => {
                window.location.href = '/profile';
            }, 5000);
        } else {
            console.error("Modal element not found after creation");
            alert(`نمره شما: ${score}%`);
            // هدایت فوری به صفحه پروفایل در صورت عدم وجود مودال
            setTimeout(() => {
                window.location.href = '/profile';
            }, 2000);
        }
    } catch (error) {
        console.error("Error showing modal:", error);
        alert(`نمره شما: ${score}%`);
        // هدایت فوری به صفحه پروفایل در صورت بروز خطا
        setTimeout(() => {
            window.location.href = '/profile';
        }, 2000);
    }
}

// تابع تایمر کوییز
function startTimer(duration) {
    let timeLeft = duration;
    const timerElement = document.getElementById('timer');

    if (!timerElement) {
        console.error("Timer element not found");
        return;
    }

    // نمایش اولیه زمان
    updateTimerDisplay(timeLeft, timerElement);

    timer = setInterval(() => {
        timeLeft--;

        if (timeLeft < 0) {
            clearInterval(timer);
            alert('زمان کوییز به پایان رسید!');
            submitQuiz(true);
            return;
        }

        updateTimerDisplay(timeLeft, timerElement);
    }, 1000);
}

// تابع به‌روزرسانی نمایش تایمر
function updateTimerDisplay(timeLeft, timerElement) {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;

    // فرمت دو رقمی
    const formattedMinutes = String(minutes).padStart(2, '0');
    const formattedSeconds = String(seconds).padStart(2, '0');

    timerElement.textContent = `${formattedMinutes}:${formattedSeconds}`;

    // تغییر رنگ تایمر در زمان‌های بحرانی
    if (timeLeft <= 60) { // یک دقیقه آخر
        timerElement.classList.add('text-danger');
        timerElement.classList.add('fw-bold');

        if (timeLeft <= 10) { // ده ثانیه آخر
            if (timeLeft % 2 === 0) {
                timerElement.style.opacity = '1';
            } else {
                timerElement.style.opacity = '0.5';
            }
        }
    }
}