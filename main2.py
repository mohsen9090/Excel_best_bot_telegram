#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import pandas as pd
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters

from config import *
from utils import *

from main1 import (
   start, get_keyboard, add_record_start, add_record_process,
   show_all_records, send_excel_file, edit_start, edit_row_select,
   edit_field_select, edit_value_apply, cancel, search_start, search_process,
   upload_file_start, upload_file_process, handle_uploaded_file,
   show_statistics, create_backup_manual, show_help,
   logger
)

async def universal_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
   chat_id = update.effective_chat.id
   await update.message.reply_text(
       f"❌ خطا در درک دستور Chat ID {chat_id}!\n🏠 بازگشت به منوی اصلی...",
       reply_markup=get_keyboard()
   )
   context.user_data.clear()
   return ConversationHandler.END

async def delete_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

def main():
   print("🚀 راه‌اندازی ربات Excel مدیریت کامل با تفکیک Chat ID...")
   print(f"🔧 توکن: {TOKEN[:10]}...")
   print("✅ آماده برای شروع!")
   
   ensure_directories()
   
   application = ApplicationBuilder().token(TOKEN).build()
   print("🔧 در حال راه‌اندازی ربات...")

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

   application.add_handler(CommandHandler("start", start))
   application.add_handler(upload_conversation)
   application.add_handler(add_conversation)
   application.add_handler(edit_conversation)
   application.add_handler(delete_conversation)
   application.add_handler(search_conversation)

   application.add_handler(MessageHandler(filters.Regex("^📋 نمایش همه$"), show_all_records))
   application.add_handler(MessageHandler(filters.Regex("^📁 دریافت فایل$"), send_excel_file))
   application.add_handler(MessageHandler(filters.Regex("^📊 آمار$"), show_statistics))
   application.add_handler(MessageHandler(filters.Regex("^ℹ️ راهنما$"), show_help))
   application.add_handler(MessageHandler(filters.Regex("^💾 بکاپ$"), create_backup_manual))

   print("🤖 ربات Excel مدیریت کامل با تفکیک Chat ID در حال اجرا...")
   print("✅ همه کلیدها فعال:")
   print("   • ➕ اضافه کردن")
   print("   • 📋 نمایش همه") 
   print("   • 📁 دریافت فایل")
   print("   • ✏️ ویرایش")
   print("   • 🗑️ حذف")
   print("   • 🔍 جستجو")
   print("   • 📤 آپلود فایل Excel")
   print("   • 📊 آمار")
   print("   • 💾 بکاپ")
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
