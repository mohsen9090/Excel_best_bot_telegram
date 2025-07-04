#!/usr/bin/env python3
# -*- coding: utf-8 -*-

TOKEN = "توکن عددی خود را واردکنید"

# مسیرهای فایل‌ها
EXCEL_DIR = "excel_files"
FIELDS_DIR = "fields_data"
USER_THEMES_DIR = "user_themes"
BACKUP_DIR = "backups"

def get_excel_file(chat_id):
    return f"{EXCEL_DIR}/data_{chat_id}.xlsx"

def get_fields_file(chat_id):
    return f"{FIELDS_DIR}/fields_{chat_id}.json"

def get_user_theme_file(chat_id):
    return f"{USER_THEMES_DIR}/theme_{chat_id}.json"

def get_backup_file(chat_id, timestamp):
    return f"{BACKUP_DIR}/backup_{chat_id}_{timestamp}.xlsx"

# فیلدهای پیش‌فرض
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

# تم‌های رنگی
THEMES = {
    "blue": {
        "name": "💙  آبی کلاسیک",
        "header": "1F4E79",
        "row1": "D9E2F3", 
        "row2": "F2F2F2",
        "border": "4472C4"
    },
    "green": {
        "name": "💚  سبز طبیعی",
        "header": "0D5016",
        "row1": "E2F0D9",
        "row2": "F2F2F2", 
        "border": "70AD47"
    },
    "purple": {
        "name": "💜  بنفش شاهانه",
        "header": "5B2C87",
        "row1": "E6D7F0",
        "row2": "F2F2F2",
        "border": "7030A0"
    },
    "red": {
        "name": "❤️ قرمز پرقدرت", 
        "header": "C5504B",
        "row1": "F2D7D5",
        "row2": "F2F2F2",
        "border": "E74C3C"
    },
    "orange": {
        "name": "🧡  نارنجی انرژی",
        "header": "D68910", 
        "row1": "FCF3CF",
        "row2": "F2F2F2",
        "border": "F39C12"
    },
    "dark": {
        "name": "🖤  تیره مدرن",
        "header": "2C3E50",
        "row1": "D5DBDB",
        "row2": "F8F9FA", 
        "border": "34495E"
    },
    "pink": {
        "name": "💗  صورتی شیک",
        "header": "AD1457",
        "row1": "FCE4EC",
        "row2": "F2F2F2",
        "border": "E91E63"
    },
    "teal": {
        "name": "💎  فیروزه‌ای",
        "header": "00695C",
        "row1": "E0F2F1", 
        "row2": "F2F2F2",
        "border": "26A69A"
    }
}

# حالات مکالمه
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

# تنظیمات عمومی
LOG_FILE = "bot.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
MAX_DISPLAY_RECORDS = 10
MAX_SEARCH_RESULTS = 8
MAX_FILE_SIZE = 20 * 1024 * 1024
ALLOWED_FILE_TYPES = ['.xlsx', '.xls']
AUTO_BACKUP = True
MAX_BACKUPS_PER_USER = 10

# محدودیت‌ها
ENABLE_ANALYTICS = True
ENABLE_AUTO_SAVE = True
ENABLE_FIELD_VALIDATION = True
ENABLE_SEARCH_HIGHLIGHT = True
MAX_RECORDS_PER_USER = 10000
MAX_FIELDS_PER_USER = 50
MAX_FIELD_LENGTH = 100

# پیام خوشامدگویی
WELCOME_MESSAGE = """🎉  سلام {name} عزیز!
به ربات مدیریت Excel پیشرفته خوش آمدید! 

🔥  امکانات ویژه شما:
- 📤  آپلود فایل Excel شخصی
- ➕  اضافه کردن رکورد جدید
- ✏️ ویرایش و حذف اطلاعات
- 🔍  جستجوی پیشرفته
- 🎨  تم‌های رنگی متنوع
- 📊  آمارگیری کامل
- 💾  بکاپ خودکار

🔒  تمام داده‌های شما کاملاً مجزا و ایمن!
💡  Chat ID شما: {chat_id}

از منوی زیر استفاده کنید:"""

# اطلاعات ربات
BOT_INFO = {
    'name': 'ربات مدیریت Excel پیشرفته',
    'version': '3.0',
    'developer': '@mohsen9090',
    'description': 'مدیریت فایل‌های Excel با تفکیک کامل کاربران'
}
