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

# ویژگی‌های مدیریت فیلدها
async def manage_fields_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        fields = load_fields(chat_id)
        
        msg = f"⚙️ **مدیریت فیلدهای Chat ID {chat_id}**\n\n"
        msg += f"📋  **فیلدهای فعلی ({len(fields)}):**\n"
        
        for i, field in enumerate(fields, 1):
            msg += f"{i}. {field}\n"
        
        keyboard = [
            [KeyboardButton("➕ اضافه کردن فیلد"), KeyboardButton("➖ حذف فیلد")],
            [KeyboardButton("🔄 بازنشانی به پیش‌فرض"), KeyboardButton("❌ بازگشت")]
        ]
        
        await update.message.reply_text(
            msg, 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return MANAGE_FIELDS
        
    except Exception as e:
        logger.error(f"خطا در manage_fields_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در بارگذاری فیلدهای Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def manage_fields_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    action = update.message.text
    
    if action == "❌ بازگشت":
        await update.message.reply_text(
            f"🏠  بازگشت به منوی اصلی Chat ID {chat_id}",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    elif action == "➕ اضافه کردن فیلد":
        fields = load_fields(chat_id)
        
        if len(fields) >= MAX_FIELDS_PER_USER:
            await update.message.reply_text(
                f"❌  حداکثر تعداد فیلد ({MAX_FIELDS_PER_USER}) برای Chat ID {chat_id} رسیده است.",
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        context.user_data['chat_id'] = chat_id
        await update.message.reply_text(
            f"📝  **Chat ID {chat_id}**\nنام فیلد جدید را وارد کنید:"
        )
        return ADD_FIELD
    
    elif action == "➖ حذف فیلد":
        fields = load_fields(chat_id)
        
        if len(fields) <= 2:
            await update.message.reply_text(
                f"❌  باید حداقل 2 فیلد برای Chat ID {chat_id} باقی بماند.",
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        context.user_data['chat_id'] = chat_id
        keyboard = [[KeyboardButton(field)] for field in fields]
        keyboard.append([KeyboardButton("❌ لغو")])
        
        await update.message.reply_text(
            f"🗑️  **Chat ID {chat_id}**\nفیلد مورد نظر برای حذف را انتخاب کنید:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return DELETE_FIELD_SELECT
    
    elif action == "🔄 بازنشانی به پیش‌فرض":
        try:
            save_fields(DEFAULT_FIELDS.copy(), chat_id)
            
            excel_file = get_excel_file(chat_id)
            if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
                df = pd.read_excel(excel_file)
                
                new_df = pd.DataFrame(columns=DEFAULT_FIELDS)
                for col in DEFAULT_FIELDS:
                    if col in df.columns:
                        new_df[col] = df[col]
                
                user_theme = load_user_theme(chat_id)
                create_excel(new_df, user_theme, chat_id)
            
            await update.message.reply_text(
                f"✅  فیلدهای Chat ID {chat_id} به حالت پیش‌فرض بازنشانی شد!",
                reply_markup=get_keyboard()
            )
            logger.info(f"فیلدهای chat_id {chat_id} بازنشانی شد")
            
        except Exception as e:
            logger.error(f"خطا در بازنشانی فیلدهای chat_id {chat_id}: {e}")
            await update.message.reply_text(
                f"❌  خطا در بازنشانی فیلدهای Chat ID {chat_id}.",
                reply_markup=get_keyboard()
            )
        
        return ConversationHandler.END
    
    return MANAGE_FIELDS

async def add_field_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    new_field = update.message.text.strip()
    
    try:
        if not new_field or len(new_field) > MAX_FIELD_LENGTH:
            await update.message.reply_text(
                f"❌  نام فیلد Chat ID {chat_id} باید بین 1 تا {MAX_FIELD_LENGTH} کاراکتر باشد."
            )
            return ADD_FIELD
        
        fields = load_fields(chat_id)
        
        if new_field in fields:
            await update.message.reply_text(
                f"❌  فیلد '{new_field}' قبلاً برای Chat ID {chat_id} وجود دارد."
            )
            return ADD_FIELD
        
        fields.append(new_field)
        save_fields(fields, chat_id)
        
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            df[new_field] = ""
            user_theme = load_user_theme(chat_id)
            create_excel(df, user_theme, chat_id)
        
        await update.message.reply_text(
            f"✅  فیلد '{new_field}' با موفقیت به Chat ID {chat_id} اضافه شد!",
            reply_markup=get_keyboard()
        )
        logger.info(f"فیلد '{new_field}' به chat_id {chat_id} اضافه شد")
        
    except Exception as e:
        logger.error(f"خطا در add_field_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در اضافه کردن فیلد Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

async def delete_field_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    field_to_delete = update.message.text
    
    if field_to_delete == "❌ لغو":
        await update.message.reply_text(
            f"❌  حذف فیلد Chat ID {chat_id} لغو شد.",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    try:
        fields = load_fields(chat_id)
        
        if field_to_delete not in fields:
            await update.message.reply_text(
                f"❌  فیلد '{field_to_delete}' برای Chat ID {chat_id} یافت نشد."
            )
            return DELETE_FIELD_SELECT
        
        fields.remove(field_to_delete)
        save_fields(fields, chat_id)
        
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            if field_to_delete in df.columns:
                df = df.drop(columns=[field_to_delete])
                user_theme = load_user_theme(chat_id)
                create_excel(df, user_theme, chat_id)
        
        await update.message.reply_text(
            f"✅  فیلد '{field_to_delete}' با موفقیت از Chat ID {chat_id} حذف شد!",
            reply_markup=get_keyboard()
        )
        logger.info(f"فیلد '{field_to_delete}' از chat_id {chat_id} حذف شد")
        
    except Exception as e:
        logger.error(f"خطا در delete_field_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در حذف فیلد Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ویژگی تغییر تم
async def change_theme_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        current_theme = load_user_theme(chat_id)
        
        msg = f"🎨  **تغییر تم Chat ID {chat_id}**\n\n"
        msg += f"🔰  تم فعلی: {THEMES[current_theme]['name']}\n\n"
        msg += f"🎨  **تم‌های موجود:**\n"
        
        keyboard = []
        for theme_key, theme_info in THEMES.items():
            status = "✅" if theme_key == current_theme else "⚪"
            keyboard.append([KeyboardButton(f"{status} {theme_info['name']}")])
        
        keyboard.append([KeyboardButton("❌ بازگشت")])
        
        await update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CHANGE_THEME
        
    except Exception as e:
        logger.error(f"خطا در change_theme_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در بارگذاری تم‌های Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def change_theme_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    selected = update.message.text
    
    if selected == "❌ بازگشت":
        await update.message.reply_text(
            f"🏠  بازگشت به منوی اصلی Chat ID {chat_id}",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    try:
        selected_theme = None
        for theme_key, theme_info in THEMES.items():
            if theme_info['name'] in selected:
                selected_theme = theme_key
                break
        
        if not selected_theme:
            await update.message.reply_text(
                f"❌  تم نامعتبر برای Chat ID {chat_id}. لطفاً دوباره انتخاب کنید."
            )
            return CHANGE_THEME
        
        save_user_theme(chat_id, selected_theme)
        
        excel_file = get_excel_file(chat_id)
        if os.path.exists(excel_file) and os.path.getsize(excel_file) > 0:
            df = pd.read_excel(excel_file)
            create_excel(df, selected_theme, chat_id)
        
        await update.message.reply_text(
            f"✅  **تم Chat ID {chat_id} با موفقیت تغییر کرد!**\n"
            f"🎨  تم جدید: {THEMES[selected_theme]['name']}\n\n"
            f"💡  فایل Excel شما با تم جدید بازسازی شد.",
            reply_markup=get_keyboard()
        )
        logger.info(f"تم chat_id {chat_id} به {selected_theme} تغییر کرد")
        
    except Exception as e:
        logger.error(f"خطا در change_theme_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در تغییر تم Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ویژگی حذف همه
async def delete_all_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        keyboard = [
            [KeyboardButton("✅ بله، همه را حذف کن"), KeyboardButton("❌ خیر، لغو کن")]
        ]
        
        msg = f"⚠️ **هشدار مهم Chat ID {chat_id}**\n\n"
        msg += f"🗑️  شما در حال حذف **تمام {len(df):,} رکورد** هستید!\n\n"
        msg += f"❗  این عملیات قابل بازگشت نیست.\n"
        msg += f"💾  توصیه می‌شود ابتدا بکاپ تهیه کنید.\n\n"
        msg += f"❓  آیا مطمئن هستید؟"
        
        await update.message.reply_text(
            msg,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return CONFIRM_DELETE_ALL
        
    except Exception as e:
        logger.error(f"خطا در delete_all_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در بارگذاری رکوردهای Chat ID {chat_id}.",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def delete_all_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    response = update.message.text
    
    if response == "❌ خیر، لغو کن":
        await update.message.reply_text(
            f"✅  حذف همه رکوردهای Chat ID {chat_id} لغو شد.",
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    elif response == "✅ بله، همه را حذف کن":
        try:
            create_backup(chat_id)
            
            fields = load_fields(chat_id)
            empty_df = pd.DataFrame(columns=fields)
            user_theme = load_user_theme(chat_id)
            
            if create_excel(empty_df, user_theme, chat_id):
                await update.message.reply_text(
                    f"✅  **تمام رکوردهای Chat ID {chat_id} حذف شد!**\n\n"
                    f"💾  بکاپ خودکار ایجاد شد.\n"
                    f"🔄  فایل Excel خالی آماده است.\n"
                    f"🏠  بازگشت به منوی اصلی...",
                    reply_markup=get_keyboard()
                )
                logger.info(f"تمام رکوردهای chat_id {chat_id} حذف شد")
            else:
                raise Exception("خطا در ایجاد فایل Excel خالی")
                
        except Exception as e:
            logger.error(f"خطا در delete_all_confirm برای chat_id {chat_id}: {e}")
            await update.message.reply_text(
                f"❌  خطا در حذف رکوردهای Chat ID {chat_id}.",
                reply_markup=get_keyboard()
            )
        
        return ConversationHandler.END
    
    else:
        await update.message.reply_text(
            f"❌  لطفاً یکی از گزینه‌های ارائه شده را برای Chat ID {chat_id} انتخاب کنید."
        )
        return CONFIRM_DELETE_ALL

# import کردن get_keyboard
from main1 import get_keyboard
