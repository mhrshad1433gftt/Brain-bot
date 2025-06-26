import logging
import uuid
import schedule
import time
import os
import json
from datetime import datetime, timedelta
import pytz
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
import re
import schedule
import threading
import shutil

# تنظیم لاگ‌گذاری برای دیباگ و ردیابی خطاها
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات اولیه بات با توکن
TOKEN = '8042250767:AAFdQHSifLCR_7KXvPfA5M8noErZ969N_A0'
ADMIN_ID = 1113652228
OWNER_ID = 1113652228
BOT_VERSION = "4.1.9"

# ایجاد نمونه بات
bot = telebot.TeleBot(TOKEN)

# کلاس ذخیره‌سازی داده‌ها برای مدیریت تمام اطلاعات
class DataStore:
def __init__(self):
        # امضاهای پیش‌فرض
        self.signatures = {
            "Default": {
                "template": "{Bold}\n\n{BlockQuote}\n\n{Simple}\n\n{Italic}\n\n{Code}\n\n{Strike}\n\n{Underline}\n\n{Spoiler}",
                "variables": ["Bold", "BlockQuote", "Simple", "Italic", "Code", "Strike", "Underline", "Spoiler"]
            }
        }
        self.variables = {}
        self.default_values = {}  # دیکشنری برای ذخیره مقادیر پیش‌فرض متغیرها
        self.user_states = {}
        self.user_data = {}
        self.settings = {
            "default_welcome": "🌟 خوش آمدید {name} عزیز! 🌟\n\nبه ربات مدیریت پست و امضا خوش آمدید."
        }
        self.channels = []
        self.scheduled_posts = []
        self.admins = [OWNER_ID]  # اضافه کردن اونر به لیست ادمین‌ها به‌صورت پیش‌فرض
        self.admin_permissions = {str(OWNER_ID): {
            "create_post": True,
            "signature_management": True,
            "variable_management": True,
            "default_values_management": True,
            "default_settings": True,
            "register_channel": True,
            "manage_timers": True,
            "options_management": True,
            "admin_management": True,
            "media_management": True  # دسترسی جدید
        }}
        self.timer_settings = {
            "timers_enabled": True,  # تنظیم پیش‌فرض: تایمرها فعال
            "inline_buttons_enabled": True  # تنظیم پیش‌فرض: کلیدهای شیشه‌ای فعال
        }
        self.last_message_id = {}  # برای ذخیره آیدی آخرین پیام ربات
        self.last_user_message_id = {}  # برای ذخیره آیدی پیام کاربر
        self.media_metadata = {}  # دیکشنری برای ذخیره متادیتای مدیاها
    
        # دیکشنری برای متن‌های وضعیت جهت اطلاع‌رسانی به کاربر
        self.state_messages = {
            None: "در حال حاضر در منوی اصلی هستید.",
            "signature_management": "در حال حاضر در حال مدیریت امضاها هستید.",
            "select_signature": "در حال حاضر در حال انتخاب امضا هستید.",
            "post_with_signature_media": "در حال حاضر در حال ارسال رسانه برای پست هستید.",
            "post_with_signature_values": "در حال حاضر در حال وارد کردن مقادیر پست هستید.",
            "post_with_signature_ready": "",
            "new_signature_name": "در حال حاضر در حال وارد کردن نام امضای جدید هستید.",
            "new_signature_template": "در حال حاضر در حال وارد کردن قالب امضا هستید。",
            "delete_signature": "در حال حاضر در حال حذف امضا هستید.",
            "admin_management": "در حال حاضر در حال مدیریت ادمین‌ها هستید.",
            "add_admin": "در حال حاضر در حال افزودن ادمین هستید。",
            "remove_admin": "در حال حاضر در حال حذف ادمین هستید.",
            "list_admins": "در حال حاضر در حال مشاهده لیست ادمین‌ها هستید.",
            "variable_management": "در حال حاضر در حال مدیریت متغیرها هستید.",
            "select_variable_format": "در حال حاضر در حال انتخاب نوع متغیر هستید.",
            "add_variable": "در حال حاضر در حال افزودن متغیر جدید هستید.",
            "remove_variable": "در حال حاضر در حال حذف متغیر هستید.",
            "set_default_settings": "در حال حاضر در حال تنظیم متن پیش‌فرض هستید.",
            "register_channel": "در حال حاضر در حال ثبت چنل هستید.",
            "set_timer": "در حال حاضر در حال تنظیم تایمر هستید.",
            "ask_for_inline_buttons": "در حال حاضر در حال پرسیدن برای افزودن کلید شیشه‌ای هستید.",
            "add_inline_button_name": "در حال حاضر در حال وارد کردن نام کلید شیشه‌ای هستید.",
            "add_inline_button_url": "در حال حاضر در حال وارد کردن لینک کلید شیشه‌ای هستید.",
            "ask_continue_adding_buttons": "در حال حاضر در حال پرسیدن برای ادامه افزودن کلیدها هستید.",
            "select_button_position": "در حال حاضر در حال انتخاب نحوه نمایش کلید شیشه‌ای بعدی هستید。",
            "schedule_post": "در حال حاضر در حال زمان‌بندی پست هستید。",
            "select_channel_for_post": "در حال حاضر در حال انتخاب چنل برای ارسال پست هستید。",
            "timer_inline_management": "در حال حاضر در حال مدیریت تایمرها و کلیدهای شیشه‌ای هستید。",
            "default_values_management": "در حال حاضر در حال مدیریت مقادیر پیش‌فرض هستید。",
            "set_default_value_select_var": "در حال حاضر در حال انتخاب متغیر برای تنظیم مقدار پیش‌فرض هستید.",
            "set_default_value": "در حال حاضر در حال وارد کردن مقدار پیش‌فرض هستید。",
            "remove_default_value": "در حال حاضر در حال حذف مقدار پیش‌فرض هستید。",
            "select_admin_for_permissions": "در حال حاضر در حال انتخاب ادمین برای تنظیم دسترسی‌ها هستید。",
            "manage_admin_permissions": "در حال حاضر در حال تنظیم دسترسی‌های ادمین هستید.",
            "media_management": "در حال حاضر در حال مدیریت فایل‌های مدیا هستید.",
            "delete_media": "در حال حاضر در حال انتخاب فایل مدیا برای حذف هستید.",
            "confirm_delete_media": "در حال حاضر در حال تأیید حذف فایل مدیا هستید.",
            "delete_sent_media": "در حال حاضر در حال تأیید حذف مدیاهای ارسال‌شده هستید."
        }
            
        os.makedirs("medias", exist_ok=True)  # ایجاد پوشه medias اگر وجود نداشته باشه
        self.load_data()
        
    def create_default_files(self):
        default_files = {
            'signatures.json': {
                "Default": {
                    "template": "{Bold}\n\n{BlockQuote}\n\n{Simple}\n\n{Italic}\n\n{Code}\n\n{Strike}\n\n{Underline}\n\n{Spoiler}",
                    "variables": ["Bold", "BlockQuote", "Simple", "Italic", "Code", "Strike", "Underline", "Spoiler"]
                }
            },
            'variables.json': {
                "Bold": {"format": "Bold"},
                "Italic": {"format": "Italic"},
                "Code": {"format": "Code"},
                "Strike": {"format": "Strike"},
                "Underline": {"format": "Underline"},
                "Spoiler": {"format": "Spoiler"},
                "BlockQuote": {"format": "BlockQuote"},
                "Simple": {"format": "Simple"}
            },
            'default_values.json': {},
            'user_data.json': {},
            'settings.json': {
                "default_welcome": "🌟 خوش آمدید {name} عزیز! 🌟\n\nبه ربات مدیریت پست و امضا خوش آمدید."
            },
            'channels.json': [],
            'scheduled_posts.json': [],
            'admins.json': [OWNER_ID],
            'admin_permissions.json': {str(OWNER_ID): {
                "create_post": True,
                "signature_management": True,
                "variable_management": True,
                "default_values_management": True,
                "default_settings": True,
                "register_channel": True,
                "manage_timers": True,
                "options_management": True,
                "admin_management": True,
                "media_management": True  # دسترسی جدید
            }},
            'timer_settings.json': {
                "timers_enabled": True,
                "inline_buttons_enabled": True
            },
            'media_metadata.json': {}  # فایل پیش‌فرض جدید
        }
        
        os.makedirs("jsons", exist_ok=True)
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsons")
        if not os.access(data_dir, os.W_OK):
            logger.error(f"عدم دسترسی به دایرکتوری برای نوشتن: {data_dir}")
            bot.send_message(OWNER_ID, f"⚠️ خطا: عدم دسترسی به دایرکتوری {data_dir} برای ذخیره‌سازی داده‌ها.")
            return False
        
        created_files = []
        existing_files = []
        for file_name, default_content in default_files.items():
            file_path = os.path.join("jsons", file_name)
            if not os.path.exists(file_path):
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=4)
                    logger.info(f"فایل {file_name} با موفقیت ایجاد شد.")
                    created_files.append(file_name)
                except Exception as e:
                    logger.error(f"خطا در ایجاد فایل {file_name}: {str(e)}")
                    bot.send_message(OWNER_ID, f"⚠️ خطا در ایجاد فایل {file_name}: {str(e)}")
            else:
                existing_files.append(file_name)
                logger.info(f"فایل {file_name} از قبل وجود دارد.")
        
        if created_files:
            bot.send_message(OWNER_ID, f"✅ فایل‌های زیر با موفقیت ایجاد شدند:\n{', '.join(created_files)}")
        if existing_files:
            bot.send_message(OWNER_ID, f"📄 فایل‌های زیر از قبل وجود دارند:\n{', '.join(existing_files)}")
        
        return True

    def load_data(self):
        if not self.create_default_files():
            return
        
        try:
            with open(os.path.join('jsons', 'signatures.json'), 'r', encoding='utf-8') as f:
                self.signatures = json.load(f)
                logger.info("فایل signatures.json با موفقیت لود شد.")
            
            with open(os.path.join('jsons', 'variables.json'), 'r', encoding='utf-8') as f:
                self.controls = json.load(f)
                for key, value in self.controls.items():
                    if not isinstance(value, dict) or 'format' not in value or value['format'] not in [
                        "Bold", "Italic", "Code", "Strike", "Underline", "Spoiler", "BlockQuote", "Simple"
                    ]:
                        logger.warning(f"متغیر نامعتبر: {key}. مقدار پیش‌فرض اعمال شد.")
                        self.controls[key] = {'format': 'Simple'}
            
            with open(os.path.join('jsons', 'default_values.json'), 'r', encoding='utf-8') as f:
                self.default_values = json.load(f)
            
            with open(os.path.join('jsons', 'user_data.json'), 'r', encoding='utf-8') as f:
                self.user_data = json.load(f)
            
            with open(os.path.join('jsons', 'settings.json'), 'r', encoding='utf-8') as f:
                self.settings = json.load(f)
            
            with open(os.path.join('jsons', 'channels.json'), 'r', encoding='utf-8') as f:
                self.channels = json.load(f)
            
            with open(os.path.join('jsons', 'scheduled_posts.json'), 'r', encoding='utf-8') as f:
                self.scheduled_posts = json.load(f)
            
            with open(os.path.join('jsons', 'admins.json'), 'r', encoding='utf-8') as f:
                self.admins = json.load(f)
                logger.info("فایل admins.json با موفقیت لود شد.")
            
            # چک برای وجود فایل admin_permissions.json
            if os.path.exists(os.path.join('jsons', 'admin_permissions.json')):
                with open(os.path.join('jsons', 'admin_permissions.json'), 'r', encoding='utf-8') as f:
                    self.admin_permissions = json.load(f)
                    logger.info("فایل admin_permissions.json با موفقیت لود شد.")
            else:
                logger.warning("فایل admin_permissions.json وجود ندارد. مقدار پیش‌فرض اعمال می‌شود.")
                self.admin_permissions = {str(OWNER_ID): {
                    "create_post": True,
                    "signature_management": True,
                    "variable_management": True,
                    "default_values_management": True,
                    "default_settings": True,
                    "register_channel": True,
                    "manage_timers": True,
                    "options_management": True,
                    "admin_management": True,
                    "media_management": True
                }}
                self.save_data()  # ذخیره مقدار پیش‌فرض
           
            with open(os.path.join('jsons', 'timer_settings.json'), 'r', encoding='utf-8') as f:
                self.timer_settings = json.load(f)
            
            # لود متادیتای مدیا
            if os.path.exists(os.path.join('jsons', 'media_metadata.json')):
                with open(os.path.join('jsons', 'media_metadata.json'), 'r', encoding='utf-8') as f:
                    self.media_metadata = json.load(f)
                    logger.info("فایل media_metadata.json با موفقیت لود شد.")
            else:
                logger.warning("فایل media_metadata.json وجود ندارد. مقدار پیش‌فرض اعمال می‌شود.")
                self.media_metadata = {}
                self.save_data()
        
        except Exception as e:
            logger.error(f"خطا در لود داده‌ها: {str(e)}")
            bot.send_message(OWNER_ID, f"⚠️ خطا در لود داده‌ها: {str(e)}")
        
    def save_data(self):
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jsons")
        os.makedirs(data_dir, exist_ok=True)
        if not os.access(data_dir, os.W_OK):
            logger.error(f"عدم دسترسی به دایرکتوری برای نوشتن: {data_dir}")
            bot.send_message(OWNER_ID, f"⚠️ خطا: عدم دسترسی به دایرکتوری {data_dir} برای ذخیره‌سازی داده‌ها.")
            return False
        
        try:
            with open(os.path.join('jsons', 'signatures.json'), 'w', encoding='utf-8') as f:
                json.dump(self.signatures, f, ensure_ascii=False, indent=4)
                logger.info("فایل signatures.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'variables.json'), 'w', encoding='utf-8') as f:
                json.dump(self.controls, f, ensure_ascii=False, indent=4)
                logger.info("فایل variables.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'default_values.json'), 'w', encoding='utf-8') as f:
                json.dump(self.default_values, f, ensure_ascii=False, indent=4)
                logger.info("فایل default_values.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'user_data.json'), 'w', encoding='utf-8') as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
                logger.info("فایل user_data.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'settings.json'), 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
                logger.info("فایل settings.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'channels.json'), 'w', encoding='utf-8') as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=4)
                logger.info("فایل channels.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'scheduled_posts.json'), 'w', encoding='utf-8') as f:
                json.dump(self.scheduled_posts, f, ensure_ascii=False, indent=4)
                logger.info("فایل scheduled_posts.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'admins.json'), 'w', encoding='utf-8') as f:
                json.dump(self.admins, f, ensure_ascii=False, indent=4)
                logger.info("فایل admins.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'admin_permissions.json'), 'w', encoding='utf-8') as f:
                json.dump(self.admin_permissions, f, ensure_ascii=False, indent=4)
                logger.info("فایل admin_permissions.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'timer_settings.json'), 'w', encoding='utf-8') as f:
                json.dump(self.timer_settings, f, ensure_ascii=False, indent=4)
                logger.info("فایل timer_settings.json با موفقیت ذخیره شد.")
            with open(os.path.join('jsons', 'media_metadata.json'), 'w', encoding='utf-8') as f:
                json.dump(self.media_metadata, f, ensure_ascii=False, indent=4)
                logger.info("فایل media_metadata.json با موفقیت ذخیره شد.")
            return True
        except Exception as e:
            logger.error(f"خطا در ذخیره‌سازی داده‌ها: {str(e)}")
            bot.send_message(OWNER_ID, f"⚠️ خطا در ذخیره‌سازی داده‌ها: {str(e)}")
            return False
        
    def get_user_state(self, user_id):
        if str(user_id) not in self.user_states:
            self.user_states[str(user_id)] = {
                "state": None,
                "data": {}
            }
        return self.user_states[str(user_id)]
    
    def update_user_state(self, user_id, state=None, data=None):
        if str(user_id) not in self.user_states:
            self.user_states[str(user_id)] = {
                "state": None,
                "data": {}
            }
        
        if state is not None:
            self.user_states[str(user_id)]["state"] = state
        if data is not None:
            self.user_states[str(user_id)]["data"].update(data)
    
    def reset_user_state(self, user_id):
        self.user_states[str(user_id)] = {
            "state": None,
            "data": {}
        }

data_store = DataStore()

def is_owner(user_id):
    return user_id == OWNER_ID

def is_admin(user_id):
    return user_id in data_store.admins

# منوی فرعی برای مدیریت تایمرها و کلیدهای شیشه‌ای
def get_timer_inline_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    timers_enabled = data_store.timer_settings.get("timers_enabled", True)
    inline_buttons_enabled = data_store.timer_settings.get("inline_buttons_enabled", True)
    
    timers_btn_text = "✅ تایمرها: فعال" if timers_enabled else "❌ تایمرها: غیرفعال"
    inline_buttons_btn_text = "✅ کلیدهای شیشه‌ای: فعال" if inline_buttons_enabled else "❌ کلیدهای شیشه‌ای: غیرفعال"
    
    timers_btn = types.KeyboardButton(timers_btn_text)
    inline_buttons_btn = types.KeyboardButton(inline_buttons_btn_text)
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    
    markup.add(timers_btn)
    markup.add(inline_buttons_btn)
    markup.add(back_btn)
    return markup

# منوی مدیریت ادمین‌ها
def get_admin_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    add_admin_btn = types.KeyboardButton("➕ افزودن ادمین")
    remove_admin_btn = types.KeyboardButton("➖ حذف ادمین")
    list_admins_btn = types.KeyboardButton("👀 لیست ادمین‌ها")
    permissions_btn = types.KeyboardButton("🔧 تنظیم دسترسی ادمین‌ها")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(add_admin_btn, remove_admin_btn)
    markup.add(list_admins_btn, permissions_btn)
    markup.add(back_btn)
    return markup

#منوی مدیا
def get_media_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    reset_btn = types.KeyboardButton("🗑️ ریست مدیاها")
    delete_btn = types.KeyboardButton("➖ حذف مدیاها")
    list_btn = types.KeyboardButton("👀 لیست مدیاها")
    delete_sent_btn = types.KeyboardButton("🗑️ حذف مدیاهای ارسال‌شده")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(reset_btn, delete_btn)
    markup.add(list_btn, delete_sent_btn)
    markup.add(back_btn)
    return markup

# تابع برای اجرای Helper
def run_helper():
    def get_folder_size(folder_path):
        """محاسبه حجم کل فایل‌های داخل پوشه به مگابایت"""
        total_size = 0
        try:
            if not os.path.exists(folder_path):
                return 0.0
            
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            logger.debug(f"فایل: {file} - حجم: {file_size / (1024 * 1024):.2f} MB")
                    except (OSError, IOError) as e:
                        logger.error(f"خطا در خواندن فایل {file_path}: {e}")
                        continue
            
            # تبدیل از بایت به مگابایت
            size_mb = total_size / (1024 * 1024)
            logger.info(f"حجم کل پوشه {folder_path}: {size_mb:.2f} MB ({total_size} bytes)")
            return size_mb
            
        except Exception as e:
            logger.error(f"خطا در محاسبه حجم پوشه {folder_path}: {e}")
            return 0.0
    
    def save_stats():
        """ذخیره آمار حجم پوشه medias در فایل JSON"""
        try:
            # محاسبه حجم پوشه medias
            medias_size = get_folder_size("medias")
            
            # آماده‌سازی دیتا برای ذخیره
            stats = {
                "medias_size_mb": round(medias_size, 2),
                "medias_size_bytes": int(medias_size * 1024 * 1024),
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "folder_path": "medias"
            }
            
            # ایجاد پوشه helper اگر وجود نداشته باشد
            os.makedirs("helper", exist_ok=True)
            
            # ذخیره در فایل JSON
            stats_file_path = os.path.join("helper", "stats.json")
            with open(stats_file_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=4)
            
            logger.info(f"✅ آمار حجم پوشه medias به‌روزرسانی شد: {stats['medias_size_mb']} MB")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره آمار: {e}")
            return False

    # اجرای فوری برای اولین بار
    logger.info("🚀 شروع Helper - محاسبه اولیه آمار...")
    save_stats()
    
    # تنظیم برنامه‌زمان‌بندی برای اجرای هر دقیقه
    schedule.every(1).minutes.do(save_stats)
    
    logger.info("⏰ Helper راه‌اندازی شد - آمار هر دقیقه به‌روزرسانی می‌شود")
    
    # حلقه اصلی
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Helper متوقف شد")
            break
        except Exception as e:
            logger.error(f"❌ خطا در Helper: {e}")
            time.sleep(5)  # صبر 5 ثانیه قبل از ادامه
            
def get_media_stats():
    """خواندن آمار مدیاها از فایل JSON تولید شده توسط helper"""
    try:
        stats_path = os.path.join("helper", "stats.json")
        if os.path.exists(stats_path):
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return stats.get("medias_size_mb", 0.0)
        return 0.0
    except Exception as e:
        logger.error(f"خطا در خواندن آمار از JSON: {e}")
        return 0.0

def get_latest_stats():
    stats_file = os.path.join("helper", "stats.json")
    
    # ابتدا تلاش برای خواندن از فایل stats.json
    if os.path.exists(stats_file):
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
                return stats.get("medias_size_mb", 0.0)
        except Exception as e:
            logger.error(f"خطا در خواندن stats.json: {e}")
            # در صورت خطا، به محاسبه مستقیم می‌رویم
    
    # محاسبه مستقیم حجم پوشه medias
    total_size = 0
    for root, _, files in os.walk("medias"):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                total_size += os.path.getsize(file_path)
            except Exception as e:
                logger.error(f"خطا در محاسبه حجم فایل {file_path}: {e}")
    
    return total_size / (1024 * 1024)  # تبدیل به مگابایت

# شروع ترد Helper
helper_thread = threading.Thread(target=run_helper, daemon=True)
helper_thread.start()

def get_admin_permissions_menu(admin_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    permissions = data_store.admin_permissions.get(str(admin_id), {
        "create_post": False,
        "signature_management": False,
        "variable_management": False,
        "default_values_management": False,
        "default_settings": False,
        "register_channel": False,
        "manage_timers": False,
        "options_management": False,
        "admin_management": False,
        "media_management": False
    })
    
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('create_post', False) else '❌'} ایجاد پست"),
        types.KeyboardButton(f"{'✅' if permissions.get('signature_management', False) else '❌'} مدیریت امضاها")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('variable_management', False) else '❌'} مدیریت متغیرها"),
        types.KeyboardButton(f"{'✅' if permissions.get('default_values_management', False) else '❌'} مقادیر پیش‌فرض")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('default_settings', False) else '❌'} تنظیمات پیش‌فرض"),
        types.KeyboardButton(f"{'✅' if permissions.get('register_channel', False) else '❌'} ثبت چنل")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('manage_timers', False) else '❌'} مدیریت تایمرها"),
        types.KeyboardButton(f"{'✅' if permissions.get('options_management', False) else '❌'} مدیریت اپشن‌ها")
    )
    markup.add(
        types.KeyboardButton(f"{'✅' if permissions.get('admin_management', False) else '❌'} مدیریت ادمین‌ها"),
        types.KeyboardButton(f"{'✅' if permissions.get('media_management', False) else '❌'} مدیریت مدیا")
    )
    markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
    return markup


# منوی اصلی برای دسترسی به امکانات بات
def get_main_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    if is_owner(user_id):  # اونر به همه گزینه‌ها دسترسی دارد
        create_post_btn = types.KeyboardButton("🆕 ایجاد پست")
        signature_btn = types.KeyboardButton("✍️ مدیریت امضاها")
        variable_btn = types.KeyboardButton("⚙️ مدیریت متغیرها")
        default_values_btn = types.KeyboardButton("📝 مدیریت مقادیر پیش‌فرض")
        default_settings_btn = types.KeyboardButton("🏠 تنظیمات پیش‌فرض")
        register_channel_btn = types.KeyboardButton("📢 ثبت چنل")
        manage_timers_btn = types.KeyboardButton("⏰ مدیریت تایمرها")
        options_mgmt_btn = types.KeyboardButton("✨ مدیریت اپشن‌ها")
        admin_management_btn = types.KeyboardButton("👤 مدیریت ادمین‌ها")
        media_management_btn = types.KeyboardButton("📁 مدیریت مدیا")  # دکمه جدید
        version_btn = types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}")
        markup.add(create_post_btn)
        markup.add(signature_btn, variable_btn)
        markup.add(default_values_btn)
        markup.add(default_settings_btn, options_mgmt_btn)
        markup.add(register_channel_btn, manage_timers_btn)
        markup.add(admin_management_btn, media_management_btn)  # اضافه کردن دکمه مدیا
        markup.add(version_btn)
    elif user_id in data_store.admins:  # ادمین‌ها فقط به گزینه‌های مجاز دسترسی دارند
        permissions = data_store.admin_permissions.get(str(user_id), {})
        if permissions.get("create_post", False):
            markup.add(types.KeyboardButton("🆕 ایجاد پست"))
        if permissions.get("signature_management", False):
            markup.add(types.KeyboardButton("✍️ مدیریت امضاها"))
        if permissions.get("variable_management", False):
            markup.add(types.KeyboardButton("⚙️ مدیریت متغیرها"))
        if permissions.get("default_values_management", False):
            markup.add(types.KeyboardButton("📝 مدیریت مقادیر پیش‌فرض"))
        if permissions.get("default_settings", False):
            markup.add(types.KeyboardButton("🏠 تنظیمات پیش‌فرض"))
        if permissions.get("register_channel", False):
            markup.add(types.KeyboardButton("📢 ثبت چنل"))
        if permissions.get("manage_timers", False):
            markup.add(types.KeyboardButton("⏰ مدیریت تایمرها"))
        if permissions.get("options_management", False):
            markup.add(types.KeyboardButton("✨ مدیریت اپشن‌ها"))
        if permissions.get("media_management", False):  # دسترسی جدید
            markup.add(types.KeyboardButton("📁 مدیریت مدیا"))
        markup.add(types.KeyboardButton(f"🤖 بات دستیار نسخه {BOT_VERSION}"))
        if not markup.keyboard:  # اگر هیچ دکمه‌ای اضافه نشده باشد
            bot.send_message(user_id, "⛔️ شما به هیچ گزینه‌ای دسترسی ندارید.")
            return None
    else:
        bot.send_message(user_id, "⛔️ این ربات فقط برای اونر و ادمین‌ها است.")
        return None
    
    return markup

# منوی بازگشت برای راحتی کاربر
def get_back_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(back_btn)
    return markup

# منوی انتخاب نحوه نمایش کلیدهای شیشه‌ای
def get_button_layout_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    inline_btn = types.KeyboardButton("📏 به کنار")
    stacked_btn = types.KeyboardButton("📐 به پایین")
    markup.add(inline_btn, stacked_btn)
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

# مدیریت ادمین‌ها
def handle_admin_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    logger.info(f"پردازش پیام در handle_admin_management، متن: '{text}'، حالت: {state}")
    
    if text == "➕ افزودن ادمین":
        logger.info(f"تغییر حالت به add_admin برای کاربر {user_id}")
        data_store.update_user_state(user_id, "add_admin")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=f"{status_text}\n\n🖊️ آیدی عددی کاربر را برای افزودن به ادمین‌ها وارد کنید:",
                reply_markup=get_back_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای افزودن ادمین: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ آیدی عددی کاربر را برای افزودن به ادمین‌ها وارد کنید:", reply_markup=get_back_menu())
            data_store.last_message_id[user_id] = msg.message_id
            
    elif text == "➖ حذف ادمین":
        logger.info(f"تغییر حالت به remove_admin برای کاربر {user_id}")
        if len(data_store.admins) <= 1:  # جلوگیری از حذف تنها ادمین (اونر)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ حداقل یک ادمین (اونر) باید باقی بماند.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ حداقل یک ادمین (اونر) باید باقی بماند.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for admin_id in data_store.admins:
            if admin_id != OWNER_ID:  # اونر قابل حذف نیست
                markup.add(types.KeyboardButton(str(admin_id)))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_admin")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=f"{status_text}\n\n🗑️ آیدی ادمینی که می‌خواهید حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ آیدی ادمینی که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "👀 لیست ادمین‌ها":
        logger.info(f"نمایش لیست ادمین‌ها برای کاربر {user_id}")
        admins_text = f"{status_text}\n\n👤 لیست ادمین‌ها:\n\n"
        if not data_store.admins:
            admins_text += "هیچ ادمینی وجود ندارد.\n"
        else:
            for admin_id in data_store.admins:
                admins_text += f"🔹 آیدی: {admin_id}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id, 0),
                text=admins_text,
                reply_markup=get_admin_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, admins_text, reply_markup=get_admin_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "admin_management")

    elif text == "🔧 تنظیم دسترسی ادمین‌ها":
            if not data_store.admins:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for admin_id in data_store.admins:
                markup.add(types.KeyboardButton(str(admin_id)))
            markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
            data_store.update_user_state(user_id, "select_admin_for_permissions")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        
    elif state == "select_admin_for_permissions":
        try:
            admin_id = int(text.strip())
            if admin_id == OWNER_ID:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ دسترسی‌های اونر قابل تغییر نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ دسترسی‌های اونر قابل تغییر نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            if admin_id in data_store.admins:
                data_store.update_user_state(user_id, "manage_admin_permissions", {"selected_admin_id": admin_id})
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:",
                        reply_markup=get_admin_permissions_menu(admin_id)
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:", reply_markup=get_admin_permissions_menu(admin_id))
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
        except ValueError:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "manage_admin_permissions":
        admin_id = user_state["data"].get("selected_admin_id")
        if not admin_id:
            logger.error(f"هیچ admin_id انتخاب‌شده‌ای برای کاربر {user_id} وجود ندارد.")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ خطا: هیچ ادمینی انتخاب نشده است.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا: هیچ ادمینی انتخاب نشده است.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "admin_management")
            return
    
        permissions = data_store.admin_permissions.get(str(admin_id), {
            "create_post": False,
            "signature_management": False,
            "variable_management": False,
            "default_values_management": False,
            "default_settings": False,
            "register_channel": False,
            "manage_timers": False,
            "options_management": False,
            "admin_management": False,
            "media_management": False  # اضافه کردن دسترسی مدیریت مدیا
        })
        
        permission_map = {
            "✅ ایجاد پست": ("create_post", True),
            "❌ ایجاد پست": ("create_post", False),
            "✅ مدیریت امضاها": ("signature_management", True),
            "❌ مدیریت امضاها": ("signature_management", False),
            "✅ مدیریت متغیرها": ("variable_management", True),
            "❌ مدیریت متغیرها": ("variable_management", False),
            "✅ مقادیر پیش‌فرض": ("default_values_management", True),
            "❌ مقادیر پیش‌فرض": ("default_values_management", False),
            "✅ تنظیمات پیش‌فرض": ("default_settings", True),
            "❌ تنظیمات پیش‌فرض": ("default_settings", False),
            "✅ ثبت چنل": ("register_channel", True),
            "❌ ثبت چنل": ("register_channel", False),
            "✅ مدیریت تایمرها": ("manage_timers", True),
            "❌ مدیریت تایمرها": ("manage_timers", False),
            "✅ مدیریت اپشن‌ها": ("options_management", True),
            "❌ مدیریت اپشن‌ها": ("options_management", False),
            "✅ مدیریت ادمین‌ها": ("admin_management", True),
            "❌ مدیریت ادمین‌ها": ("admin_management", False),
            "✅ مدیریت مدیا": ("media_management", True),  # اضافه کردن به permission_map
            "❌ مدیریت مدیا": ("media_management", False)   # اضافه کردن به permission_map
        }
        
        if text == "🔙 بازگشت به مدیریت ادمین":
            data_store.update_user_state(user_id, "admin_management")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n👤 مدیریت ادمین‌ها:",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        elif text in permission_map:
            perm_key, new_value = permission_map[text]
            permissions[perm_key] = new_value  # مستقیماً مقدار جدید را تنظیم می‌کنیم
            data_store.admin_permissions[str(admin_id)] = permissions
            data_store.save_data()
            action_text = "فعال شد" if new_value else "غیرفعال شد"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n✅ دسترسی '{perm_key}' {action_text}.\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:",
                    reply_markup=get_admin_permissions_menu(admin_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ دسترسی '{perm_key}' {action_text}.\n🔧 تنظیم دسترسی‌های ادمین {admin_id}:", reply_markup=get_admin_permissions_menu(admin_id))
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ گزینه نامعتبر. لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                    reply_markup=get_admin_permissions_menu(admin_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ گزینه نامعتبر. لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_admin_permissions_menu(admin_id))
                data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "add_admin":
        logger.info(f"تلاش برای افزودن ادمین با آیدی: '{text}'")
        try:
            admin_id = int(text.strip())
            logger.info(f"آیدی تبدیل‌شده: {admin_id}")
            if admin_id in data_store.admins:
                logger.warning(f"آیدی {admin_id} قبلاً در لیست ادمین‌ها وجود دارد.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این کاربر قبلاً ادمین است.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این کاربر قبلاً ادمین است.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            logger.info(f"لیست ادمین‌ها قبل از افزودن: {data_store.admins}")
            data_store.admins.append(admin_id)
            # مقداردهی اولیه دسترسی‌های ادمین جدید
            data_store.admin_permissions[str(admin_id)] = {
                "create_post": False,
                "signature_management": False,
                "variable_management": False,
                "default_values_management": False,
                "default_settings": False,
                "register_channel": False,
                "manage_timers": False,
                "options_management": False,
                "admin_management": False
            }
            logger.info(f"لیست ادمین‌ها بعد از افزودن: {data_store.admins}")
            if data_store.save_data():
                logger.info(f"آیدی {admin_id} با موفقیت به ادمین‌ها اضافه و ذخیره شد.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n✅ کاربر با آیدی {admin_id} به ادمین‌ها اضافه شد.\n👤 مدیریت ادمین‌ها:",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n✅ کاربر با آیدی {admin_id} به ادمین‌ها اضافه شد.\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                logger.error(f"خطا در ذخیره‌سازی آیدی {admin_id} در فایل admins.json")
                data_store.admins.remove(admin_id)
                del data_store.admin_permissions[str(admin_id)]
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی ادمین. لطفاً دوباره امتحان کنید.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی ادمین. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "admin_management")
        except ValueError as ve:
            logger.error(f"آیدی نامعتبر وارد شده: '{text}', خطا: {ve}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "remove_admin":
        logger.info(f"تلاش برای حذف ادمین با آیدی: '{text}'")
        try:
            admin_id = int(text.strip())
            logger.info(f"آیدی تبدیل‌شده: {admin_id}")
            if admin_id == OWNER_ID:
                logger.warning(f"تلاش برای حذف اونر با آیدی {admin_id}")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ اونر قابل حذف نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ اونر قابل حذف نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                data_store.update_user_state(user_id, "admin_management")
                return
            if admin_id in data_store.admins:
                logger.info(f"لیست ادمین‌ها قبل از حذف: {data_store.admins}")
                data_store.admins.remove(admin_id)
                logger.info(f"لیست ادمین‌ها بعد از حذف: {data_store.admins}")
                if data_store.save_data():
                    logger.info(f"آیدی {admin_id} با موفقیت از ادمین‌ها حذف شد.")
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id.get(user_id, 0),
                            text=f"{status_text}\n\n✅ ادمین با آیدی {admin_id} حذف شد.\n👤 مدیریت ادمین‌ها:",
                            reply_markup=get_admin_management_menu()
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n✅ ادمین با آیدی {admin_id} حذف شد.\n👤 مدیریت ادمین‌ها:", reply_markup=get_admin_management_menu())
                        data_store.last_message_id[user_id] = msg.message_id
                else:
                    logger.error(f"خطا در ذخیره‌سازی پس از حذف آیدی {admin_id}")
                    data_store.admins.append(admin_id)  # rollback در صورت خطا
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id.get(user_id, 0),
                            text=f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی پس از حذف ادمین. لطفاً دوباره امتحان کنید.",
                            reply_markup=get_admin_management_menu()
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ذخیره‌سازی پس از حذف ادمین. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                        data_store.last_message_id[user_id] = msg.message_id
            else:
                logger.warning(f"آیدی {admin_id} در لیست ادمین‌ها نیست.")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id, 0),
                        text=f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.",
                        reply_markup=get_admin_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این آیدی در لیست ادمین‌ها نیست.", reply_markup=get_admin_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "admin_management")
        except ValueError as ve:
            logger.error(f"آیدی نامعتبر برای حذف: '{text}', خطا: {ve}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً یک آیدی عددی معتبر وارد کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در حذف ادمین: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id, 0),
                    text=f"{status_text}\n\n⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره امتحان کنید.",
                    reply_markup=get_admin_management_menu()
                )
            except Exception as ex:
                logger.error(f"خطا در ویرایش پیام: {ex}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطای غیرمنتظره رخ داد. لطفاً دوباره امتحان کنید.", reply_markup=get_admin_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
                
# منوی مدیریت امضاها
def get_signature_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده امضاها")
    add_btn = types.KeyboardButton("➕ افزودن امضای جدید")
    delete_btn = types.KeyboardButton("🗑️ حذف امضا")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, add_btn)
    markup.add(delete_btn, back_btn)
    return markup

def handle_media_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if not (is_owner(user_id) or data_store.admin_permissions.get(str(user_id), {}).get("media_management", False)):
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n⛔️ دسترسی ندارید.", reply_markup=get_main_menu(user_id))
            data_store.last_message_id[user_id] = msg.message_id
        return
    
    if text == "🗑️ ریست مدیاها":
        try:
            shutil.rmtree("medias")
            os.makedirs("medias", exist_ok=True)
            data_store.media_metadata.clear()
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n✅ پوشه مدیا ریست شد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ پوشه مدیا ریست شد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطا در ریست پوشه مدیا: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ خطا در ریست پوشه مدیا: {str(e)}",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ریست پوشه مدیا: {str(e)}", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➖ حذف مدیاها":
        if not data_store.media_metadata:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ فایل مدیایی وجود ندارد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ فایل مدیایی وجود ندارد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for media_id in data_store.media_metadata.keys():
            markup.add(types.KeyboardButton(media_id))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "delete_media")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🗑️ شناسه فایل مدیا را برای حذف انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ شناسه فایل مدیا را برای حذف انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "👀 لیست مدیاها":
        media_text = f"{status_text}\n\n📁 لیست فایل‌های مدیا (حجم کل: {get_latest_stats():.2f} MB):\n\n"
        if not data_store.media_metadata:
            media_text += "هیچ فایل مدیایی وجود ندارد.\n"
        else:
            for idx, (media_id, metadata) in enumerate(data_store.media_metadata.items(), 1):
                file_type = metadata["type"]
                sent_status = "🕒 زمان‌بندی‌شده" if metadata["scheduled_time"] else ("✅ ارسال‌شده" if metadata["sent"] else "⏳ ارسال‌نشده")
                channel = metadata["channel"] if metadata["channel"] else "نامشخص"
                scheduled_time = metadata["scheduled_time"] if metadata["scheduled_time"] else "نامشخص"
                media_text += f"{idx}. نوع: {file_type.capitalize()}\nشناسه: {media_id}\nوضعیت: {sent_status}\nچنل: {channel}\nزمان‌بندی: {scheduled_time}\n\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=media_text,
                reply_markup=get_media_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, media_text, reply_markup=get_media_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "🗑️ حذف مدیاهای ارسال‌شده":
        sent_media = [media_id for media_id, metadata in data_store.media_metadata.items() if metadata["sent"]]
        if not sent_media:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ مدیای ارسال‌شده‌ای وجود ندارد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ مدیای ارسال‌شده‌ای وجود ندارد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("✅ بله"), types.KeyboardButton("❌ خیر"))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "delete_sent_media")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🗑️ آیا مطمئن هستید که می‌خواهید {len(sent_media)} فایل مدیای ارسال‌شده را حذف کنید؟",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ آیا مطمئن هستید که می‌خواهید {len(sent_media)} فایل مدیای ارسال‌شده را حذف کنید؟", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif state == "delete_media":
        if text in data_store.media_metadata:
            data_store.update_user_state(user_id, "confirm_delete_media", {"media_id": text})
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(types.KeyboardButton("✅ بله"), types.KeyboardButton("❌ خیر"))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n🗑️ آیا مطمئن هستید که می‌خواهید فایل با شناسه {text} را حذف کنید؟",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ آیا مطمئن هستید که می‌خواهید فایل با شناسه {text} را حذف کنید؟", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ شناسه فایل معتبر نیست.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ شناسه فایل معتبر نیست.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "media_management")
    
    elif state == "confirm_delete_media":
        media_id = user_state["data"]["media_id"]
        if text == "✅ بله":
            try:
                media_path = data_store.media_metadata[media_id]["path"]
                if os.path.exists(media_path):
                    os.remove(media_path)
                del data_store.media_metadata[media_id]
                data_store.save_data()
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id),
                        text=f"{status_text}\n\n✅ فایل با شناسه {media_id} حذف شد.",
                        reply_markup=get_media_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n✅ فایل با شناسه {media_id} حذف شد.", reply_markup=get_media_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            except Exception as e:
                logger.error(f"خطا در حذف فایل {media_id}: {e}")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id.get(user_id),
                        text=f"{status_text}\n\n⚠️ خطا در حذف فایل: {str(e)}",
                        reply_markup=get_media_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در حذف فایل: {str(e)}", reply_markup=get_media_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n❌ حذف فایل لغو شد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n❌ حذف فایل لغو شد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "media_management")
    
    elif state == "delete_sent_media":
        if text == "✅ بله":
            sent_media = [media_id for media_id, metadata in list(data_store.media_metadata.items()) if metadata["sent"]]
            deleted_count = 0
            for media_id in sent_media:
                try:
                    media_path = data_store.media_metadata[media_id]["path"]
                    if os.path.exists(media_path):
                        os.remove(media_path)
                    del data_store.media_metadata[media_id]
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"خطا در حذف فایل ارسال‌شده {media_id}: {e}")
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n✅ {deleted_count} فایل ارسال‌شده حذف شد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ {deleted_count} فایل ارسال‌شده حذف شد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n❌ حذف فایل‌های ارسال‌شده لغو شد.",
                    reply_markup=get_media_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n❌ حذف فایل‌های ارسال‌شده لغو شد.", reply_markup=get_media_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "media_management")

# دکمه‌های منو برای دسترسی سریع
MAIN_MENU_BUTTONS = [
    "🆕 ایجاد پست",
    "✍️ مدیریت امضاها",
    "⚙️ مدیریت متغیرها",
    "📝 مدیریت مقادیر پیش‌فرض",
    "🏠 تنظیمات پیش‌فرض",
    "📢 ثبت چنل",
    "⏰ مدیریت تایمرها",
    "✨ مدیریت اپشن‌ها",
    "👤 مدیریت ادمین‌ها",
    "📁 مدیریت مدیا",  # دکمه جدید
    f"🤖 بات دستیار نسخه {BOT_VERSION}",
    "🔙 بازگشت به منوی اصلی",
    "⏭️ رد کردن مرحله رسانه",
    "🆕 پست جدید",
    "⏭️ پایان ارسال رسانه",
    "📏 به کنار",
    "📐 به پایین",
    "⏰ زمان‌بندی پست",
    "✅ ادامه دادن",
    "✅ بله",
    "❌ خیر",
    "Bold",
    "Italic",
    "Code",
    "Strike",
    "Underline",
    "Spoiler",
    "BlockQuote",
    "Simple",
    "✅ تایمرها: فعال", "❌ تایمرها: غیرفعال",
    "✅ کلیدهای شیشه‌ای: فعال",
    "❌ کلیدهای شیشه‌ای: غیرفعال",
    "👀 مشاهده مقادیر پیش‌فرض",
    "➕ تنظیم مقدار پیش‌فرض",
    "➖ حذف مقدار پیش‌فرض",
    "➕ افزودن ادمین",
    "➖ حذف ادمین",
    "👀 لیست ادمین‌ها",
    "🔧 تنظیم دسترسی ادمین‌ها",
    "✅ ایجاد پست",
    "❌ ایجاد پست",
    "✅ مدیریت امضاها",
    "❌ مدیریت امضاها",
    "✅ مدیریت متغیرها",
    "❌ مدیریت متغیرها",
    "✅ مقادیر پیش‌فرض",
    "❌ مقادیر پیش‌فرض",
    "✅ تنظیمات پیش‌فرض",
    "❌ تنظیمات پیش‌فرض",
    "✅ ثبت چنل",
    "❌ ثبت چنل",
    "✅ مدیریت تایمرها",
    "❌ مدیریت تایمرها",
    "✅ مدیریت اپشن‌ها",
    "❌ مدیریت اپشن‌ها",
    "✅ مدیریت ادمین‌ها",
    "❌ مدیریت ادمین‌ها",
    "🔙 بازگشت به مدیریت ادمین",
    "🗑️ ریست مدیاها",
    "➖ حذف مدیاها",
    "👀 لیست مدیاها",
    "🗑️ حذف مدیاهای ارسال‌شده"
]

# هندلر استارت برای خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    if not (is_owner(user_id) or is_admin(user_id)):
        bot.send_message(user_id, "⛔️ این ربات فقط برای اونر و ادمین‌ها است.")
        return
    markup = get_main_menu(user_id)
    welcome_text = data_store.settings["default_welcome"].format(name=user_name)
    status_text = data_store.state_messages.get(None, "وضعیت نامشخص")
    
    # ذخیره آیدی پیام کاربر
    data_store.last_user_message_id[user_id] = message.message_id
    
    # پاک کردن پیام قبلی ربات (اگر وجود داشته باشه)
    if user_id in data_store.last_message_id:
        try:
            bot.delete_message(user_id, data_store.last_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام: {e}")
    
    # ارسال پیام جدید با وضعیت و ذخیره آیدی
    msg = bot.send_message(user_id, f"{status_text}\n\n{welcome_text}", reply_markup=markup)
    data_store.last_message_id[user_id] = msg.message_id
    
    # پاک کردن پیام کاربر
    try:
        bot.delete_message(user_id, data_store.last_user_message_id[user_id])
    except Exception as e:
        logger.error(f"خطا در حذف پیام کاربر: {e}")

# هندلر عکس برای دریافت تصاویر
@bot.message_handler(content_types=['photo', 'video'])
def handle_photo(message):
    user_id = message.from_user.id
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    data_store.last_user_message_id[user_id] = message.message_id
    
    if state == "post_with_signature_media":
        current_size_mb = get_media_stats()
        max_size_mb = 100  # فرض می‌کنیم حداکثر حجم مجاز 100 مگابایت است
        if current_size_mb >= max_size_mb:
            try:
                msg = bot.send_message(
                    user_id,
                    f"{status_text}\n\n⚠️ فضای ذخیره‌سازی پر شده است! ({current_size_mb:.2f} MB)",
                    reply_markup=get_back_menu()
                )
                data_store.last_message_id[user_id] = msg.message_id
            except Exception as e:
                logger.error(f"خطا در ارسال پیام: {e}")
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
            file_ext = '.jpg'
            media_type = 'photo'
        elif message.content_type == 'video':
            file_id = message.video.file_id
            file_ext = '.mp4'
            media_type = 'video'
        
        try:
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            downloaded_file = bot.download_file(file_path)
            unique_id = str(uuid.uuid4())
            media_path = os.path.join("medias", f"{unique_id}{file_ext}")
            with open(media_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            # ذخیره متادیتا
            data_store.media_metadata[unique_id] = {
                "path": media_path,
                "type": media_type,
                "sent": False,
                "channel": None,
                "scheduled_time": None
            }
            user_state["data"]["media_paths"] = user_state["data"].get("media_paths", []) + [{"path": media_path, "type": media_type}]
            logger.info(f"فایل {media_type} با آیدی {unique_id} ذخیره شد: {media_path}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ فایل {media_type} ذخیره شد (شناسه: {unique_id}).\nارسال فایل‌های بیشتر یا انتخاب یکی از گزینه‌ها:",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                        types.KeyboardButton("⏭️ پایان ارسال رسانه"),
                        types.KeyboardButton("🔙 بازگشت به منوی اصلی")
                    )
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(
                    user_id,
                    f"{status_text}\n\n✅ رسانه دریافت شد. برای ارسال رسانه دیگر ادامه دهید یا '⏭️ پایان ارسال رسانه' را انتخاب کنید.",
                    reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(
                        types.KeyboardButton("⏭️ پایان ارسال رسانه"),
                        types.KeyboardButton("🔙 بازگشت به منوی اصلی")
                    )
                )
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطا در پردازش رسانه: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ خطا در ذخیره رسانه. لطفاً دوباره امتحان کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(
                    user_id,
                    f"{status_text}\n\n⚠️ خطا در ذخیره رسانه. لطفاً دوباره امتحان کنید.",
                    reply_markup=get_back_menu()
                )
                data_store.last_message_id[user_id] = msg.message_id        
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return

        
# فرمت کردن پست با قابلیت‌های متنی تلگرام
def format_post_content(post_content, variables):
    formatted_content = post_content
    for var, value in variables.items():
        var_format = data_store.controls.get(var, {}).get("format", "Simple")
        if var_format == "Bold":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<b>{value}</b>")
        elif var_format == "BlockQuote":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<blockquote>{value}</blockquote>")
        elif var_format == "Italic":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<i>{value}</i>")
        elif var_format == "Code":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<code>{value}</code>")
        elif var_format == "Strike":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<s>{value}</s>")
        elif var_format == "Underline":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<u>{value}</u>")
        elif var_format == "Spoiler":
            formatted_content = formatted_content.replace(f"{{{var}}}", f"<tg-spoiler>{value}</tg-spoiler>")
        else:
            formatted_content = formatted_content.replace(f"{{{var}}}", value)
    return formatted_content

# پیش‌نمایش پست با کلیدهای شیشه‌ای و گزینه تایمر
def send_post_preview(user_id, post_content, media_paths=None, inline_buttons=None, row_width=4):
    markup_preview = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    continue_btn = types.KeyboardButton("✅ ادامه دادن")  # دکمه جدید
    schedule_btn = types.KeyboardButton("⏰ زمان‌بندی پست")
    new_post_btn = types.KeyboardButton("🆕 پست جدید")
    main_menu_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup_preview.add(continue_btn)  # اضافه کردن دکمه
    markup_preview.add(schedule_btn)
    markup_preview.add(new_post_btn)
    markup_preview.add(main_menu_btn)
    
    inline_keyboard = None
    if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
        inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
        for button in inline_buttons:
            inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
    
    # ارسال پیام نهایی (این پیام پاک نمی‌شه)
    user_state = data_store.get_user_state(user_id)
    status_text = data_store.state_messages.get(user_state["state"], "وضعیت نامشخص")
    
    if user_id in data_store.last_message_id:
        try:
            bot.delete_message(user_id, data_store.last_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام: {e}")
    
    if media_paths:
        for media in media_paths:
            try:
                with open(media["path"], "rb") as file:
                    if media["type"] == "photo":
                        bot.send_photo(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                    elif media["type"] == "video":
                        bot.send_video(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
            except Exception as e:
                logger.error(f"خطا در ارسال رسانه {media['path']}: {e}")
    else:
        msg = bot.send_message(user_id, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
        data_store.last_message_id[user_id] = msg.message_id
    
    # ارسال منوی نهایی
    try:
        bot.send_message(user_id, "📬 گزینه‌های پست:", reply_markup=markup_preview)
    except Exception as e:
        logger.error(f"خطا در ارسال منوی نهایی: {e}")

# پردازش پیام‌ها
@bot.message_handler(func=lambda message: True)
def process_message(message):
    user_id = message.from_user.id
    text = message.text
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    logger.info(f"پیام دریافت‌شده از {user_id}: '{text}'، حالت: {state}")
    # ذخیره آیدی پیام کاربر
    data_store.last_user_message_id[user_id] = message.message_id
    
    if text in MAIN_MENU_BUTTONS:
            logger.info(f"دکمه منو شناسایی شد: {text}")
            if process_main_menu_button(user_id, text):
                # پاک کردن پیام کاربر
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return

    if state in ["admin_management", "add_admin", "remove_admin", "select_admin_for_permissions", "manage_admin_permissions"]:
        logger.info(f"هدایت پیام به handle_admin_management، حالت: {state}")
        handle_admin_management(user_id, text)
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return

        if state == "admin_management":
            handle_admin_management(user_id, text)
            # پاک کردن پیام کاربر
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        
    if state == "default_values_management":
        logger.info(f"هدایت پیام به handle_default_values_management، حالت: {state}")
        handle_default_values_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
        
    if state == "timer_inline_management":
        logger.info(f"پردازش پیام در timer_inline_management، متن: {text}")
        timers_enabled = data_store.timer_settings.get("timers_enabled", True)
        inline_buttons_enabled = data_store.timer_settings.get("inline_buttons_enabled", True)
        timers_status = "✅ فعال" if timers_enabled else "❌ غیرفعال"
        buttons_status = "✅ فعال" if inline_buttons_enabled else "❌ غیرفعال"
        status_message = (
            f"{status_text}\n\n"
            f"⏰ وضعیت تایمرها: {timers_status}\n"
            f"🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n"
            f"✨ مدیریت اپشن‌ها:"
        )
        
        timers_btn_text = "✅ تایمرها: فعال" if timers_enabled else "❌ تایمرها: غیرفعال"
        inline_buttons_btn_text = "✅ کلیدهای شیشه‌ای: فعال" if inline_buttons_enabled else "❌ کلیدهای شیشه‌ای: غیرفعال"
        
        if text == timers_btn_text:
            data_store.timer_settings["timers_enabled"] = not timers_enabled
            data_store.save_data()
            new_timers_status = "✅ فعال" if not timers_enabled else "❌ غیرفعال"
            action_text = "فعال شدند" if not timers_enabled else "غیرفعال شدند"
            try:
                bot.edit_message_text(
                    chat_id=user_id, 
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⏰ تایمرها {action_text}.\n⏰ وضعیت تایمرها: {new_timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n✨ مدیریت اپشن‌ها:",
                    reply_markup=get_timer_inline_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⏰ تایمرها {action_text}.\n⏰ وضعیت تایمرها: {new_timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {buttons_status}\n\n✨ مدیریت اپشن‌ها:", reply_markup=get_timer_inline_menu())
                data_store.last_message_id[user_id] = msg.message_id
        elif text == inline_buttons_btn_text:
            data_store.timer_settings["inline_buttons_enabled"] = not inline_buttons_enabled
            data_store.save_data()
            new_buttons_status = "✅ فعال" if not inline_buttons_enabled else "❌ غیرفعال"
            action_text = "فعال شدند" if not inline_buttons_enabled else "غیرفعال شدند"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 کلیدهای شیشه‌ای {action_text}.\n⏰ وضعیت تایمرها: {timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {new_buttons_status}\n\n✨ مدیریت اپشن‌ها:",
                    reply_markup=get_timer_inline_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 کلیدهای شیشه‌ای {action_text}.\n⏰ وضعیت تایمرها: {timers_status}\n🔗 وضعیت کلیدهای شیشه‌ای: {new_buttons_status}\n\n✨ مدیریت اپشن‌ها:", reply_markup=get_timer_inline_menu())
                data_store.last_message_id[user_id] = msg.message_id
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state is None:
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🔍 لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🔍 لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_main_menu(user_id))
            data_store.last_message_id[user_id] = msg.message_id
        
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "signature_management":
        handle_signature_management(user_id, text)
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "select_signature":
        if text in data_store.signatures:
            data_store.update_user_state(user_id, "post_with_signature_media", {"signature_name": text})
            markup = get_back_menu()
            markup.add(types.KeyboardButton("⏭️ رد کردن مرحله رسانه"))
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📸 عکس یا ویدیو ارسال کنید (یا دکمه زیر برای رد کردن):",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📸 عکس یا ویدیو ارسال کنید (یا دکمه زیر برای رد کردن):", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "post_with_signature_media":
        if text == "⏭️ پایان ارسال رسانه" or text == "⏭️ رد کردن مرحله رسانه":
            media_paths = user_state["data"].get("media_paths", None)
            data_store.update_user_state(user_id, "post_with_signature_values", {"media_paths": media_paths, "current_var_index": 0})
            sig_name = user_state["data"]["signature_name"]
            signature = data_store.signatures[sig_name]
            variables = signature["variables"]
            
            # مقداردهی اولیه برای متغیرها با استفاده از مقادیر پیش‌فرض
            user_state["data"]["temp_post_content"] = signature["template"]
            variables_without_default = []
            for var in variables:
                if var in data_store.default_values:
                    user_state["data"][var] = data_store.default_values[var]
                else:
                    user_state["data"][var] = f"[{var} وارد نشده]"
                    variables_without_default.append(var)
            
            data_store.update_user_state(user_id, "post_with_signature_values", {
                "media_paths": media_paths,
                "current_var_index": 0,
                "variables_without_default": variables_without_default
            })
            
            if variables_without_default:
                # نمایش اولیه پست
                temp_content = user_state["data"]["temp_post_content"]
                for var in variables:
                    temp_content = temp_content.replace(f"{{{var}}}", user_state["data"][var])
                display_text = f"{status_text}\n\n📝 در حال ساخت پست:\n\n{temp_content}\n\nـــــــــــــــــــــ\n🖊️ مقدار {variables_without_default[0]} را وارد کنید:"
                
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=display_text,
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, display_text, reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                post_content = signature["template"]
                for var in variables:
                    post_content = post_content.replace(f"{{{var}}}", user_state["data"][var])
                data_store.update_user_state(user_id, "add_inline_buttons", {"post_content": post_content, "media_paths": media_paths})
                markup = get_back_menu()
                markup.add(types.KeyboardButton("✅ پایان افزودن کلیدها"))
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n🔗 کلید شیشه‌ای اضافه کنید (نام کلید و لینک را به‌صورت 'نام|لینک' وارد کنید) یا 'پایان افزودن کلیدها' را بزنید:",
                        reply_markup=markup
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n🔗 کلید شیشه‌ای اضافه کنید (نام کلید و لینک را به‌صورت 'نام|لینک' وارد کنید) یا 'پایان افزودن کلیدها' را بزنید:", reply_markup=markup)
                    data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "post_with_signature_values":
        sig_name = user_state["data"]["signature_name"]
        current_index = user_state["data"].get("current_var_index", 0)
        signature = data_store.signatures[sig_name]
        variables_without_default = user_state["data"].get("variables_without_default", signature["variables"])
        
        var_name = variables_without_default[current_index]
        user_state["data"][var_name] = text
        current_index += 1
        
        if current_index < len(variables_without_default):
            data_store.update_user_state(user_id, None, {"current_var_index": current_index})
            
            # به‌روزرسانی محتوای پست
            temp_content = user_state["data"]["temp_post_content"]
            for var in signature["variables"]:
                temp_content = temp_content.replace(f"{{{var}}}", user_state["data"][var])
            display_text = f"{status_text}\n\n📝 در حال ساخت پست:\n\n{temp_content}\n\nـــــــــــــــــــــ\n🖊️ مقدار {variables_without_default[current_index]} را وارد کنید:"
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=display_text,
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, display_text, reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            variables_dict = {var: user_state["data"][var] for var in signature["variables"]}
            result = format_post_content(signature["template"], variables_dict)
            
            media_paths = user_state["data"].get("media_paths")
            data_store.update_user_state(user_id, "ask_for_inline_buttons", {"post_content": result, "media_paths": media_paths, "inline_buttons": []})
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(types.KeyboardButton("✅ بله"), types.KeyboardButton("❌ خیر"))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 آیا می‌خواهید کلید شیشه‌ای اضافه کنید؟",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 آیا می‌خواهید کلید شیشه‌ای اضافه کنید؟", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "ask_for_inline_buttons":
        if text == "✅ بله":
            data_store.update_user_state(user_id, "add_inline_button_name", {"inline_buttons": user_state["data"].get("inline_buttons", []), "row_width": 4})
            markup = get_back_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📝 نام کلید شیشه‌ای را وارد کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📝 نام کلید شیشه‌ای را وارد کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "❌ خیر":
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            data_store.update_user_state(user_id, "post_with_signature_ready", {
                "post_content": post_content,
                "media_paths": media_paths,
                "inline_buttons": inline_buttons,
                "row_width": 4
            })
            send_post_preview(user_id, post_content, media_paths, inline_buttons, row_width=4)
           
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "add_inline_button_name":
        button_text = text.strip()
        if button_text:
            data_store.update_user_state(user_id, "add_inline_button_url", {
                "inline_buttons": user_state["data"].get("inline_buttons", []),
                "row_width": user_state["data"].get("row_width", 4),
                "button_text": button_text
            })
            markup = get_back_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🔗 لینک کلید '{button_text}' را وارد کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🔗 لینک کلید '{button_text}' را وارد کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ نام کلید نمی‌تواند خالی باشد! لطفاً یک نام وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ نام کلید نمی‌تواند خالی باشد! لطفاً یک نام وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
        
    if state == "add_inline_button_url":
        button_url = text.strip()
        if button_url:
            button_text = user_state["data"].get("button_text", "")
            inline_buttons = user_state["data"].get("inline_buttons", [])
            inline_buttons.append({"text": button_text, "url": button_url})
            
            data_store.update_user_state(user_id, "ask_continue_adding_buttons", {"inline_buttons": inline_buttons})
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            markup.add(types.KeyboardButton("✅ ادامه دادن"), types.KeyboardButton("❌ خیر"))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ کلید '{button_text}' اضافه شد. آیا می‌خواهید کلید دیگری اضافه کنید؟",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ کلید '{button_text}' اضافه شد. آیا می‌خواهید کلید دیگری اضافه کنید؟", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ لینک نمی‌تواند خالی باشد! لطفاً یک لینک معتبر وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لینک نمی‌تواند خالی باشد! لطفاً یک لینک معتبر وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "ask_continue_adding_buttons":
        if text == "✅ ادامه دادن":
            data_store.update_user_state(user_id, "select_button_position")
            markup = get_button_layout_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📏 نحوه نمایش کلید شیشه‌ای بعدی را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📏 نحوه نمایش کلید شیشه‌ای بعدی را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "❌ خیر":
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            data_store.update_user_state(user_id, "post_with_signature_ready", {
                "post_content": post_content,
                "media_paths": media_paths,
                "inline_buttons": inline_buttons,
                "row_width": 4
            })
            send_post_preview(user_id, post_content, media_paths, inline_buttons, row_width=4)
           
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "select_button_position":
        row_width = 4  # کنار هم (به صورت پیش‌فرض)
        if text == "📏 به کنار":
            row_width = 4  # کنار هم
        elif text == "📐 به پایین":
            row_width = 1  # زیر هم
        
        data_store.update_user_state(user_id, "add_inline_button_name", {
            "inline_buttons": user_state["data"].get("inline_buttons", []),
            "row_width": row_width
        })
        markup = get_back_menu()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n📝 نام کلید شیشه‌ای بعدی را وارد کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n📝 نام کلید شیشه‌ای بعدی را وارد کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return

    if state == "post_with_signature_ready":
        if text == "✅ ادامه دادن":
            if not data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            
            # نمایش لیست چنل‌ها برای انتخاب
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for channel in data_store.channels:
                markup.add(types.KeyboardButton(channel))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            data_store.update_user_state(user_id, "select_channel_for_post", {
                "post_content": user_state["data"].get("post_content", ""),
                "media_paths": user_state["data"].get("media_paths", []),
                "inline_buttons": user_state["data"].get("inline_buttons", []),
                "row_width": user_state["data"].get("row_width", 4)
            })
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n📢 چنل مقصد را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n📢 چنل مقصد را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
    
    if state == "select_channel_for_post":
        if text in data_store.channels:
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            row_width = user_state["data"].get("row_width", 4)
            channel = text
            
            inline_keyboard = None
            if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
                inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
                for button in inline_buttons:
                    inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
            
            if media_paths:
                for media in media_paths:
                    try:
                        with open(media["path"], "rb") as file:
                            if media["type"] == "photo":
                                bot.send_photo(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                            elif media["type"] == "video":
                                bot.send_video(user_id, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"خطا در ارسال رسانه: {e}")
                        try:
                            bot.edit_message_text(
                                chat_id=user_id,
                                message_id=data_store.last_message_id[user_id],
                                text=f"{status_text}\n\n⚠️ خطا در ارسال رسانه: {e}",
                                reply_markup=get_main_menu(user_id)
                            )
                        except Exception as e:
                            logger.error(f"خطا در ویرایش پیام: {e}")
                            msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ارسال رسانه: {e}", reply_markup=get_main_menu(user_id))
                            data_store.last_message_id[user_id] = msg.message_id
                        data_store.reset_user_state(user_id)
                        try:
                            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                        except Exception as e:
                            logger.error(f"خطا در حذف پیام کاربر: {e}")
                        return
            else:
                try:
                    bot.send_message(channel, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                except Exception as e:
                    logger.error(f"خطا در ارسال پیام: {e}")
                    try:
                        bot.edit_message_text(
                            chat_id=user_id,
                            message_id=data_store.last_message_id[user_id],
                            text=f"{status_text}\n\n⚠️ خطا در ارسال پیام: {e}",
                            reply_markup=get_main_menu(user_id)
                        )
                    except Exception as e:
                        logger.error(f"خطا در ویرایش پیام: {e}")
                        msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در ارسال پیام: {e}", reply_markup=get_main_menu(user_id))
                        data_store.last_message_id[user_id] = msg.message_id
                    data_store.reset_user_state(user_id)
                    try:
                        bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                    except Exception as e:
                        logger.error(f"خطا در حذف پیام کاربر: {e}")
                    return
            
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ پست با موفقیت به {channel} ارسال شد.\n🏠 منوی اصلی:",
                    reply_markup=get_main_menu(user_id)
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ پست با موفقیت به {channel} ارسال شد.\n🏠 منوی اصلی:", reply_markup=get_main_menu(user_id))
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return

    if state == "post_with_signature_ready":
        if text == "🆕 پست جدید":
            data_store.reset_user_state(user_id)
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            for sig_name in data_store.signatures.keys():
                markup.add(types.KeyboardButton(sig_name))
            markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
            data_store.update_user_state(user_id, "select_signature")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
        elif text == "⏰ زمان‌بندی پست":
            if not data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ چنلی ثبت نشده است. ابتدا یک چنل ثبت کنید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
            else:
                channels_list = "\n".join(data_store.channels)
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                data_store.update_user_state(user_id, "schedule_post")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n📢 چنل‌های ثبت‌شده:\n{channels_list}\n\n⏰ زمان پیشنهادی: <code>{one_minute_later}</code>\nلطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>):",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n📢 چنل‌های ثبت‌شده:\n{channels_list}\n\n⏰ زمان پیشنهادی: <code>{one_minute_later}</code>\nلطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>):", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "schedule_post":
        try:
            parts = text.split()
            if len(parts) < 3:
                tehran_tz = pytz.timezone('Asia/Tehran')
                one_minute_later = (datetime.now(tehran_tz) + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ لطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>)",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ لطفاً چنل و زمان آینده را وارد کنید (مثال: <code>@channel {one_minute_later}</code>)", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            
            channel = parts[0]
            time_str = " ".join(parts[1:])
            scheduled_time = datetime.strptime(time_str, "%Y/%m/%d %H:%M")
            
            if scheduled_time <= datetime.now():
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ فقط زمان آینده قابل قبول است! زمان پیشنهادی: <code>{one_minute_later}</code>",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ فقط زمان آینده قابل قبول است! زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            
            if channel not in data_store.channels:
                one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ این چنل ثبت نشده است. ابتدا چنل را ثبت کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                        reply_markup=get_back_menu(),
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این چنل ثبت نشده است. ابتدا چنل را ثبت کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            
            post_content = user_state["data"].get("post_content", "")
            media_paths = user_state["data"].get("media_paths", [])
            inline_buttons = user_state["data"].get("inline_buttons", [])
            row_width = user_state["data"].get("row_width", 4)
            
            job_id = str(uuid.uuid4())
            data_store.scheduled_posts.append({
                "job_id": job_id,
                "channel": channel,
                "time": time_str,
                "post_content": post_content,
                "media_paths": media_paths if media_paths else [],
                "inline_buttons": inline_buttons,
                "row_width": row_width
            })
            data_store.save_data()
            
            schedule.every().day.at(scheduled_time.strftime("%H:%M")).do(send_scheduled_post, job_id=job_id).tag(job_id)
            markup = get_main_menu(user_id)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ پست برای ارسال به {channel} در زمان {time_str} زمان‌بندی شد.\n منوی اصلی:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ پست برای ارسال به {channel} در زمان {time_str} زمان‌بندی شد.\n منوی اصلی:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
        except ValueError:
            one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ فرمت زمان اشتباه است! از yyyy/mm/dd hh:mm استفاده کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                    reply_markup=get_back_menu(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ فرمت زمان اشتباه است! از yyyy/mm/dd hh:mm استفاده کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
        except Exception as e:
            logger.error(f"خطا در تنظیم تایمر: {e}")
            one_minute_later = (datetime.now() + timedelta(minutes=1)).strftime("%Y/%m/%d %H:%M")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ یه مشکلی پیش اومد. دوباره امتحان کنید. زمان پیشنهادی: <code>{one_minute_later}</code>",
                    reply_markup=get_back_menu(),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ یه مشکلی پیش اومد. دوباره امتحان کنید. زمان پیشنهادی: <code>{one_minute_later}</code>", reply_markup=get_back_menu(), parse_mode="HTML")
                data_store.last_message_id[user_id] = msg.message_id
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return  
  
    if state == "new_signature_name":
        if text in data_store.signatures:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ این نام امضا قبلاً وجود دارد.\n✏️ نام دیگری وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این نام امضا قبلاً وجود دارد.\n✏️ نام دیگری وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            data_store.update_user_state(user_id, "new_signature_template", {"new_sig_name": text})
            example = "[5253877736207821121] {name}\n[5256160369591723706] {description}\n[5253864872780769235] {version}"
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🖊️ قالب امضا را وارد کنید.\nمثال:\n{example}",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ قالب امضا را وارد کنید.\nمثال:\n{example}", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "new_signature_template":
        template = text
        sig_name = user_state["data"]["new_sig_name"]
        variables = re.findall(r'\{(\w+)\}', template)
        
        if not variables:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ حداقل یک متغیر با فرمت {{variable_name}} وارد کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ حداقل یک متغیر با فرمت {{variable_name}} وارد کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        
        undefined_vars = [var for var in variables if var not in data_store.controls]
        if undefined_vars:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ متغیرهای زیر تعریف نشده‌اند: {', '.join(undefined_vars)}\nلطفاً ابتدا این متغیرها را در بخش 'مدیریت متغیرها' تعریف کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیرهای زیر تعریف نشده‌اند: {', '.join(undefined_vars)}\nلطفاً ابتدا این متغیرها را در بخش 'مدیریت متغیرها' تعریف کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        
        data_store.signatures[sig_name] = {
            "template": template,
            "variables": variables
        }
        data_store.save_data()
        
        markup = get_main_menu(user_id)
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ امضای جدید '{sig_name}' ایجاد شد.\n🏠 منوی اصلی:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ امضای جدید '{sig_name}' ایجاد شد.\n🏠 منوی اصلی:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        
        data_store.reset_user_state(user_id)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "delete_signature":
        if text in data_store.signatures:
            del data_store.signatures[text]
            data_store.save_data()
            markup = get_signature_management_menu()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ امضای '{text}' حذف شد.\n✍️ مدیریت امضاها:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ امضای '{text}' حذف شد.\n✍️ مدیریت امضاها:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "signature_management")
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ امضای انتخاب‌شده وجود ندارد.",
                    reply_markup=get_signature_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ امضای انتخاب‌شده وجود ندارد.", reply_markup=get_signature_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "admin_management":
        status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⛔️ قابلیت مدیریت ادمین‌ها حذف شده است.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ قابلیت مدیریت ادمین‌ها حذف شده است.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        data_store.update_user_state(user_id, "main_menu")
        return
    
    if state == "variable_management":
        handle_variable_management(user_id, text)
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "set_default_settings":
        data_store.settings["default_welcome"] = text
        data_store.save_data()
        markup = get_main_menu(user_id)
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ متن پیش‌فرض تنظیم شد.\n🏠 منوی اصلی:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ متن پیش‌فرض تنظیم شد.\n🏠 منوی اصلی:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
        data_store.reset_user_state(user_id)
        # پاک کردن پیام کاربر
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    if state == "register_channel":
        channel_name = text.strip()
        if not channel_name.startswith('@'):
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ آیدی چنل باید با @ شروع شود (مثال: @channelname).",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ آیدی چنل باید با @ شروع شود (مثال: @channelname).", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        required_permissions = [
            ("ارسال پیام", False),
            ("مدیریت پیام‌ها", False)
        ]
        try:
            chat = bot.get_chat(channel_name)
            bot_member = bot.get_chat_member(channel_name, bot.get_me().id)
            
            # بررسی نوع عضویت
            if bot_member.status not in ['administrator', 'creator']:
                required_permissions = [
                    ("ارسال پیام", False),
                    ("ویرایش پیام‌های دیگران", False),
                    ("حذف پیام‌های دیگران", False),
                    ("ادمین کردن کاربران", False)
                ]
            else:
                # بررسی دسترسی‌های واقعی برای ادمین
                can_post = bot_member.can_post_messages if hasattr(bot_member, 'can_post_messages') else True
                can_edit = bot_member.can_edit_messages if hasattr(bot_member, 'can_edit_messages') else False
                can_delete = bot_member.can_delete_messages if hasattr(bot_member, 'can_delete_messages') else False
                can_promote = bot_member.can_promote_members if hasattr(bot_member, 'can_promote_members') else False
                
                required_permissions = [
                    ("ارسال پیام", can_post),
                    ("ویرایش پیام‌های دیگران", can_edit),
                    ("حذف پیام‌های دیگران", can_delete),
                    ("ادمین کردن کاربران", can_promote)
                ]
            
            if not all(granted for _, granted in required_permissions):
                permissions_text = "\n".join(
                    f"{name}: {'✅' if granted else '❌'}" for name, granted in required_permissions
                )
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ هیچ قابلیتی بهم ندادی!\n{permissions_text}\nلطفاً دسترسی‌های لازم را بدهید.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ قابلیتی بهم ندادی!\n{permissions_text}\nلطفاً دسترسی‌های لازم را بدهید.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            if channel_name in data_store.channels:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ این چنل قبلاً ثبت شده است.",
                        reply_markup=get_back_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این چنل قبلاً ثبت شده است.", reply_markup=get_back_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                try:
                    bot.delete_message(user_id, data_store.last_user_message_id[user_id])
                except Exception as e:
                    logger.error(f"خطا در حذف پیام کاربر: {e}")
                return
            data_store.channels.append(channel_name)
            data_store.save_data()
            permissions_text = "\n".join(
                f"{name}: ✅" for name, _ in required_permissions
            )
            markup = get_main_menu(user_id)
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n{permissions_text}\n✅ چنل {channel_name} چک شد و به حافظه اضافه شد.\n🏠 منوی اصلی:",
                    reply_markup=markup
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n{permissions_text}\n✅ چنل {channel_name} چک شد و به حافظه اضافه شد.\n🏠 منوی اصلی:", reply_markup=markup)
                data_store.last_message_id[user_id] = msg.message_id
            data_store.reset_user_state(user_id)
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return
        except Exception as e:
            logger.error(f"خطا در بررسی دسترسی چنل {channel_name}: {e}")
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ خطا در بررسی چنل {channel_name}. لطفاً مطمئن شوید که ربات به چنل دسترسی دارد و دوباره امتحان کنید.",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ خطا در بررسی چنل {channel_name}. لطفاً مطمئن شوید که ربات به چنل دسترسی دارد و دوباره امتحان کنید.", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
            return

# ارسال پست زمان‌بندی‌شده
def send_scheduled_post(job_id):
    if not data_store.timer_settings.get("timers_enabled", True):
        logger.info(f"تایمر {job_id} اجرا نشد چون تایمرها غیرفعال هستند.")
        return
    for post in data_store.scheduled_posts:
        if post["job_id"] == job_id:
            channel = post["channel"]
            post_content = post["post_content"]
            media_paths = post["media_paths"]
            inline_buttons = post["inline_buttons"]
            row_width = post.get("row_width", 4)
            
            inline_keyboard = None
            if data_store.timer_settings.get("inline_buttons_enabled", True) and inline_buttons:
                inline_keyboard = types.InlineKeyboardMarkup(row_width=row_width)
                for button in inline_buttons:
                    inline_keyboard.add(types.InlineKeyboardButton(button["text"], url=button["url"]))
            
            if media_paths:
                for media in media_paths:
                    try:
                        media_path = os.path.join("medias", os.path.basename(media["path"]))
                        if not os.path.exists(media_path):
                            logger.error(f"فایل رسانه {media_path} یافت نشد.")
                            continue
                        # به‌روزرسانی متادیتا
                        media_id = os.path.splitext(os.path.basename(media_path))[0]
                        if media_id in data_store.media_metadata:
                            data_store.media_metadata[media_id]["sent"] = True
                            data_store.media_metadata[media_id]["channel"] = channel
                            data_store.save_data()
                        with open(media_path, "rb") as file:
                            if media["type"] == "photo":
                                bot.send_photo(channel, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                            elif media["type"] == "video":
                                bot.send_video(channel, file, caption=post_content, reply_markup=inline_keyboard, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"خطا در ارسال رسانه زمان‌بندی‌شده {media_path}: {e}")
            else:
                bot.send_message(channel, post_content, reply_markup=inline_keyboard, parse_mode="HTML")
            
            data_store.scheduled_posts.remove(post)
            data_store.save_data()
            schedule.clear(job_id)
            break

# پردازش دکمه‌های منو
def process_main_menu_button(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if text == "🔙 بازگشت به منوی اصلی":
        data_store.reset_user_state(user_id)
        markup = get_main_menu(user_id)
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🏠 بازگشت به منوی اصلی:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
            
    elif text == "✨ مدیریت اپشن‌ها":
        data_store.update_user_state(user_id, "timer_inline_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n✨ مدیریت اپشن‌ها:",
            reply_markup=get_timer_inline_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "👤 مدیریت ادمین‌ها":
        if not is_owner(user_id):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ فقط اونر به این بخش دسترسی دارد.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "admin_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n👤 مدیریت ادمین‌ها:",
            reply_markup=get_admin_management_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "🆕 ایجاد پست":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sig_name in data_store.signatures.keys():
            markup.add(types.KeyboardButton(sig_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "select_signature")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ امضای مورد نظر را انتخاب کنید:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "📝 مدیریت مقادیر پیش‌فرض":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_default_values_management_menu()
        data_store.update_user_state(user_id, "default_values_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n📝 مدیریت مقادیر پیش‌فرض:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "✍️ مدیریت امضاها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_signature_management_menu()
        data_store.update_user_state(user_id, "signature_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n✍️ مدیریت امضاها:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "⚙️ مدیریت متغیرها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = get_variable_management_menu()
        data_store.update_user_state(user_id, "variable_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n⚙️ مدیریت متغیرها:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "🏠 تنظیمات پیش‌فرض":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "set_default_settings")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ متن پیش‌فرض خوش‌آمدگویی را وارد کنید:",
            reply_markup=get_back_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "📢 ثبت چنل":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "register_channel")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🖊️ آیدی چنل را وارد کنید (مثال: @channelname):",
            reply_markup=get_back_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "⏰ مدیریت تایمرها":
        if not (is_owner(user_id) or is_admin(user_id)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        if not data_store.scheduled_posts:
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n📅 هیچ تایمری تنظیم نشده است.\n🏠 منوی اصلی:",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        timers_text = f"{status_text}\n\n⏰ تایمرهای تنظیم‌شده:\n\n"
        for post in data_store.scheduled_posts:
            timers_text += f"🆔 {post['job_id']}\nچنل: {post['channel']}\nزمان: {post['time']}\n\n"
        inline_keyboard = types.InlineKeyboardMarkup()
        for post in data_store.scheduled_posts:
            inline_keyboard.add(types.InlineKeyboardButton(f"حذف تایمر {post['job_id']}", callback_data=f"delete_timer_{post['job_id']}"))
        msg = bot.send_message(
            user_id,
            timers_text,
            reply_markup=inline_keyboard
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
        
    elif text == f"🤖 بات دستیار نسخه {BOT_VERSION}":
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🤖 این بات دستیار نسخه {BOT_VERSION} است.\nتوسعه توسط @py_zon",
            reply_markup=get_main_menu(user_id)
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    
    elif text == "🔧 تنظیم دسترسی ادمین‌ها":
        if not is_owner(user_id):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ فقط اونر به این بخش دسترسی دارد.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        if not data_store.admins:
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ هیچ ادمینی وجود ندارد.",
                reply_markup=get_admin_management_menu()
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for admin_id in data_store.admins:
            markup.add(types.KeyboardButton(str(admin_id)))
        markup.add(types.KeyboardButton("🔙 بازگشت به مدیریت ادمین"))
        data_store.update_user_state(user_id, "select_admin_for_permissions")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n🔧 آیدی ادمینی که می‌خواهید دسترسی‌هایش را تنظیم کنید را انتخاب کنید:",
            reply_markup=markup
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    elif text == "📁 مدیریت مدیا":
        if not (is_owner(user_id) or data_store.admin_permissions.get(str(user_id), {}).get("media_management", False)):
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
            return True
        data_store.update_user_state(user_id, "media_management")
        msg = bot.send_message(
            user_id,
            f"{status_text}\n\n📁 مدیریت فایل‌های مدیا:",
            reply_markup=get_media_management_menu()
        )
        data_store.last_message_id[user_id] = msg.message_id
        return True
    return False

# مدیریت امضاها
def handle_signature_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if text == "👀 مشاهده امضاها":
        signatures_text = f"{status_text}\n\n📋 لیست امضاها:\n\n"
        if not data_store.signatures:
            signatures_text += "هیچ امضایی وجود ندارد.\n"
        else:
            for sig_name, sig_data in data_store.signatures.items():
                template = sig_data["template"]
                variables = sig_data["variables"]
                preview_content = template
                for var in variables:
                    var_format = data_store.controls.get(var, {}).get("format", "Simple")
                    if var_format == "Bold":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<b>[{var}]</b>")
                    elif var_format == "Italic":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<i>[{var}]</i>")
                    elif var_format == "Code":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<code>[{var}]</code>")
                    elif var_format == "Strike":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<s>[{var}]</s>")
                    elif var_format == "Underline":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<u>[{var}]</u>")
                    elif var_format == "Spoiler":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<tg-spoiler>[{var}]</tg-spoiler>")
                    elif var_format == "BlockQuote":
                        preview_content = preview_content.replace(f"{{{var}}}", f"<blockquote>[{var}]</blockquote>")
                    else:
                        preview_content = preview_content.replace(f"{{{var}}}", f"[{var}]")
                signatures_text += f"🔹 امضا: {sig_name}\n📝 متن:\n{preview_content}\n\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=signatures_text,
                reply_markup=get_signature_management_menu(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, signatures_text, reply_markup=get_signature_management_menu(), parse_mode="HTML")
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ افزودن امضای جدید":
        data_store.update_user_state(user_id, "new_signature_name")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✏️ نام امضای جدید را وارد کنید:",
                reply_markup=get_back_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✏️ نام امزای جدید را وارد کنید:", reply_markup=get_back_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "🗑️ حذف امضا":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for sig_name in data_store.signatures.keys():
            markup.add(types.KeyboardButton(sig_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "delete_signature")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🗑️ امضای مورد نظر برای حذف را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ امزای مورد نظر برای حذف را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
            
# مدیریت کنترل‌ها
def get_variable_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده متغیرها")
    add_btn = types.KeyboardButton("➕ افزودن متغیر")
    remove_btn = types.KeyboardButton("➖ حذف متغیر")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, add_btn)
    markup.add(remove_btn, back_btn)
    return markup

def get_text_format_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    formats = [
        "Bold", "Italic", "Code", "Strike",
        "Underline", "Spoiler", "BlockQuote", "Simple"
    ]
    for fmt in formats:
        markup.add(types.KeyboardButton(fmt))
    markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    return markup

def handle_variable_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if text == "👀 مشاهده متغیرها":
        variables_text = f"{status_text}\n\n⚙️ متغیرها:\n\n"
        if not data_store.controls:
            variables_text += "هیچ متغیری وجود ندارد.\n"
        else:
            for var_name, var_data in data_store.controls.items():
                variables_text += f"🔹 {var_name}: نوع {var_data['format']}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=variables_text,
                reply_markup=get_variable_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, variables_text, reply_markup=get_variable_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ افزودن متغیر":
        data_store.update_user_state(user_id, "select_variable_format")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🖊️ نوع متغیر را انتخاب کنید:",
                reply_markup=get_text_format_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ نوع متغیر را انتخاب کنید:", reply_markup=get_text_format_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➖ حذف متغیر":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.controls.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_variable")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n🗑️ متغیری که می‌خواهید حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ متغیری که می‌خواهید حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif user_state["state"] == "select_variable_format":
        if text in ["Bold", "Italic", "Code", "Strike", "Underline", "Spoiler", "BlockQuote", "Simple"]:
            data_store.update_user_state(user_id, "add_variable", {"selected_format": text})
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n🖊️ نام متغیر جدید را وارد کنید (به انگلیسی، بدون فاصله):",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ نام متغیر جدید را وارد کنید (به انگلیسی، بدون فاصله):", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ نوع نامعتبر! لطفاً یکی از گزینه‌های منو را انتخاب کنید.",
                    reply_markup=get_text_format_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ نوع نامعتبر! لطفاً یکی از گزینه‌های منو را انتخاب کنید.", reply_markup=get_text_format_menu())
                data_store.last_message_id[user_id] = msg.message_id
    
    elif user_state["state"] == "add_variable":
        if not re.match(r'^[a-zA-Z0-9_]+$', text):
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ نام متغیر باید به انگلیسی و بدون فاصله باشد!",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ نام متغیر باید به انگلیسی و بدون فاصله باشد!", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        if text in data_store.controls:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ این نام متغیر قبلاً وجود دارد!",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ این نام متغیر قبلاً وجود دارد!", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        data_store.controls[text] = {"format": user_state["data"]["selected_format"]}
        data_store.save_data()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id[user_id],
                text=f"{status_text}\n\n✅ متغیر '{text}' با نوع {user_state['data']['selected_format']} اضافه شد.\n⚙️ مدیریت متغیرها:",
                reply_markup=get_variable_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ متغیر '{text}' با نوع {user_state['data']['selected_format']} اضافه شد.\n⚙️ مدیریت متغیرها:", reply_markup=get_variable_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "variable_management")
    
    elif user_state["state"] == "remove_variable":
        if text in data_store.controls:
            del data_store.controls[text]
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n✅ متغیر '{text}' حذف شد.\n⚙️ مدیریت متغیرها:",
                    reply_markup=get_variable_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ متغیر '{text}' حذف شد.\n⚙️ مدیریت متغیرها:", reply_markup=get_variable_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id[user_id],
                    text=f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.",
                    reply_markup=get_variable_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.", reply_markup=get_variable_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "variable_management")

    elif user_state["state"] == "remove_variable":
        if text in data_store.controls:
            # چک کن که متغیر توی هیچ امضایی استفاده نشده باشه
            used_in_signatures = []
            for sig_name, sig_data in data_store.signatures.items():
                if text in sig_data["variables"]:
                    used_in_signatures.append(sig_name)
            if used_in_signatures:
                try:
                    bot.edit_message_text(
                        chat_id=user_id,
                        message_id=data_store.last_message_id[user_id],
                        text=f"{status_text}\n\n⚠️ متغیر '{text}' در امضاهای {', '.join(used_in_signatures)} استفاده شده است. ابتدا این امضاها را ویرایش یا حذف کنید.",
                        reply_markup=get_variable_management_menu()
                    )
                except Exception as e:
                    logger.error(f"خطا در ویرایش پیام: {e}")
                    msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر '{text}' در امضاهای {', '.join(used_in_signatures)} استفاده شده است. ابتدا این امضاها را ویرایش یا حذف کنید.", reply_markup=get_variable_management_menu())
                    data_store.last_message_id[user_id] = msg.message_id
                return
            del data_store.controls[text]
            data_store.save_data()

def get_default_values_management_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    view_btn = types.KeyboardButton("👀 مشاهده مقادیر پیش‌فرض")
    set_btn = types.KeyboardButton("➕ تنظیم مقدار پیش‌فرض")
    remove_btn = types.KeyboardButton("➖ حذف مقدار پیش‌فرض")
    back_btn = types.KeyboardButton("🔙 بازگشت به منوی اصلی")
    markup.add(view_btn, set_btn)
    markup.add(remove_btn, back_btn)
    return markup

def handle_default_values_management(user_id, text):
    user_state = data_store.get_user_state(user_id)
    state = user_state.get("state", None)  # بهینه‌سازی: بررسی وجود state
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    if not (is_owner(user_id) or is_admin(user_id)):
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⛔️ دسترسی ندارید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای عدم دسترسی: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n⛔️ دسترسی ندارید.", reply_markup=get_main_menu(user_id))
            data_store.last_message_id[user_id] = msg.message_id
        return
    
    if text == "👀 مشاهده مقادیر پیش‌فرض":
        values_text = f"{status_text}\n\n📝 مقادیر پیش‌فرض:\n\n"
        if not data_store.default_values:
            values_text += "هیچ مقدار پیش‌فرضی وجود ندارد.\n"
        else:
            for var_name, value in data_store.default_values.items():
                values_text += f"🔹 {var_name}: {value}\n"
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=values_text,
                reply_markup=get_default_values_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای مشاهده مقادیر: {e}")
            msg = bot.send_message(user_id, values_text, reply_markup=get_default_values_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➕ تنظیم مقدار پیش‌فرض":
        if not data_store.controls:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ متغیری تعریف نشده است.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای عدم وجود متغیر: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ متغیری تعریف نشده است.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.controls.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "set_default_value_select_var")
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🖊️ متغیری که می‌خواهید مقدار پیش‌فرض برای آن تنظیم کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای تنظیم مقدار: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ متغیری که می‌خواهید مقدار پیش‌فرض برای آن تنظیم کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id
    
    elif text == "➖ حذف مقدار پیش‌فرض":
        if not data_store.default_values:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ هیچ مقدار پیش‌فرضی برای حذف وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای عدم وجود مقدار پیش‌فرض: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ هیچ مقدار پیش‌فرضی برای حذف وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            return
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        for var_name in data_store.default_values.keys():
            markup.add(types.KeyboardButton(var_name))
        markup.add(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
        data_store.update_user_state(user_id, "remove_default_value")
        try:
            bot.edit_message_text(
                chat_id=user_id,  # اصلاح خطا: chatelder به chat_id تغییر کرد
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n🗑️ متغیری که می‌خواهید مقدار پیش‌فرض آن را حذف کنید را انتخاب کنید:",
                reply_markup=markup
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای حذف مقدار پیش‌فرض: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n🗑️ متغیری که می‌خواهید مقدار پیش‌فرض آن را حذف کنید را انتخاب کنید:", reply_markup=markup)
            data_store.last_message_id[user_id] = msg.message_id

    elif state == "set_default_value_select_var":
        if text in data_store.controls:
            data_store.update_user_state(user_id, "set_default_value", {"selected_var": text})
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n🖊️ مقدار پیش‌فرض برای '{text}' را وارد کنید:",
                    reply_markup=get_back_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای وارد کردن مقدار پیش‌فرض: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n🖊️ مقدار پیش‌فرض برای '{text}' را وارد کنید:", reply_markup=get_back_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای متغیر ناموجود: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ متغیر انتخاب‌شده وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
            data_store.update_user_state(user_id, "default_values_management")
    
    elif state == "set_default_value":
        data_store.default_values[user_state["data"]["selected_var"]] = text
        data_store.save_data()
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{user_state['data']['selected_var']}' تنظیم شد.\n📝 مدیریت مقادیر پیش‌فرض:",
                reply_markup=get_default_values_management_menu()
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام برای تنظیم موفق: {e}")
            msg = bot.send_message(user_id, f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{user_state['data']['selected_var']}' تنظیم شد.\n📝 مدیریت مقادیر پیش‌فرض:", reply_markup=get_default_values_management_menu())
            data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "default_values_management")
    
    elif state == "remove_default_value":
        if text in data_store.default_values:
            del data_store.default_values[text]
            data_store.save_data()
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{text}' حذف شد.\n📝 مدیریت مقادیر پیش‌فرض:",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای حذف موفق: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n✅ مقدار پیش‌فرض برای '{text}' حذف شد.\n📝 مدیریت مقادیر پیش‌فرض:", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        else:
            try:
                bot.edit_message_text(
                    chat_id=user_id,
                    message_id=data_store.last_message_id.get(user_id),
                    text=f"{status_text}\n\n⚠️ مقدار پیش‌فرض برای '{text}' وجود ندارد.",
                    reply_markup=get_default_values_management_menu()
                )
            except Exception as e:
                logger.error(f"خطا در ویرایش پیام برای مقدار پیش‌فرض ناموجود: {e}")
                msg = bot.send_message(user_id, f"{status_text}\n\n⚠️ مقدار پیش‌فرض برای '{text}' وجود ندارد.", reply_markup=get_default_values_management_menu())
                data_store.last_message_id[user_id] = msg.message_id
        data_store.update_user_state(user_id, "default_values_management")

# هندلر دکمه‌های شیشه‌ای برای حذف تایمرها
@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_timer_"))
def delete_timer_callback(call):
    user_id = call.from_user.id
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    job_id = call.data.replace("delete_timer_", "")
    for post in data_store.scheduled_posts:
        if post["job_id"] == job_id:
            data_store.scheduled_posts.remove(post)
            data_store.save_data()
            schedule.clear(job_id)
            break
    
    try:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=data_store.last_message_id[user_id],
            text=f"{status_text}\n\n✅ تایمر {job_id} حذف شد.\n🏠 منوی اصلی:",
            reply_markup=get_main_menu(user_id)
        )
    except Exception as e:
        logger.error(f"خطا در ویرایش پیام: {e}")
        msg = bot.send_message(user_id, f"{status_text}\n\n✅ تایمر {job_id} حذف شد.\n🏠 منوی اصلی:", reply_markup=get_main_menu(user_id))
        data_store.last_message_id[user_id] = msg.message_id

# بعد از تعریف توابع و کلاس‌ها
@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    text = message.text
    user_state = data_store.get_user_state(user_id)
    state = user_state["state"]
    status_text = data_store.state_messages.get(state, "وضعیت نامشخص")
    
    data_store.last_user_message_id[user_id] = message.message_id
    
    if text in MAIN_MENU_BUTTONS:
        if process_main_menu_button(user_id, text):
            try:
                bot.delete_message(user_id, data_store.last_user_message_id[user_id])
            except Exception as e:
                logger.error(f"خطا در حذف پیام کاربر: {e}")
        return
    
    elif state == "admin_management":
        handle_admin_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    elif state == "signature_management":
        handle_signature_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    elif state == "variable_management":
        handle_variable_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    elif state == "default_values_management":
        handle_default_values_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    elif state == "media_management":
        handle_media_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    elif state in ["delete_media", "confirm_delete_media", "delete_sent_media"]:
        handle_media_management(user_id, text)
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")
    
    # اضافه کردن یک else برای مدیریت حالتی که هیچ شرطی مطابقت ندارد
    else:
        try:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=data_store.last_message_id.get(user_id),
                text=f"{status_text}\n\n⚠️ دستور نامعتبر. لطفاً از منو گزینه‌ای انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام: {e}")
            msg = bot.send_message(
                user_id,
                f"{status_text}\n\n⚠️ دستور نامعتبر. لطفاً از منو گزینه‌ای انتخاب کنید.",
                reply_markup=get_main_menu(user_id)
            )
            data_store.last_message_id[user_id] = msg.message_id
        try:
            bot.delete_message(user_id, data_store.last_user_message_id[user_id])
        except Exception as e:
            logger.error(f"خطا در حذف پیام کاربر: {e}")

# اجرای زمان‌بندی و بات
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    logger.info("بات در حال شروع است...")
    try:
        bot.send_message(OWNER_ID, f"🤖 ران شدم! نسخه: {BOT_VERSION}")
        logger.info(f"پیام 'بات ران شدم' به {OWNER_ID} ارسال شد.")
    except Exception as e:
        logger.error(f"خطا در ارسال پیام شروع بات: {e}")
    
    bot.polling(none_stop=True)