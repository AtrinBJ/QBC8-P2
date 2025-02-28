@echo off
echo === شروع فرآیند بازسازی محیط مجازی ===

:: غیرفعال کردن محیط مجازی فعلی
echo [1/6] غیرفعال کردن محیط مجازی فعلی...
call A:\PythonProject2\.venv1\Scripts\deactivate.bat

:: حذف پوشه محیط مجازی موجود
echo [2/6] حذف محیط مجازی قبلی...
rmdir /s /q A:\PythonProject2\.venv1

:: ایجاد محیط مجازی جدید
echo [3/6] ایجاد محیط مجازی جدید...
python -m venv A:\PythonProject2\.venv1

:: فعال‌سازی محیط مجازی جدید
echo [4/6] فعال‌سازی محیط مجازی جدید...
call A:\PythonProject2\.venv1\Scripts\activate.bat

:: آپدیت pip
echo [5/6] به‌روزرسانی pip...
python -m pip install --upgrade pip

:: نصب کتابخانه‌ها از requirements.txt
echo [6/6] نصب کتابخانه‌ها از requirements.txt...
pip install -r A:\PythonProject2\requirements.txt

echo === فرآیند بازسازی محیط مجازی با موفقیت انجام شد ===
echo کتابخانه‌های نصب شده:
pip list

echo.
echo برای اجرای برنامه‌تان، دستور زیر را اجرا کنید:
echo python A:\PythonProject2\app.py