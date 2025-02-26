// متغیرهای سراسری برای مدیریت کوییز
let currentQuestion = 1;
let totalQuestions = 0;
let startTime = Date.now();
let timer;
let isQuizActive = false; // متغیر جدید برای تشخیص فعال بودن کوییز

// اجرای کد پس از لود کامل صفحه
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM fully loaded");
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        console.log("Quiz form found");
        totalQuestions = parseInt(quizForm.dataset.totalQuestions) || 0;
        console.log("Total questions:", totalQuestions);
        isQuizActive = true; // کوییز فعال است

        // افزودن Event Listener به لینک خروج
        setupExitConfirmation();
    } else {
        console.log("Quiz form not found!");
    }

    // نمایش اولین سوال
    showQuestion(1);

    // افزودن Event Listener به دکمه‌های بعدی و قبلی
    document.querySelectorAll('.nav-btn').forEach(button => {
        button.addEventListener('click', function () {
            const direction = this.getAttribute('data-direction');
            let newQuestion = direction === 'next' ? currentQuestion + 1 : currentQuestion - 1;
            if (newQuestion >= 1 && newQuestion <= totalQuestions) {
                showQuestion(newQuestion);
            }
        });
    });

    // افزودن Event Listener به دکمه پایان کوییز
    const finishQuizBtn = document.getElementById('finishQuiz');
    if (finishQuizBtn) {
        console.log("Finish quiz button found");
        finishQuizBtn.addEventListener('click', confirmSubmit);
    } else {
        console.log("Finish quiz button NOT found!");
    }

    // شروع تایمر برای کوییز (۱۰ دقیقه)
    startTimer(600);
});

// تابع جدید برای تنظیم تأیید خروج
function setupExitConfirmation() {
    const logoutLinks = document.querySelectorAll('a[href*="logout"]');

    logoutLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            if (isQuizActive) {
                event.preventDefault();
                if (confirm('آیا مطمئن هستید که می‌خواهید از کوییز خارج شوید؟ اطلاعات کوییز ذخیره نخواهد شد.')) {
                    // اگر کاربر تأیید کرد، به صفحه پروفایل هدایت شود
                    window.location.href = '/profile';
                }
                // اگر کاربر تأیید نکرد، در صفحه کوییز باقی می‌ماند
            } else {
                // اگر کوییز فعال نیست، به صورت عادی خارج شود
                window.location.href = this.href;
            }
        });
    });
}

// تابع نمایش سوال مشخص شده
function showQuestion(num) {
    // بررسی انتخاب گزینه در سوال فعلی قبل از رفتن به سوال بعد
    if (num > currentQuestion) {
        const currentCard = document.getElementById(`question-${currentQuestion}`);
        if (currentCard) {
            const selectedOption = currentCard.querySelector('input[type="radio"]:checked');
            if (!selectedOption) {
                alert('لطفاً یک گزینه را انتخاب کنید');
                return false;
            }
        }
    }

    // مخفی کردن همه سوالات
    document.querySelectorAll('.question-card').forEach(card => {
        card.style.display = 'none';
    });

    // نمایش سوال مورد نظر
    const nextCard = document.getElementById(`question-${num}`);
    if (nextCard) {
        nextCard.style.display = 'block';
        document.getElementById('currentQuestion').textContent = num;
        document.getElementById('progressBar').style.width = `${(num / totalQuestions) * 100}%`;
        currentQuestion = num;
    }
    return true;
}

// تابع تایید ارسال کوییز
function confirmSubmit() {
    console.log("Confirm submit called");
    // بررسی پاسخ به سوال آخر
    const lastCard = document.getElementById(`question-${totalQuestions}`);
    if (lastCard) {
        const lastAnswer = lastCard.querySelector('input[type="radio"]:checked');
        if (!lastAnswer) {
            alert('لطفاً به سوال آخر پاسخ دهید');
            return;
        }
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
                'Content-Type': 'application/json'
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
            showResult(result.score, answered, isTimeout);
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
function showResult(score, answered, isTimeout) {
    console.log("Showing result:", score);

    // ایجاد مودال نتیجه با روشی ایمن‌تر
    if (!document.getElementById('resultModal')) {
        console.log("Creating result modal");
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
                        <h3>نمره شما: <span id="scorePercentage"></span>%</h3>
                        <p>پاسخ‌های صحیح: <span id="correctAnswers"></span> از ${totalQuestions}</p>
                        <div id="resultMessage" class="mt-3"></div>
                    </div>
                    <div class="modal-footer">
                        <a href="/profile" class="btn btn-primary">مشاهده پروفایل</a>
                    </div>
                </div>
            </div>
        </div>
        `;

        // افزودن مودال به DOM
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHTML;
        document.body.appendChild(modalContainer.firstChild);

        // کمی صبر کنید تا DOM به‌روزرسانی شود
        setTimeout(() => {
            updateModalContent(score, answered, isTimeout);
        }, 100);
    } else {
        // مودال قبلاً ایجاد شده، فقط محتوا را به‌روز کنید
        updateModalContent(score, answered, isTimeout);
    }
}

// تابع جدید برای به‌روزرسانی محتوای مودال
function updateModalContent(score, answered, isTimeout) {
    console.log("Updating modal content");

    // بررسی وجود عناصر قبل از دسترسی به آنها
    const resultIcon = document.getElementById('resultIcon');
    const resultMessage = document.getElementById('resultMessage');
    const scorePercentage = document.getElementById('scorePercentage');
    const correctAnswersElement = document.getElementById('correctAnswers');

    if (!resultIcon || !resultMessage || !scorePercentage || !correctAnswersElement) {
        console.error("Required modal elements not found!");
        console.log("resultIcon exists:", !!resultIcon);
        console.log("resultMessage exists:", !!resultMessage);
        console.log("scorePercentage exists:", !!scorePercentage);
        console.log("correctAnswers exists:", !!correctAnswersElement);

        // نمایش نتیجه به صورت alert در صورت بروز خطا
        alert(`نمره شما: ${score}%`);
        setTimeout(() => {
            window.location.href = '/profile';
        }, 2000);
        return;
    }

    const correctAnswers = Math.floor((score / 100) * totalQuestions);

    // تعیین وضعیت نتیجه با بررسی وجود عناصر
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
        if (isTimeout && resultMessage) {
            resultMessage.textContent = 'زمان کوییز به پایان رسید. ' + resultMessage.textContent;
        }
    }

    // به‌روزرسانی اطلاعات در مودال
    if (scorePercentage) scorePercentage.textContent = score;
    if (correctAnswersElement) correctAnswersElement.textContent = correctAnswers;

    // نمایش مودال نتیجه
    try {
        if (typeof bootstrap !== 'undefined') {
            const resultModal = document.getElementById('resultModal');
            if (resultModal) {
                const bsModal = new bootstrap.Modal(resultModal);
                bsModal.show();

                // هدایت خودکار به صفحه پروفایل بعد از 4 ثانیه
                setTimeout(() => {
                    window.location.href = '/profile';
                }, 4000);
            } else {
                console.error("Modal element not found");
                alert(`نمره شما: ${score}%`);
                // هدایت فوری به صفحه پروفایل در صورت عدم وجود مودال
                setTimeout(() => {
                    window.location.href = '/profile';
                }, 2000);
            }
        } else {
            console.error("Bootstrap not loaded");
            alert(`نمره شما: ${score}%`);
            // هدایت فوری به صفحه پروفایل در صورت عدم وجود بوت‌استرپ
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
    timer = setInterval(() => {
        let minutes = parseInt(timeLeft / 60, 10);
        let seconds = parseInt(timeLeft % 60, 10);
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;
        const timerElement = document.getElementById('timer');
        if (timerElement) {
            timerElement.textContent = minutes + ":" + seconds;
        }
        if (--timeLeft < 0) {
            clearInterval(timer);
            submitQuiz(true);
        }
    }, 1000);
}