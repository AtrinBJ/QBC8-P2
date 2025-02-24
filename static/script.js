// متغیرهای سراسری برای مدیریت کوییز
let currentQuestion = 1;
let totalQuestions = 0;
let startTime = Date.now();
let timer;

// اجرای کد پس از لود کامل صفحه
document.addEventListener('DOMContentLoaded', function() {
    // دریافت تعداد کل سوالات از فرم
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        totalQuestions = parseInt(quizForm.getAttribute('data-total-questions')) || 0;
    }

    // شروع تایمر برای کوییز
    startTimer(600); // 10 دقیقه
});

// تابع نمایش سوال مشخص شده
function showQuestion(num) {
    // بررسی انتخاب گزینه در سوال فعلی قبل از رفتن به سوال بعد
    if (num > currentQuestion) {
        const currentCard = document.getElementById(`question-${currentQuestion}`);
        const selectedOption = currentCard.querySelector('input[type="radio"]:checked');

        if (!selectedOption) {
            alert('لطفاً یک گزینه را انتخاب کنید');
            return false;
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
    // بررسی پاسخ به سوال آخر
    const lastCard = document.getElementById(`question-${totalQuestions}`);
    const lastAnswer = lastCard.querySelector('input[type="radio"]:checked');

    if (!lastAnswer) {
        alert('لطفاً به سوال آخر پاسخ دهید');
        return;
    }

    if (confirm('آیا مطمئن هستید که می‌خواهید کوییز را به پایان برسانید؟')) {
        submitQuiz(false);
    }
}

// تابع ارسال نتایج کوییز
async function submitQuiz(isTimeout = false) {
    clearInterval(timer);

    const form = document.getElementById('quizForm');
    const formData = new FormData(form);
    const answers = {};
    let answered = 0;

    // جمع‌آوری پاسخ‌ها
    for (let [key, value] of formData.entries()) {
        const questionId = key.split('-')[1];
        answers[questionId] = value;
        answered++;
    }

    // بررسی تکمیل همه سوالات
    if (!isTimeout && answered < totalQuestions) {
        alert(`لطفاً به تمام سوالات پاسخ دهید. ${totalQuestions - answered} سوال بدون پاسخ مانده است.`);
        return;
    }

    try {
        const response = await fetch('/submit_quiz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                category: form.dataset.category,
                answers: answers,
                time_taken: Math.floor((Date.now() - startTime) / 1000)
            })
        });

        const result = await response.json();
        if (result.success) {
            showResult(result.score, answered, isTimeout);
        } else {
            alert('خطا در ثبت نتایج: ' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('خطا در ارتباط با سرور');
    }
}

// تابع نمایش نتیجه کوییز
function showResult(score, answered, isTimeout) {
    const resultIcon = document.getElementById('resultIcon');
    const resultMessage = document.getElementById('resultMessage');

    // تعیین وضعیت نتیجه
    if (score >= 80) {
        resultIcon.className = 'bi bi-emoji-smile display-1 text-success';
        resultMessage.className = 'alert alert-success';
        resultMessage.textContent = 'عالی! عملکرد شما فوق‌العاده بود.';
    } else if (score >= 60) {
        resultIcon.className = 'bi bi-emoji-neutral display-1 text-warning';
        resultMessage.className = 'alert alert-warning';
        resultMessage.textContent = 'خوب! اما جای پیشرفت دارید.';
    } else {
        resultIcon.className = 'bi bi-emoji-frown display-1 text-danger';
        resultMessage.className = 'alert alert-danger';
        resultMessage.textContent = 'نیاز به تمرین بیشتر دارید.';
    }

    // نمایش اطلاعات در مودال
    document.getElementById('scorePercentage').textContent = score;
    document.getElementById('correctAnswers').textContent = answered;

    if (isTimeout) {
        resultMessage.textContent = 'زمان کوییز به پایان رسید. ' + resultMessage.textContent;
    }

    // نمایش مودال نتیجه
    new bootstrap.Modal(document.getElementById('resultModal')).show();
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