#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

from config import *
from utils import *

# import کردن تمام ویژگی‌ها از فایل‌های مختلف
from main1 import (
    start, get_keyboard, add_record_start, add_record_process,
    show_all_records, send_excel_file, show_statistics, 
    create_backup_manual, show_help, cancel
)

from features import (
    edit_start, edit_row_select, edit_field_select, edit_value_apply,
    search_start, search_process
)

from advanced_features import (
    manage_fields_start, manage_fields_process, add_field_process, delete_field_process,
    change_theme_start, change_theme_process, delete_all_start, delete_all_confirm
)

from upload_features import (
    upload_file_start, upload_file_process, handle_uploaded_file,
    delete_start, delete_row_process
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def universal_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"❌  خطا در درک دستور Chat ID {chat_id}!\n🏠  بازگشت به منوی اصلی...",
        reply_markup=get_keyboard()
    )
    context.user_data.clear()
    return ConversationHandler.END

def main():
    print("🚀  راه‌اندازی ربات Excel مدیریت کامل با تفکیک Chat ID...")
    print(f"🔧  توکن: {TOKEN[:10]}...")
    print("✅  آماده برای شروع!")
    
    ensure_directories()
    
    application = ApplicationBuilder().token(TOKEN).build()
    print("🔧  در حال راه‌اندازی ربات...")

    # مکالمه اضافه کردن رکورد
    add_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^➕  اضافه کردن$"), add_record_start)],
        states={ADD_DATA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_record_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه آپلود فایل
    upload_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📤  آپلود فایل Excel$"), upload_file_start)],
        states={
            UPLOAD_FILE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, upload_file_process),
                MessageHandler(filters.Document.ALL, handle_uploaded_file)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه ویرایش
    edit_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✏️ ویرایش$"), edit_start)],
        states={
            EDIT_ROW: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_row_select)],
            EDIT_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_field_select)],
            EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_apply)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه حذف رکورد
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

    # مکالمه جستجو
    search_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🔍  جستجو$"), search_start)],
        states={SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه مدیریت فیلدها
    manage_fields_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ مدیریت فیلدها$"), manage_fields_start)],
        states={
            MANAGE_FIELDS: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage_fields_process)],
            ADD_FIELD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_field_process)],
            DELETE_FIELD_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_field_process)]
        },
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه تغییر تم
    change_theme_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🎨  تغییر تم$"), change_theme_start)],
        states={CHANGE_THEME: [MessageHandler(filters.TEXT & ~filters.COMMAND, change_theme_process)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # مکالمه حذف همه
    delete_all_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🧹  حذف همه$"), delete_all_start)],
        states={CONFIRM_DELETE_ALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_all_confirm)]},
        fallbacks=[CommandHandler("cancel", cancel), MessageHandler(filters.ALL, universal_fallback)]
    )

    # اضافه کردن همه مکالمه‌ها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(upload_conversation)
    application.add_handler(add_conversation)
    application.add_handler(edit_conversation)
    application.add_handler(delete_conversation)
    application.add_handler(search_conversation)
    application.add_handler(manage_fields_conversation)
    application.add_handler(change_theme_conversation)
    application.add_handler(delete_all_conversation)

    # دکمه‌های ساده
    application.add_handler(MessageHandler(filters.Regex("^📋  نمایش همه$"), show_all_records))
    application.add_handler(MessageHandler(filters.Regex("^📁  دریافت فایل$"), send_excel_file))
    application.add_handler(MessageHandler(filters.Regex("^📊  آمار$"), show_statistics))
    application.add_handler(MessageHandler(filters.Regex("^ℹ️ راهنما$"), show_help))
    application.add_handler(MessageHandler(filters.Regex("^💾  بکاپ$"), create_backup_manual))

    print("🤖  ربات Excel مدیریت کامل با تفکیک Chat ID در حال اجرا...")
    print("✅  همه کلیدها فعال:")
    print("   • ➕  اضافه کردن")
    print("   • 📋  نمایش همه") 
    print("   • 📁  دریافت فایل")
    print("   • ✏️ ویرایش")
    print("   • 🗑️ حذف")
    print("   • 🔍  جستجو")
    print("   • 📤  آپلود فایل Excel")
    print("   • ⚙️ مدیریت فیلدها")
    print("   • 🎨  تغییر تم")
    print("   • 📊  آمار")
    print("   • 🧹  حذف همه")
    print("   • 💾  بکاپ")
    print("   • ℹ️ راهنما")
    print("🔒  تفکیک کامل Chat ID فعال!")
    print("📡  منتظر دریافت پیام...")
    
    try:
        application.run_polling(drop_pending_updates=True)
    except KeyboardInterrupt:
        print("\n⏹️ ربات متوقف شد.")
    except Exception as e:
        print(f"❌  خطا در راه‌اندازی: {e}")
        logger.error(f"خطا در راه‌اندازی ربات: {e}")

if __name__ == "__main__":
    main()
