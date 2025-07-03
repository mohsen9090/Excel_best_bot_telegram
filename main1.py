#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
import os
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

from config import *
from utils import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_keyboard():
    keyboard = [
        [KeyboardButton("➕  اضافه کردن"), KeyboardButton("📋  نمایش همه"), KeyboardButton("📁  دریافت فایل")],
        [KeyboardButton("✏️ ویرایش"), KeyboardButton("🗑️ حذف"), KeyboardButton("🔍  جستجو")],
        [KeyboardButton("📤  آپلود فایل Excel"), KeyboardButton("⚙️ مدیریت فیلدها")],
        [KeyboardButton("🎨  تغییر تم"), KeyboardButton("📊  آمار"), KeyboardButton("🧹  حذف همه")],
        [KeyboardButton("💾  بکاپ"), KeyboardButton("ℹ️ راهنما")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_name = update.effective_user.first_name or "کاربر"
    
    try:
        initialize_user_data(chat_id)
        
        welcome = WELCOME_MESSAGE.format(name=user_name, chat_id=chat_id)
        await update.message.reply_text(welcome, reply_markup=get_keyboard())
        
        logger.info(f"کاربر {chat_id} ربات را شروع کرد")
        
    except Exception as e:
        logger.error(f"خطا در start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌  خطا در راه‌اندازی. لطفاً دوباره تلاش کنید.")

async def add_record_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if os.path.exists(excel_file):
            df = pd.read_excel(excel_file)
            if len(df) >= MAX_RECORDS_PER_USER:
                await update.message.reply_text(
                    f"❌  حداکثر تعداد رکورد ({MAX_RECORDS_PER_USER:,}) برای Chat ID {chat_id} رسیده است.",
                    reply_markup=get_keyboard()
                )
                return ConversationHandler.END
        
        fields = load_fields(chat_id)
        context.user_data['record_data'] = {}
        context.user_data['current_field'] = 0
        context.user_data['chat_id'] = chat_id
        
        first_field = fields[0]
        await update.message.reply_text(
            f"📝  **Chat ID {chat_id}**\n**{first_field}** را وارد کنید: (1/{len(fields)})"
        )
        return ADD_DATA
        
    except Exception as e:
        logger.error(f"خطا در add_record_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در شروع اضافه کردن رکورد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def add_record_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    fields = load_fields(chat_id)
    
    field = fields[context.user_data['current_field']]
    user_input = update.message.text.strip()
    
    is_valid, result = validate_field_input(field, user_input)
    if not is_valid:
        await update.message.reply_text(f"❌  Chat ID {chat_id}: {result}")
        return ADD_DATA
    
    context.user_data['record_data'][field] = result
    context.user_data['current_field'] += 1
    
    if context.user_data['current_field'] < len(fields):
        next_field = fields[context.user_data['current_field']]
        progress = f"({context.user_data['current_field'] + 1}/{len(fields)})"
        await update.message.reply_text(
            f"📝  **Chat ID {chat_id}**\n**{next_field}** را وارد کنید: {progress}"
        )
        return ADD_DATA
    else:
        try:
            excel_file = get_excel_file(chat_id)
            new_row = pd.DataFrame([context.user_data['record_data']])
            
            if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
                df = pd.read_excel(excel_file)
                
                if len(df) >= MAX_RECORDS_PER_USER:
                    await update.message.reply_text(
                        f"❌  Chat ID {chat_id} نمی‌تواند بیش از {MAX_RECORDS_PER_USER:,} رکورد داشته باشد.",
                        reply_markup=get_keyboard()
                    )
                    return ConversationHandler.END
                
                df = pd.concat([df, new_row], ignore_index=True)
            else:
                df = new_row
            
            user_theme = load_user_theme(chat_id)
            if create_excel(df, user_theme, chat_id):
                total_records = len(df)
                await update.message.reply_text(
                    f"✅  رکورد جدید برای Chat ID {chat_id} با موفقیت اضافه شد! 🎉 \n"
                    f"📊  تعداد کل رکوردها: {total_records:,}", 
                    reply_markup=get_keyboard()
                )
                logger.info(f"کاربر {chat_id} یک رکورد جدید اضافه کرد")
            else:
                raise Exception("خطا در ایجاد فایل Excel")
                
        except Exception as e:
            logger.error(f"خطا در ذخیره رکورد chat_id {chat_id}: {e}")
            await update.message.reply_text(
                f"❌  خطا در ذخیره رکورد Chat ID {chat_id}. لطفاً دوباره تلاش کنید.", 
                reply_markup=get_keyboard()
            )
        
        return ConversationHandler.END

async def show_all_records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(f"📭  هیچ رکوردی در فایل Chat ID {chat_id} وجود ندارد.")
            return
        
        df = pd.read_excel(excel_file)
        message = format_record_display(df, MAX_DISPLAY_RECORDS, chat_id)
        await update.message.reply_text(message)
            
    except Exception as e:
        logger.error(f"خطا در نمایش رکوردهای chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌  خطا در نمایش رکوردهای Chat ID {chat_id}.")

async def send_excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            user_theme = load_user_theme(chat_id)
            create_excel(df, user_theme, chat_id)
            
            with open(excel_file, "rb") as file:
                filename = f"excel_data_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                caption = f"""📁  **فایل Excel شخصی شما**
🆔  Chat ID: {chat_id}
📊  تعداد رکوردها: {len(df):,}
🎨  تم: {THEMES[user_theme]['name']}
🕐  تاریخ: {datetime.now().strftime('%Y/%m/%d %H:%M')}

🔒  این فایل مخصوص شماست!"""
                
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=caption
                )
                
            logger.info(f"فایل Excel برای chat_id {chat_id} ارسال شد")
        else:
            await update.message.reply_text(f"📭  فایل Excel برای Chat ID {chat_id} یافت نشد.")
            
    except Exception as e:
        logger.error(f"خطا در ارسال فایل chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌  خطا در ارسال فایل Excel Chat ID {chat_id}.")

async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        stats = get_user_statistics(chat_id)
        
        if not stats:
            await update.message.reply_text(f"❌  خطا در دریافت آمار Chat ID {chat_id}.")
            return
        
        msg = f"""📊  **آمار Chat ID {chat_id}**

📋  **آمار فایل:**
- تعداد رکوردها: {stats['total_records']:,}
- تعداد فیلدها: {stats['total_fields']}
- حجم فایل: {stats['file_size']} کیلوبایت
- آخرین بروزرسانی: {stats['last_updated']}

🎨  **تنظیمات:**
- تم فعال: {stats['theme']}
- تعداد بکاپ‌ها: {stats['backup_count']}

💾  **ظرفیت:**
- حداکثر رکورد مجاز: {MAX_RECORDS_PER_USER:,}
- باقیمانده: {MAX_RECORDS_PER_USER - stats['total_records']:,}

🔒  **تمام این اطلاعات مخصوص شماست!**"""

        await update.message.reply_text(msg)
        
    except Exception as e:
        logger.error(f"خطا در show_statistics برای chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌  خطا در نمایش آمار Chat ID {chat_id}.")

async def create_backup_manual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        if create_backup(chat_id):
            timestamp = datetime.now().strftime('%Y/%m/%d %H:%M')
            await update.message.reply_text(
                f"✅  **بکاپ Chat ID {chat_id} ایجاد شد!**\n\n"
                f"🕐  زمان: {timestamp}\n"
                f"💾  فایل شما در صورت نیاز قابل بازیابی است.\n\n"
                f"🔒  بکاپ مخصوص شماست!"
            )
            logger.info(f"بکاپ دستی برای chat_id {chat_id} ایجاد شد")
        else:
            await update.message.reply_text(f"❌  خطا در ایجاد بکاپ Chat ID {chat_id}.")
    except Exception as e:
        logger.error(f"خطا در create_backup_manual برای chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌  خطا در ایجاد بکاپ Chat ID {chat_id}.")

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    help_text = f"""ℹ️ **راهنمای کامل ربات**
🆔  Chat ID شما: {chat_id}

🔧  **عملیات اصلی:**
- ➕  اضافه کردن: افزودن رکورد جدید
- 📋  نمایش همه: مشاهده تمام رکوردها
- 📁  دریافت فایل: دانلود فایل Excel شخصی

✏️ **ویرایش و مدیریت:**
- ✏️ ویرایش: تغییر اطلاعات رکورد
- 🗑️ حذف: حذف رکورد منتخب
- 🔍  جستجو: یافتن رکوردهای مشخص

📤  **آپلود فایل:**
- آپلود فایل Excel دلخواه شما
- دو حالت: جایگزینی یا ادغام
- حداکثر {MAX_FILE_SIZE//(1024*1024)} مگابایت

⚙️ **تنظیمات پیشرفته:**
- ⚙️ مدیریت فیلدها: اضافه/حذف ستون‌ها
- 🎨  تغییر تم: انتخاب رنگ‌بندی Excel
- 📊  آمار: مشاهده اطلاعات آماری
- 🧹  حذف همه: پاک کردن تمام داده‌ها
- 💾  بکاپ: ایجاد نسخه پشتیبان

🔒  **امنیت:**
- هر کاربر فایل کاملاً مجزا دارد
- داده‌های شما محرمانه و ایمن است
- حداکثر {MAX_RECORDS_PER_USER:,} رکورد برای هر کاربر

💡  از دکمه‌های زیر استفاده کنید."""

    await update.message.reply_text(help_text)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    await update.message.reply_text(
        f"❌  **عملیات Chat ID {chat_id} لغو شد.**\n🏠  بازگشت به منوی اصلی",
        reply_markup=get_keyboard()
    )
    
    context.user_data.clear()
    
    return ConversationHandler.END
