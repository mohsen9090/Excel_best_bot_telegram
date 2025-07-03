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

# ویژگی‌های ویرایش
async def edit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(
                f"📭  هیچ رکوردی برای ویرایش در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        df = pd.read_excel(excel_file)
        
        if df.empty:
            await update.message.reply_text(
                f"📭  هیچ رکوردی برای ویرایش در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        context.user_data['chat_id'] = chat_id
        
        msg = f"✏️ **ویرایش رکورد Chat ID {chat_id}**\n\n"
        msg += f"شماره ردیف مورد نظر برای ویرایش:\n\n"
        
        for i, row in df.iterrows():
            name = clean_value(row.get('نام', f'ردیف {i+1}'))
            family = clean_value(row.get('نام خانوادگی', ''))
            if family:
                name += f" {family}"
            msg += f"{i+1}. {name}\n"
        
        await update.message.reply_text(msg)
        return EDIT_ROW
        
    except Exception as e:
        logger.error(f"خطا در edit_start برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در بارگذاری رکوردهای Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END

async def edit_row_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        row_num = int(update.message.text) - 1
        excel_file = get_excel_file(chat_id)
        df = pd.read_excel(excel_file)
        
        if row_num < 0 or row_num >= len(df):
            await update.message.reply_text(f"❌  شماره ردیف نامعتبر است برای Chat ID {chat_id}.")
            return EDIT_ROW
        
        context.user_data['edit_row'] = row_num
        context.user_data['chat_id'] = chat_id
        
        fields = load_fields(chat_id)
        keyboard = [[KeyboardButton(field)] for field in fields]
        keyboard.append([KeyboardButton("❌  لغو")])
        
        await update.message.reply_text(
            f"🔧  **ویرایش رکورد {row_num + 1} از Chat ID {chat_id}**\n\n"
            f"فیلد مورد نظر برای ویرایش:", 
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return EDIT_FIELD
        
    except ValueError:
        await update.message.reply_text(f"❌  لطفاً یک عدد معتبر برای Chat ID {chat_id} وارد کنید.")
        return EDIT_ROW

async def edit_field_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    field = update.message.text
    
    if field == "❌  لغو":
        await update.message.reply_text(
            f"❌  ویرایش Chat ID {chat_id} لغو شد.", 
            reply_markup=get_keyboard()
        )
        return ConversationHandler.END
    
    fields = load_fields(chat_id)
    
    if field not in fields:
        await update.message.reply_text(f"❌  فیلد نامعتبر است برای Chat ID {chat_id}.")
        return EDIT_FIELD
    
    context.user_data['edit_field'] = field
    
    try:
        excel_file = get_excel_file(chat_id)
        df = pd.read_excel(excel_file)
        current_value = clean_value(df.iloc[context.user_data['edit_row']][field])
        if not current_value:
            current_value = "خالی"
        
        await update.message.reply_text(
            f"📝  **Chat ID {chat_id} - ویرایش فیلد**\n"
            f"🔧  **فیلد:** {field}\n"
            f"🔍  **مقدار فعلی:** {current_value}\n\n"
            f"✏️ **مقدار جدید را وارد کنید:**",
            reply_markup=ReplyKeyboardMarkup([["❌  لغو"]], resize_keyboard=True)
        )
    except Exception:
        await update.message.reply_text(
            f"✏️ **Chat ID {chat_id}** - مقدار جدید را وارد کنید:",
            reply_markup=ReplyKeyboardMarkup([["❌  لغو"]], resize_keyboard=True)
        )
    
    return EDIT_VALUE

async def edit_value_apply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        value = update.message.text.strip()
        
        if value == "❌  لغو":
            await update.message.reply_text(
                f"❌  ویرایش Chat ID {chat_id} لغو شد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        field = context.user_data['edit_field']
        row = context.user_data['edit_row']
        
        is_valid, validated_value = validate_field_input(field, value)
        if not is_valid:
            await update.message.reply_text(f"❌  Chat ID {chat_id}: {validated_value}")
            return EDIT_VALUE
        
        excel_file = get_excel_file(chat_id)
        df = pd.read_excel(excel_file)
        old_value = clean_value(df.at[row, field])
        df.at[row, field] = validated_value
        
        user_theme = load_user_theme(chat_id)
        if create_excel(df, user_theme, chat_id):
            await update.message.reply_text(
                f"✅  **ویرایش Chat ID {chat_id} موفق!**\n"
                f"🔧  فیلد: {field}\n"
                f"🔄  از: {old_value}\n"
                f"➡️ به: {validated_value}",
                reply_markup=get_keyboard()
            )
            logger.info(f"کاربر {chat_id} فیلد {field} را ویرایش کرد")
        else:
            raise Exception("خطا در ایجاد فایل Excel")
        
    except Exception as e:
        logger.error(f"خطا در edit_value_apply برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در ویرایش رکورد Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# ویژگی‌های جستجو
async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    context.user_data['chat_id'] = chat_id
    
    await update.message.reply_text(
        f"🔍  **جستجو در فایل Chat ID {chat_id}**\n\n"
        f"کلمه کلیدی جستجو را وارد کنید:"
    )
    return SEARCH_QUERY

async def search_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        query = update.message.text.strip()
        
        if not query:
            await update.message.reply_text(f"❌  لطفاً کلمه کلیدی برای Chat ID {chat_id} وارد کنید.")
            return SEARCH_QUERY
        
        ensure_excel_file(chat_id)
        excel_file = get_excel_file(chat_id)
        
        if not os.path.exists(excel_file) or os.path.getsize(excel_file) == 0:
            await update.message.reply_text(
                f"📭  هیچ رکوردی برای جستجو در Chat ID {chat_id} وجود ندارد.", 
                reply_markup=get_keyboard()
            )
            return ConversationHandler.END
        
        df = pd.read_excel(excel_file)
        found_records = search_in_dataframe(df, query, chat_id)
        
        if not found_records:
            await update.message.reply_text(
                f"❌  هیچ نتیجه‌ای برای '{query}' در Chat ID {chat_id} یافت نشد.",
                reply_markup=get_keyboard()
            )
        else:
            msg = f"🔍  **نتایج جستجو Chat ID {chat_id}**\n"
            msg += f"📝  جستجو برای: '{query}'\n"
            msg += f"📊  تعداد نتایج: {len(found_records)}\n\n"
            
            for record in found_records:
                row_data = record['row_data']
                matched_field = record['matched_field']
                row_index = record['index']
                
                record_info = []
                for col in df.columns[:3]:
                    value = clean_value(row_data[col])
                    if value:
                        record_info.append(f"{col}: {value}")
                
                msg += f"**{row_index}.** {' | '.join(record_info)}\n"
                msg += f"   📍  یافت شده در: {matched_field}\n\n"
            
            if len(found_records) == MAX_SEARCH_RESULTS:
                msg += f"💡  فقط {MAX_SEARCH_RESULTS} نتیجه اول نمایش داده شد."
            
            await update.message.reply_text(msg, reply_markup=get_keyboard())
        
        logger.info(f"کاربر {chat_id} جستجو کرد: {query}")
        
    except Exception as e:
        logger.error(f"خطا در search_process برای chat_id {chat_id}: {e}")
        await update.message.reply_text(
            f"❌  خطا در جستجوی Chat ID {chat_id}.", 
            reply_markup=get_keyboard()
        )
    
    return ConversationHandler.END

# import کردن get_keyboard
from main1 import get_keyboard
