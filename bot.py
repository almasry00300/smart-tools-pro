import json
import logging
import asyncio
import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'site_content.json')

def load_data():
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"tools_descriptions": {}, "blog_posts": [], "pages": {}, "social_links": {}}

def save_data(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def clean_html_tags(text):
    text = re.sub(r'</?(h[1-6]|p|div|strong|b|i|u)[^>]*>', '\n', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text

async def deploy_via_vercel():
    try:
        process = await asyncio.create_subprocess_shell(
            "vercel --prod --yes",
            cwd=BASE_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60.0)
            return process.returncode == 0, stdout.decode() if process.returncode == 0 else stderr.decode()
        except asyncio.TimeoutError:
            process.kill()
            return False, "Timeout"
    except Exception as e:
        return False, str(e)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "👑 لوحة التحكم الشاملة لإثراء محتوى موقعك (مقبول أدسنس):\n\n"
        "📝 1. قسم التدوين والمقالات الحصرية:\n"
        "نشر: /write_post [المقال الطويل] | [العنوان]\n\n"
        "🛠️ 2. تعديل شروحات ووصف الأدوات:\n"
        "/set_desc [الشرح الطويل] | [معرف_الأداة]\n"
        "💡 معرفات الأدوات المتاحة: `word_counter`, `qr_generator` وغيرها.\n\n"
        "📄 3. الصفحات القانونية الإلزامية:\n"
        "تعديل صفحة من نحن: /edit_about [النص]\n"
        "تعديل سياسة الخصوصية: /edit_privacy [النص]\n"
        "تعديل صفحة اتصل بنا: /edit_contact [النص]"
    )
    await update.message.reply_text(help_text)

async def write_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_text = " ".join(context.args)
    if "|" not in full_text:
        await update.message.reply_text("❌ صيغة خاطئة! المثال:\n/write_post المقال هنا | عنوان المقال")
        return
    parts = full_text.split("|", 1)
    content = parts[0].strip()
    title = parts[1].strip()
    
    data = load_data()
    if "blog_posts" not in data:
        data["blog_posts"] = []
    data["blog_posts"].insert(0, {"title": title, "content": content})
    save_data(data)

    await update.message.reply_text("🔄 تم حفظ المقال! جاري الرفع إلى Vercel...")
    success, msg = await deploy_via_vercel()
    if success:
        await update.message.reply_text("✅ تم نشر المقال وظهر على الموقع فوراً!")
    else:
        await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")

async def set_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_text = " ".join(context.args)
    if "|" not in full_text:
        await update.message.reply_text("❌ صيغة خاطئة! المثال:\n/set_desc الشرح الجديد للأداة | word_counter")
        return
    parts = full_text.split("|", 1)
    desc = parts[0].strip()
    tool_id = parts[1].strip()

    data = load_data()
    if "tools_descriptions" not in data:
        data["tools_descriptions"] = {}
    data["tools_descriptions"][tool_id] = desc
    save_data(data)

    await update.message.reply_text(f"🔄 تم تحديث وصف الأداة ({tool_id})! جاري الرفع...")
    success, msg = await deploy_via_vercel()
    if success:
        await update.message.reply_text("✅ تم التحديث وظهرت النتيجة أونلاين!")
    else:
        await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")

async def edit_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة النص بعد الأمر.")
        return
    text = " ".join(context.args)
    file_path = os.path.join(BASE_DIR, 'templates', 'about.html')
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>من نحن</title>
    <style>
        body {{ font-family: Tahoma, sans-serif; padding: 20px; line-height: 2; background: #fff; color: #222; margin: 0; }}
        .container {{ max-width: 800px; margin: auto; padding: 10px; }}
        h1 {{ font-size: 26px; color: #000; text-align: center; margin-bottom: 20px; }}
        p, div {{ font-size: 18px; word-break: break-word; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>من نحن</h1>
        <hr style="border: 0; border-top: 1px solid #ddd; margin-bottom: 20px;">
        <div>{text}</div>
    </div>
</body>
</html>''')
        await update.message.reply_text("🔄 جاري الرفع...")
        success, msg = await deploy_via_vercel()
        if success:
            await update.message.reply_text("✅ تم تحديث صفحة من نحن بنجاح!")
        else:
            await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def edit_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة النص بعد الأمر.")
        return
    text = " ".join(context.args)
    file_path = os.path.join(BASE_DIR, 'templates', 'privacy.html')
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>سياسة الخصوصية</title>
    <style>
        body {{ font-family: Tahoma, sans-serif; padding: 20px; line-height: 2; background: #fff; color: #222; margin: 0; }}
        .container {{ max-width: 800px; margin: auto; padding: 10px; }}
        h1 {{ font-size: 26px; color: #000; text-align: center; margin-bottom: 20px; }}
        p, div {{ font-size: 18px; word-break: break-word; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>سياسة الخصوصية</h1>
        <hr style="border: 0; border-top: 1px solid #ddd; margin-bottom: 20px;">
        <div>{text}</div>
    </div>
</body>
</html>''')
        await update.message.reply_text("🔄 جاري الرفع...")
        success, msg = await deploy_via_vercel()
        if success:
            await update.message.reply_text("✅ تم تحديث سياسة الخصوصية بنجاح!")
        else:
            await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

async def edit_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ يرجى كتابة النص بعد الأمر.")
        return
    text = " ".join(context.args)
    file_path = os.path.join(BASE_DIR, 'templates', 'contact.html')
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>اتصل بنا</title>
    <style>
        body {{ font-family: Tahoma, sans-serif; padding: 20px; line-height: 2; background: #fff; color: #222; margin: 0; }}
        .container {{ max-width: 800px; margin: auto; padding: 10px; }}
        h1 {{ font-size: 26px; color: #000; text-align: center; margin-bottom: 20px; }}
        p, div {{ font-size: 18px; word-break: break-word; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>اتصل بنا</h1>
        <hr style="border: 0; border-top: 1px solid #ddd; margin-bottom: 20px;">
        <div>{text}</div>
    </div>
</body>
</html>''')
        await update.message.reply_text("🔄 جاري الرفع...")
        success, msg = await deploy_via_vercel()
        if success:
            await update.message.reply_text("✅ تم تحديث صفحة اتصل بنا بنجاح!")
        else:
            await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

if __name__ == '__main__':
    TOKEN = "8977692829:AAFVzIxUkDOm40ifuZbzrW1BaBZP2V7mkJg"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('write_post', write_post))
    application.add_handler(CommandHandler('set_desc', set_desc))
    application.add_handler(CommandHandler('edit_about', edit_about))
    application.add_handler(CommandHandler('edit_privacy', edit_privacy))
    application.add_handler(CommandHandler('edit_contact', edit_contact))
    print("🚀 البوت يعمل بكامل أوامره وصلاحياته...")
    application.run_polling()
