import json
import logging
import asyncio
import os
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
        "👑 لوحة التحكم الشاملة:\n\n"
        "📄 لتحديث سياسة الخصوصية مباشرة:\n"
        "/edit_privacy [النص الجديد]"
    )
    await update.message.reply_text(help_text)

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

        await update.message.reply_text("🔄 تم الكتابة في الملف بالمسار المطلق! جاري الرفع الفوري...")
        success, msg = await deploy_via_vercel()
        if success:
            await update.message.reply_text("✅ تم التعديل وظهرت التغييرات أونلاين فوراً!")
        else:
            await update.message.reply_text(f"⚠️ فشل الرفع: {msg[-200:]}")
    except Exception as e:
        await update.message.reply_text(f"❌ خطأ: {e}")

if __name__ == '__main__':
    TOKEN = "8977692829:AAFVzIxUkDOm40ifuZbzrW1BaBZP2V7mkJg"
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('edit_privacy', edit_privacy))
    print("🚀 البوت يعمل بالمسارات المطلقة...")
    application.run_polling()
