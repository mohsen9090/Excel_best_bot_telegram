#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
فایل تنظیمات ربات Excel با تفکیک کامل Chat ID
نسخه بهبود یافته با قابلیت‌های پیشرفته
"""

# توکن ربات تلگرام
TOKEN = "8010319526:AAFtrg4ifAiczDM5V2-enUmQvWkguX2s0AE"

# مسیرهای فایل‌ها - با تفکیک chat_id
EXCEL_DIR = "excel_files"  # پوشه فایل‌های اکسل
FIELDS_DIR = "fields_data"  # پوشه فیلدها
USER_THEMES_DIR = "user_themes"  # پوشه تم‌های کاربران
BACKUP_DIR = "backups"  # پوشه بکاپ‌ها

# نام فایل‌های مختص هر chat_id
def get_excel_file(chat_id):
    """دریافت مسیر فایل اکسل مخصوص chat_id"""
    return f"{EXCEL_DIR}/data_{chat_id}.xlsx"

def get_fields_file(chat_id):
    """دریافت مسیر فایل فیلدهای مخصوص chat_id"""
    return f"{FIELDS_DIR}/fields_{chat_id}.json"

def get_user_theme_file(chat_id):
    """دریافت مسیر فایل تم مخصوص chat_id"""
    return f"{USER_THEMES_DIR}/theme_{chat_id}.json"

def get_backup_file(chat_id, timestamp):
    """دریافت مسیر فایل بکاپ مخصوص chat_id"""
    return f"{BACKUP_DIR}/backup_{chat_id}_{timestamp}.xlsx"

# فیلدهای پیش فرض برای هر کاربر جدید
DEFAULT_FIELDS = [
    "نام",
    "نام خانوادگی", 
    "سن",
    "شغل",
    "کد ملی",
    "شماره تلفن",
    "ایمیل",
    "کد پستی",
    "آدرس منزل",
    "شماره کارت بانکی",
    "تاریخ تولد",
    "وضعیت تاهل"
]

# States برای ConversationHandler
ADD_DATA = 0
EDIT_ROW = 1
EDIT_FIELD = 2
EDIT_VALUE = 3
DELETE_ROW = 4
SEARCH_FIELD = 5
SEARCH_VALUE = 6
FIELD_MANAGEMENT = 7
ADD_FIELD = 8
DELETE_FIELD = 9
CONFIRM_DELETE_ALL = 10
UPLOAD_FILE = 11
CHANGE_THEME = 12
MANAGE_FIELDS = 13
SEARCH_QUERY = 14
DELETE_FIELD_SELECT = 15

# تنظیمات لاگینگ
LOG_FILE = "bot.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# تنظیمات نمایش
MAX_DISPLAY_RECORDS = 10  # حداکثر تعداد رکورد برای نمایش
MAX_SEARCH_RESULTS = 8    # حداکثر تعداد نتایج جستجو
MAX_FILE_SIZE = 20 * 1024 * 1024  # حداکثر حجم فایل آپلود (20MB)

# تنظیمات ایمنی
ALLOWED_FILE_TYPES = ['.xlsx', '.xls']  # فرمت‌های مجاز فایل
AUTO_BACKUP = True  # بکاپ خودکار
MAX_BACKUPS_PER_USER = 10  # حداکثر تعداد بکاپ برای هر کاربر

# پیام‌های سیستم
WELCOME_MESSAGE = """🎉 سلام {name} عزیز!

به ربات مدیریت Excel پیشرفته خوش آمدید! 

🔥 امکانات ویژه شما:
• 📤 آپلود فایل Excel شخصی
• ➕ اضافه کردن رکورد جدید
• ✏️ ویرایش و حذف اطلاعات  
• 🔍 جستجوی پیشرفته
• 🎨 تم‌های رنگی متنوع
• 📊 آمارگیری کامل
• 💾 بکاپ خودکار

🔒 تمام داده‌های شما کاملاً مجزا و ایمن!
💡 Chat ID شما: {chat_id}

از منوی زیر استفاده کنید:"""

ERROR_MESSAGES = {
    'file_not_found': '❌ فایل یافت نشد!',
    'invalid_format': '❌ فرمت فایل نامعتبر است!',
    'file_too_large': '❌ حجم فایل بیش از حد مجاز است!',
    'permission_denied': '❌ دسترسی مجاز نیست!',
    'unknown_error': '❌ خطای نامشخص رخ داد!'
}

SUCCESS_MESSAGES = {
    'record_added': '✅ رکورد با موفقیت اضافه شد! 🎉',
    'record_updated': '✅ رکورد با موفقیت ویرایش شد! ✏️',
    'record_deleted': '✅ رکورد با موفقیت حذف شد! 🗑️',
    'file_uploaded': '✅ فایل با موفقیت آپلود شد! 📤',
    'theme_changed': '✅ تم با موفقیت تغییر یافت! 🎨'
}

# تنظیمات پیشرفته
ENABLE_ANALYTICS = True  # فعال‌سازی آمارگیری
ENABLE_AUTO_SAVE = True  # ذخیره خودکار
ENABLE_FIELD_VALIDATION = True  # اعتبارسنجی فیلدها
ENABLE_SEARCH_HIGHLIGHT = True  # هایلایت نتایج جستجو

# محدودیت‌های کاربر
MAX_RECORDS_PER_USER = 10000  # حداکثر تعداد رکورد برای هر کاربر
MAX_FIELDS_PER_USER = 50      # حداکثر تعداد فیلد برای هر کاربر
MAX_FIELD_LENGTH = 100        # حداکثر طول هر فیلد

# اطلاعات ربات
BOT_INFO = {
    'name': 'ربات مدیریت Excel پیشرفته',
    'version': '2.1',
    'developer': '@mohsen9090',
    'description': 'مدیریت فایل‌های Excel با تفکیک کامل کاربران'
}
