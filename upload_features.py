#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from config import *
from utils import *

logger = logging.getLogger(__name__)

# ویژگی آپلود فایل
async def upload_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    msg = f"📤  **آپلود فایل Excel Chat ID {chat_id}**\n\n"
    msg += f"📋  **دو حالت آپلود:**\n"
    msg += f"1️⃣  جایگزینی: حذف داده‌های فعلی و جایگزینی با فایل جدید\n"
    msg += f"2️⃣  ادغام: اضافه کردن داده‌های جدید به داده‌های موجود\n\n"
    msg += f"📏  **محدودیت‌ها:**\n"
    msg += f"- حداکثر حجم: {MAX_FILE_SIZE//(1024*1024)} مگابایت\n"
    msg += f"- فرمت‌های مجاز: .xlsx, .xls\n"
    msg += f"- حداکثر رکورد: {MAX_RECORDS_PER_USER:,}\n\n"
    msg += f"🔧  **مرحله اول:** نحوه آپلود را انتخاب کنید:"
    
    keyboard = [
        [KeyboardButton("🔄 جایگزینی داده‌ها"), KeyboardButton("➕ ادغام داده‌ها")],
        [KeyboardButton("❌ لغو")]
    ]
    
    await update.message.reply_text(
        msg,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return UPLOAD_FILE

async def upload_file_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mode = update.message.text
    
    if mode == "❌ لغو":
        await update.message.reply_text(
            f"❌  آپلود فایل Chat ID {chat_id} لغو شد.",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    elif mode in ["🔄 جایگزینی داده‌ها", "➕ ادغام داده‌ها"]:
        context.user_data['upload_mode'] = 'replace' if mode.startswith('🔄') else 'merge'
        context.user_data['chat_id'] = chat_id
        
        await update.message.reply_text(
            f"📁  **Chat ID {chat_id}**\n"
            f"حالت انتخابی: {mode}\n\n"
            f"📤  لطفاً فایل Excel خود را ارسال کنید:"
        )
        return UPLOAD_FILE
    
    else:
        await update.message.reply_text(
            f"❌  لطفاً یکی از گزینه‌های ارائه شده را برای Chat ID {chat_id} انتخاب کنید."
        )
        return UPLOAD_FILE

async def handle_uploaded_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        document = update.message.document
        
        if not document:
            await update.message.reply_text(f"❌  فایلی دریافت نشد برای Chat ID {chat_id}.")
            return UPLOAD_FILE
        
        # بررسی نوع فایل
        file_name = document.file_name.lower()
        if not any(file_name.endswith(ext) for ext in ALLOWED_FILE_TYPES):
            await update.message.reply_text(
                f"❌  فرمت فایل Chat ID {chat_id} پشتیبانی نمی‌شود.\n"
                f"فرمت‌های مجاز: {', '.join(ALLOWED_FILE_TYPES)}"
            )
            return UPLOAD_FILE
        
        # بررسی حجم فایل
        if document.file_size > MAX_FILE_SIZE:
            await update.message.reply_text(
                f"❌  حجم فایل Chat ID {chat_id} بیش از حد مجاز است.\n"
                f"حداکثر مجاز: {MAX_FILE_SIZE//(1024*1024)} مگابایت"
            )
            return UPLOAD_FILE
        
        # دانلود فایل
        file = await document.get_file()
        temp_file_path = f"temp_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        await file.download_to_drive(temp_file_path)
        
        # اعتبارسنجی فایل
        is_valid, validation_message = validate_excel_file(temp_file_path)
        if not is_valid:
            os.remove(temp_file_path)
            await update.message.reply_text(f"❌  Chat ID {chat_id}: {validation_message}")
            return UPLOAD_FILE
        
        # خواندن داده‌های فایل آپلود شده
        uploaded_df = pd.read_excel(temp_file_path)
        
        # تنظیم نوع داده‌ها برای جلوگیری از .0 در اعداد طولانی
        for col in uploaded_df.columns:
            uploaded_df[col] = uploaded_df[col].apply(lambda x: format_numeric_field(x, col))
        
        upload_mode = context.user_data.get('upload_mode', 'replace')
        
        if upload_mode == 'replace':
            # جایگزینی کامل
            result_df = uploaded_df.copy()
            
            # ذخیره فیلدهای جدید
            new_fields = list(uploaded_df.columns)
            save_fields(new_fields, chat_id)
            
        else:
            # ادغام با داده‌های موجود
            excel_file = get_excel_file(chat_id)
            if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
                existing_df = pd.read_excel(excel_file)
                result_df = merge_dataframes(existing_df, uploaded_df)
            else:
                result_df = uploaded_df.copy()
            
            # بروزرسانی فیلدها
            all_fields = list(result_df.columns)
            save_fields(all_fields, chat_id)
        
        # بررسی محدودیت تعداد رکورد
        if len(result_df) > MAX_RECORDS_PER_USER:
            os.remove(temp_file_path)
            await update.message.reply_text(
                f"❌  تعداد کل رکوردها ({len(result_df):,}) بیش از حد مجاز ({MAX_RECORDS_PER_USER:,}) برای Chat ID {chat_id} است."
            )
            return UPLOAD_FILE
        
        # ایجاد فایل Excel جدید
        user_theme = load_user_theme(chat_id)
        if create_excel(result_df, user_theme, chat_id):
            mode_text = "جایگزین" if upload_mode == 'replace' else "ادغام"
            await update.message.reply_text(
                f"✅  **آپلود موفق Chat ID {chat_id}!**\n\n"
                f"📊  تعداد رکوردها: {len(result_df):,}\n"
                f"📋  تعداد فیلدها: {len(result_df.columns)}\n"
                f"🔄  حالت: {mode_text}\n\n"
                f"🎉  فایل شما آماده است!",
                reply_markup=get_keyboard()
            )
            logger.info(f"فایل برای chat_id {chat_id} با حالت {upload_mode} آپلود شد")
        else:
            raise Exception("خطا در ایجاد فایل Excel")
        
        # حذف فایل موقت
        os.remove(temp_file_path)
        
    except Exception as e:
        logger.error(f"خطا در handle_uploaded_file برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در پردازش فایل Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
        
        # حذف فایل موقت در صورت خطا
        temp_file_path = f"temp_{chat_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    
    return ConversationHandler.END

# ویژگی حذف رکورد
async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(
                f"📭  هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        df = pd.read_excel(excel_file)
        
        if df.empty:
            await update.message.reply_text(
                f"📭  هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        context.user_data['chat_id'] = chat_id
        
        msg = f"🗑️ **حذف رکورد Chat ID {chat_id}**\n\n"
        msg += "شماره ردیف مورد نظر برای حذف:\n\n"
        
        for i, row in df.iterrows():
            name = clean_value(row.get('نام', f'ردیف {i+1}'))
            family = clean_value(row.get('نام خانوادگی', ''))
            if family:
                name += f" {family}"
            msg += f"{i+1}. {name}\n"
        
        await update.message.reply_text(msg)
        return DELETE_ROW
        
    except Exception as e:
        logger.error(f"خطا در delete_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در بارگذاری رکوردهای Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def delete_row_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        row_num = int(update.message.text) - 1
        excel_file = get_excel_file(chat_id)
        df = pd.read_excel(excel_file)
        
        if row_num < 0 or row_num >= len(df):
            await update.message.reply_text(f"❌  شماره ردیف نامعتبر است برای Chat ID {chat_id}.")
            return DELETE_ROW
        
        deleted_name = clean_value(df.iloc[row_num].get('نام', f'ردیف {row_num+1}'))
        df = df.drop(df.index[row_num]).reset_index(drop=True)
        
        user_theme = load_user_theme(chat_id)
        if create_excel(df, user_theme, chat_id):
            await update.message.reply_text(
                f"✅  رکورد '{deleted_name}' از Chat ID {chat_id} با موفقیت حذف شد!\n"
                f"📊  تعداد باقیمانده: {len(df):,} رکورد",
                reply_markup=get_keyboard()
            )
            logger.info(f"کاربر {chat_id} رکورد {deleted_name} را حذف کرد")
        else:
            raise Exception("خطا در ایجاد فایل Excel")
            
    except ValueError:
        await update.message.reply_text(f"❌  لطفاً یک عدد معتبر برای Chat ID {chat_id} وارد کنید.")
        return DELETE_ROW
    except Exception as e:
        logger.error(f"خطا در delete_row_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در حذف رکورد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# import کردن get_keyboard
from main1 import get_keyboard
