#!/bin/bash

echo "🚀 شروع نصب ربات اکسل تلگرام..."

# ایجاد پوشه‌های مورد نیاز
mkdir -p data/excel_files
mkdir -p data/backups
mkdir -p logs

echo "📁 پوشه‌ها ایجاد شدند"

# نصب Python dependencies
echo "📦 نصب وابستگی‌ها..."
pip3 install -r requirements.txt

echo "✅ وابستگی‌ها نصب شدند"

# اجازه اجرا به فایل اصلی
chmod +x main.py

echo "🔐 مجوزها تنظیم شدند"

# تست اتصال ربات
echo "🔍 تست اتصال ربات..."
python3 -c "
import requests
token = '8010319526:AAFtrg4ifAiczDM5V2-enUmQvWkguX2s0AE'
url = f'https://api.telegram.org/bot{token}/getMe'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    if data['ok']:
        print('✅ ربات متصل است!')
        print(f'نام ربات: {data[\"result\"][\"first_name\"]}')
        print(f'نام کاربری: @{data[\"result\"][\"username\"]}')
    else:
        print('❌ خطا در اتصال ربات')
else:
    print('❌ خطا در درخواست')
"

echo ""
echo "🎉 نصب کامل شد!"
echo "برای اجرای ربات دستور زیر را اجرا کنید:"
echo "python3 main.py"
echo ""
echo "یا برای اجرای دائمی:"
echo "nohup python3 main.py > logs/bot.log 2>&1 &"

