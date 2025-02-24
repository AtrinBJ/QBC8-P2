# QBC8-P2
(P2) Quiz System

((
python project2/
│
├── app.py                         # فایل اصلی برنامه با تمام مسیرها و مدل‌ها
├── config.py                      # تنظیمات برنامه مثل تنظیمات دیتابیس و امنیتی
├── requirements.txt               # لیست کتابخانه‌های مورد نیاز
│
├── static/                        # فایل‌های استاتیک
│   ├── css/
│   │   ├── style.css              # استایل‌های اصلی
│   │   └── theme.css              # تم‌های مختلف (روشن/تاریک)
│   │
│   ├── js/
│   │   ├── script.js              # اسکریپت‌های عمومی
│   │   ├── quiz.js                # اسکریپت‌های مربوط به کوییز
│   │   └── admin.js               # اسکریپت‌های بخش مدیریت
│   │
│   └── images/
│       ├── background.jpg         # تصویر پس‌زمینه
│       └── icons/                 # آیکون‌ها
│
├── templates/                     # قالب‌های HTML
│   ├── base.html                  # قالب پایه که بقیه قالب‌ها از آن ارث می‌برند
│   ├── index.html                 # صفحه اصلی
│   ├── login.html                 # صفحه ورود
│   ├── register.html              # صفحه ثبت‌نام
│   ├── profile.html               # صفحه پروفایل کاربر
│   ├── quiz.html                  # صفحه انجام کوییز
│   ├── tickets.html               # صفحه تیکت‌ها
│   ├── ticket_detail.html         # صفحه جزئیات تیکت
│   │
│   └── admin/                     # قالب‌های بخش مدیریت
│       ├── dashboard.html         # داشبورد مدیریت
│       ├── manage_questions.html  # مدیریت سوالات
│       ├── manage_access.html     # مدیریت دسترسی‌ها
│       └── analytics.html         # صفحه آمار و تحلیل
│
├── models/                        # در صورت نیاز به جداسازی مدل‌ها
│   ├── __init__.py
│   ├── user.py                    # مدل کاربر
│   ├── quiz.py                    # مدل‌های مربوط به کوییز
│   └── ticket.py                  # مدل‌های تیکت
│
└── instance/                      # فایل‌های مربوط به نمونه برنامه
    └── quiz.db                    # فایل دیتابیس SQLite
))

        
