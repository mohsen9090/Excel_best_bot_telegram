#!/bin/bash

echo "🚀 راه‌اندازی ربات Excel مدیریت کامل..."

# نصب پکیج‌ها
echo "📦 نصب پکیج‌های مورد نیاز..."
pip3 install -r requirements.txt

# ایجاد پوشه‌های مورد نیاز
echo "📁 ایجاد پوشه‌ها..."
mkdir -p excel_files fields_data user_themes backups logs

# تنظیم مجوزها
echo "🔐 تنظیم مجوزها..."
chmod +x main.py
chmod +x run_bot.sh

# اجرای ربات
echo "🤖 شروع ربات..."
python3 main.py
