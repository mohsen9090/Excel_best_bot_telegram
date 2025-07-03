#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات مدیریت Excel پیشرفته - فایل اصلی اجرا
نسخه 2.1 - با تفکیک کامل Chat ID و امکانات پیشرفته
"""

import logging
import pandas as pd
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

from config import *
from utils import *

# وارد کردن تمام توابع از main1
from main1 import (
    start, get_keyboard, add_record_start, add_record_process,
    show_all_records, send_excel_file, edit_start, edit_row_select,
    edit_field_select, edit_value_apply, cancel, search_start, search_process,
    upload_file_start, upload_file_process, handle_uploaded_file,
    show_statistics, create_backup_manual, show_help,
    logger
)

# ============================ توابع اضافی ============================

async def universal_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت عمومی در صورت خطا"""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"❌ خطا در درک دستور Chat ID {chat_id}!\n🏠 بازگشت به منوی اصلی...",
        reply_markup=get_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

# ============================ حذف رکورد ============================

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف رکورد با تفکیک Chat ID"""
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(
                f"📭 هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        df = pd.read_excel(excel_file)
        
        if df.empty:
            await update.message.reply_text(
                f"📭 هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد.", 
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
            f"❌ خطا در بارگذاری رکوردهای Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def delete_row_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش حذف رکورد با تفکیک Chat ID"""
    chat_id = update.effective_chat.id
    
    try:
        row_num = int(update.message.text) - 1
        excel_file = get_excel_file(chat_id)
        df = pd.read_excel(excel_file)
        
        if row_num < 0 or row_num >= len(df):
            await update.message.reply_text(f"❌ شماره ردیف نامعتبر است برای Chat ID {chat_id}.")
            return DELETE_ROW
        
        deleted_name = clean_value(df.iloc[row_num].get('نام', f'ردیف {row_num+1}'))
        df = df.drop(df.index[row_num]).reset_index(drop=True)
        
        user_theme = load_user_theme(chat_id)
        if create_excel(df, user_theme, chat_id):
            await update.message.reply_text(
                f"✅ رکورد '{deleted_name}' از Chat ID {chat_id} با موفقیت حذف شد!\n"
                f"📊 تعداد باقیمانده: {len(df):,} رکورد",
                reply_markup=get_keyboard()
            )
            logger.info(f"کاربر {chat_id} رکورد {deleted_name} را حذف کرد")
        else:
            raise Exception("خطا در ایجاد فایل Excel")
            
    except ValueError:
        await update.message.reply_text(f"❌ لطفاً یک عدد معتبر برای Chat ID {chat_id} وارد کنید.")
        return DELETE_ROW
    except Exception as e:
        logger.error(f"خطا در delete_row_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌ خطا در حذف رکورد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ============================ مدیریت فیلدها ============================

async def manage_fields_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع مدیریت فیلدها با تفکیک Chat ID"""
    chat_id = update.effective_chat.id
    fields = load_fields(chat_id)
    
    context.user_data['chat_id'] = chat_id
    
    keyboard = [
        ["➕ اضافه کردن فیلد جدید"],
        ["🗑️ حذف فیلد موجود"],
        ["📋 نمایش فیلدهای فعلی"],
        ["❌ بازگشت"]
    ]
    
    msg = f"⚙️ **مدیریت فیلدهای Chat ID {chat_id}**\n\n"
    msg += f"📋 فیلدهای فعلی ({len(fields)} عدد):\n"
    for i, field in enumerate(fields, 1):
        msg += f"{i}. {field}\n"
    
    msg += f"\n💡 حداکثر {MAX_FIELDS_PER_USER} فیلد مجاز است."
    
    await update.message.reply_text(
        msg, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return MANAGE_FIELDS

async def manage_fields_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش مدیریت فیلدها"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == "❌ بازگشت":
        await update.message.reply_text(
            f"🏠 بازگشت به منوی اصلی Chat ID {chat_id}", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
        
    elif text == "➕ اضافه کردن فیلد جدید":
        fields = load_fields(chat_id)
        if len(fields) >= MAX_FIELDS_PER_USER:
            await update.message.reply_text(
                f"❌ نمی‌توان بیش از {MAX_FIELDS_PER_USER} فیلد برای Chat ID {chat_id} داشت."
            )
            return MANAGE_FIELDS
        
        await update.message.reply_text(
            f"📝 **Chat ID {chat_id}** - نام فیلد جدید را وارد کنید:"
        )
        return ADD_FIELD
        
    elif text == "🗑️ حذف فیلد موجود":
        fields = load_fields(chat_id)
        if len(fields) <= 1:
            await update.message.reply_text(
                f"❌ نمی‌توان همه فیلدهای Chat ID {chat_id} را حذف کرد."
            )
            return MANAGE_FIELDS
        
        keyboard = [[field] for field in fields]
        keyboard.append(["❌ لغو"])
        await update.message.reply_text(
            f"🗑️ **Chat ID {chat_id}** - فیلد مورد نظر برای حذف:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return DELETE_FIELD_SELECT
        
    elif text == "📋 نمایش فیلدهای فعلی":
        fields = load_fields(chat_id)
        msg = f"📋 **فیلدهای فعلی Chat ID {chat_id}** ({len(fields)} عدد):\n\n"
        for i, field in enumerate(fields, 1):
            msg += f"{i}. {field}\n"
        await update.message.reply_text(msg)
        return MANAGE_FIELDS
    else:
        await update.message.reply_text(f"❌ گزینه نامعتبر است برای Chat ID {chat_id}.")
        return MANAGE_FIELDS

async def add_field_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اضافه کردن فیلد جدید"""
    chat_id = update.effective_chat.id
    
    try:
        new_field = update.message.text.strip()
        
        if not new_field:
            await update.message.reply_text(f"❌ نام فیلد نمی‌تواند خالی باشد برای Chat ID {chat_id}.")
            return ADD_FIELD
        
        if len(new_field) > MAX_FIELD_LENGTH:
            await update.message.reply_text(
                f"❌ نام فیلد نباید از {MAX_FIELD_LENGTH} کاراکتر بیشتر باشد برای Chat ID {chat_id}."
            )
            return ADD_FIELD
        
        fields = load_fields(chat_id)
        if new_field in fields:
            await update.message.reply_text(f"❌ این فیلد قبلاً در Chat ID {chat_id} وجود دارد.")
            return ADD_FIELD
        
        fields.append(new_field)
        save_fields(fields, chat_id)
        
        # اضافه کردن ستون جدید به فایل موجود
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            df[new_field] = ""
            user_theme = load_user_theme(chat_id)
            create_excel(df, user_theme, chat_id)
        
        await update.message.reply_text(
            f"✅ فیلد '{new_field}' با موفقیت به Chat ID {chat_id} اضافه شد!\n"
            f"📊 تعداد کل فیلدها: {len(fields)}",
            reply_markup=get_keyboard()
        )
        
        logger.info(f"کاربر {chat_id} فیلد {new_field} را اضافه کرد")
        
    except Exception as e:
        logger.error(f"خطا در add_field_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌ خطا در اضافه کردن فیلد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

async def delete_field_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف فیلد موجود"""
    chat_id = update.effective_chat.id
    
    try:
        field_to_delete = update.message.text
        
        if field_to_delete == "❌ لغو":
            await update.message.reply_text(
                f"❌ حذف فیلد Chat ID {chat_id} لغو شد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        fields = load_fields(chat_id)
        if field_to_delete not in fields:
            await update.message.reply_text(f"❌ فیلد نامعتبر است برای Chat ID {chat_id}.")
            return DELETE_FIELD_SELECT
        
        if len(fields) <= 1:
            await update.message.reply_text(
                f"❌ نمی‌توان آخرین فیلد Chat ID {chat_id} را حذف کرد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        fields.remove(field_to_delete)
        save_fields(fields, chat_id)
        
        # حذف ستون از فایل موجود
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            if field_to_delete in df.columns:
                df = df.drop(columns=[field_to_delete])
                user_theme = load_user_theme(chat_id)
                create_excel(df, user_theme, chat_id)
        
        await update.message.reply_text(
            f"✅ فیلد '{field_to_delete}' از Chat ID {chat_id} با موفقیت حذف شد!\n"
            f"📊 تعداد باقیمانده: {len(fields)} فیلد",
            reply_markup=get_keyboard()
        )
        
        logger.info(f"کاربر {chat_id} فیلد {field_to_delete} را حذف کرد")
        
    except Exception as e:
        logger.error(f"خطا در delete_field_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌ خطا در حذف فیلد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ============================ حذف همه رکوردها ============================

async def delete_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع حذف همه رکوردها"""
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(
                f"📭 هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد."
            )
            return ConversationHandler.END
        
        df = pd.read_excel(excel_file)
        if df.empty:
            await update.message.reply_text(
                f"📭 هیچ رکوردی برای حذف در Chat ID {chat_id} وجود ندارد."
            )
            return ConversationHandler.END
        
        context.user_data['chat_id'] = chat_id
        
        keyboard = [
            ["✅ بله، همه را حذف کن"],
            ["❌ لغو"]
        ]
        
        await update.message.reply_text(
            f"⚠️ **هشدار Chat ID {chat_id}!**\n\n"
            f"آیا مطمئن هستید که می‌خواهید {len(df):,} رکورد را حذف کنید?\n"
            f"🚨 این عمل غیرقابل بازگشت است!\n\n"
            f"💾 توصیه: ابتدا بکاپ بگیرید.",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CONFIRM_DELETE_ALL
        
    except Exception as e:
        logger.error(f"خطا در delete_all_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(f"❌ خطا در دسترسی به فایل Chat ID {chat_id}.")
        return ConversationHandler.END

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأیید حذف همه رکوردها"""
    chat_id = update.effective_chat.id
    
    try:
        text = update.message.text
        
        if text == "❌ لغو":
            await update.message.reply_text(
                f"❌ حذف همه رکوردهای Chat ID {chat_id} لغو شد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
            
        elif text == "✅ بله، همه را حذف کن":
            # ایجاد بکاپ اتوماتیک قبل از حذف
            if AUTO_BACKUP:
                create_backup(chat_id)
            
            fields = load_fields(chat_id)
            empty_df = pd.DataFrame(columns=fields)
            user_theme = load_user_theme(chat_id)
            
            if create_excel(empty_df, user_theme, chat_id):
                await update.message.reply_text(
                    f"✅ همه رکوردهای Chat ID {chat_id} با موفقیت حذف شدند! 🧹\n\n"
                    f"💾 بکاپ خودکار ایجاد شد.\n"
                    f"🔒 فیلدهای شما حفظ شدند.",
                    reply_markup=get_keyboard()
                )
                logger.info(f"کاربر {chat_id} همه رکوردها را حذف کرد")
            else:
                raise Exception("خطا در ایجاد فایل Excel خالی")
        else:
            await update.message.reply_text(
                f"❌ لطفاً یکی از گزینه‌های Chat ID {chat_id} را انتخاب کنید."
            )
            return CONFIRM_DELETE_ALL
            
    except Exception as e:
        logger.error(f"خطا در confirm_delete_all برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌ خطا در حذف رکوردهای Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ============================ تغییر تم ============================

async def change_theme_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع تغییر تم"""
    chat_id = update.effective_chat.id
    current_theme = load_user_theme(chat_id)
    
    context.user_data['chat_id'] = chat_id
    
    keyboard = []
    
    for theme_key, theme_data in THEMES.items():
        status = "✅" if theme_key == current_theme else "⚪"
        keyboard.append([f"{status} {theme_data['name']}"])
    
    keyboard.append(["❌ لغو"])
    
    msg = f"🎨 **انتخاب تم رنگی Chat ID {chat_id}**\n\n"
    msg += f"🎯 تم فعلی: {THEMES[current_theme]['name']}\n\n"
    msg += "💡 تم جدید را انتخاب کنید:"
    
    await update.message.reply_text(
        msg, 
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return CHANGE_THEME

async def change_theme_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش تغییر تم"""
    chat_id = update.effective_chat.id
    
    try:
        text = update.message.text
        
        if text == "❌ لغو":
            await update.message.reply_text(
                f"❌ تغییر تم Chat ID {chat_id} لغو شد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        selected_theme = None
        for theme_key, theme_data in THEMES.items():
            if theme_data['name'] in text:
                selected_theme = theme_key
                break
        
        if not selected_theme:
            await update.message.reply_text(f"❌ تم نامعتبر است برای Chat ID {chat_id}.")
            return CHANGE_THEME
        
        save_user_theme(chat_id, selected_theme)
        
        # بازسازی فایل با تم جدید
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            create_excel(df, selected_theme, chat_id)
        
        await update.message.reply_text(
            f"✅ تم Chat ID {chat_id} به '{THEMES[selected_theme]['name']}' تغییر یافت! 🎨\n\n"
            f"🎯 فایل Excel شما با تم جدید بازسازی شد.",
            reply_markup=get_keyboard()
        )
        
        logger.info(f"کاربر {chat_id} تم را به {selected_theme} تغییر داد")
        
    except Exception as e:
        logger.error(f"خطا در change_theme_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌ خطا در تغییر تم Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ============================ مدیریت پیام‌های متنی ============================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی با تفکیک Chat ID"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # ثبت فعالیت کاربر
    logger.info(f"کاربر {chat_id} پیام فرستاد: {text}")
    
    if text == "📤 آپلود فایل Excel":
        await upload_file_start(update, context)
    elif text in ["🔄 جایگزینی کامل فایل فعلی", "➕ ادغام با فایل موجود", "❌ لغو"]:
        # این متن‌ها توسط upload conversation handle میشن
        return
    elif text == "➕ اضافه کردن":
        await add_record_start(update, context)
    elif text == "📋 نمایش همه":
        await show_all_records(update, context)
    elif text == "📁 دریافت فایل":
        await send_excel_file(update, context)
    elif text == "✏️ ویرایش":
        await edit_start(update, context)
    elif text == "🗑️ حذف":
        await delete_start(update, context)
    elif text == "🔍 جستجو":
        await search_start(update, context)
    elif text == "📊 آمار":
        await show_statistics(update, context)
    elif text == "ℹ️ راهنما":
        await show_help(update, context)
    elif text == "⚙️ مدیریت فیلدها":
        await manage_fields_start(update, context)
    elif text == "🎨 تغییر تم":
        await change_theme_start(update, context)
    elif text == "🧹 حذف همه":
        await delete_all_start(update, context)
    elif text == "💾 بکاپ":
        await create_backup_manual(update, context)
    else:
        await update.message.reply_text(
            f"❌ دستور نامعتبر است برای Chat ID {chat_id}.\n"
            f"💡 از منوی زیر استفاده کنید:",
            reply_markup=get_keyboard()
        )

# ============================ تابع اصلی ============================

def main():
    """تابع اصلی اجرای ربات"""
    print("🚀 راه‌اندازی ربات Excel مدیریت کامل با تفکیک Chat ID...")
    print(f"🔧 توکن: {TOKEN[:10]}...")
    print("✅ آماده برای شروع!")
    
    # اطمینان از وجود پوشه‌ها
    ensure_directories()
    
    application = ApplicationBuilder().token(TOKEN).build()
    print("🔧 در حال راه‌اندازی ربات...")

    # تعریف ConversationHandler ها
    add_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕ اضافه کردن$"), add_record_start)],
        states={ADD_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_record_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    upload_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📤 آپلود فایل Excel$"), upload_file_start)],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, upload_file_process),
                MessageHandler(filters.Document.ALL, handle_uploaded_file)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    edit_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✏️ ویرایش$"), edit_start)],
        states={
            EDIT_ROW: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_row_select)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_select)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_apply)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    delete_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🗑️ حذف$"), delete_start)],
        states={
            DELETE_ROW: [
                MessageHandler(filters.TEXT & filters.Regex(r"^\d+$"), delete_row_process),
                MessageHandler(filters.TEXT & ~filters.COMMAND, universal_fallback)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    search_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍 جستجو$"), search_start)],
        states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    manage_fields_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ مدیریت فیلدها$"), manage_fields_start)],
        states={
            MANAGE_FIELDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_fields_process)],
            ADD_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_field_process)],
            DELETE_FIELD_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_field_process)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    theme_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎨 تغییر تم$"), change_theme_start)],
        states={CHANGE_THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_theme_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # اضافه کردن handler ها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(upload_conversation)
    application.add_handler(add_conversation)
    application.add_handler(edit_conversation)
    application.add_handler(delete_conversation)
    application.add_handler(search_conversation)
    application.add_handler(manage_fields_conversation)
    application.add_handler(delete_all_conversation)
    application.add_handler(theme_conversation)

    # Handler های ساده
    application.add_handler(MessageHandler(filters.Regex("^📋 نمایش همه$"), show_all_records))
    application.add_handler(MessageHandler(filters.Regex("^📁 دریافت فایل$"), send_excel_file))
    application.add_handler(MessageHandler(filters.Regex("^📊 آمار$"), show_statistics))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ راهنما$"), show_help))
    application.add_handler(MessageHandler(filters.Regex("^💾 بکاپ$"), create_backup_manual))
    
    # Handler کلی برای پیام‌های متنی (آخرین handler)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))

    print("🤖 ربات Excel مدیریت کامل با تفکیک Chat ID در حال اجرا...")
    print("✅ همه کلیدها فعال:")
    print("   • ➕ اضافه کردن")
    print("   • 📋 نمایش همه") 
    print("   • 📁 دریافت فایل")
    print("   • ✏️ ویرایش")
    print("   • 🗑️ حذف")
    print("   • 🔍 جستجو")
    print("   • 📤 آپلود فایل Excel")
    print("   • ⚙️ مدیریت فیلدها")
    print("   • 🎨 تغییر تم")
    print("   • 🧹 حذف همه")
    print("   • 💾 بکاپ")
    print("   • 📊 آمار")
    print("   • ℹ️ راهنما")
    print("🔒 تفکیک کامل Chat ID فعال!")
    print("📡 منتظر دریافت پیام...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n⏹️ ربات متوقف شد.")
    except Exception as e:
        print(f"❌ خطا در راه‌اندازی: {e}")
        logger.error(f"خطا در راه‌اندازی ربات: {e}")

if __name__ == "__main__":
    main()

