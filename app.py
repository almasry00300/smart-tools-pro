from flask import Flask, render_template, request, send_file, jsonify, redirect, make_response
from gtts import gTTS
import qrcode
import io
import base64
from pypdf import PdfReader, PdfWriter
import urllib.request
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse
import hashlib
import time
import os

app = Flask(__name__)

# إعدادات الاتصال المباشر بقاعدة البيانات عبر REST API
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_DsdesyOGwBszyysrtoFrgg_pWHepUJy")

site_settings = {
    "ads_enabled": True,
    "header_ad": "",
    "ads_txt": "",
    "custom_header_code": ""
}

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم الشاملة</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
<div class="container my-4" style="max-width: 800px;">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>لوحة إعدادات الموقع والإعلانات</h2>
        <a href="/admin/logout" class="btn btn-outline-danger">تسجيل خروج</a>
    </div>

    {% if saved %}
    <div class="alert alert-success">تم حفظ التغييرات بنجاح!</div>
    {% endif %}

    <form method="POST" action="/admin" class="card p-4 shadow-sm">
        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" name="ads_enabled" {% if settings.ads_enabled %}checked{% endif %}>
            <label class="form-check-label fw-bold">تفعيل الإعلانات في الموقع</label>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">شفرة إعلان الهيدر (Header Ad)</label>
            <textarea name="header_ad" class="form-control" rows="3">{{ settings.header_ad }}</textarea>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">محتوى ملف Ads.txt</label>
            <textarea name="ads_txt" class="form-control" rows="3">{{ settings.ads_txt }}</textarea>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">كود Header المخصص (Google Analytics / Meta)</label>
            <textarea name="custom_header_code" class="form-control" rows="3">{{ settings.custom_header_code }}</textarea>
        </div>
        <button type="submit" class="btn btn-success btn-lg w-100">حفظ كافة التغييرات</button>
    </form>
</div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <title>تسجيل الدخول</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
<div class="container mt-5" style="max-width: 400px;">
    <div class="card p-4 shadow-sm">
        <h4 class="text-center mb-3">تسجيل الدخول للوحة التحكم</h4>
        {% if error %}<div class="alert alert-danger p-2">{{ error }}</div>{% endif %}
        <form method="POST" action="/admin/login">
            <div class="mb-3">
                <label class="form-label">اسم المستخدم</label>
                <input type="text" name="username" class="form-control" required>
            </div>
            <div class="mb-3">
                <label class="form-label">كلمة السر</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">دخول</button>
        </form>
    </div>
</div>
</body>
</html>
"""


def save_site_config(settings):
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicate"
    }
    try:
        requests.post(f"{SUPABASE_URL}/rest/v1/site_content", json=settings, headers=headers, timeout=5)
    except: pass


def get_site_config():
    headers = { "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}" }
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/site_content?select=*", headers=headers, timeout=5).json()
        if res: return res[0] if isinstance(res, list) else res
    except: pass
    return site_settings

@app.route('/')
def home():
    config = get_site_config()
    return render_template('index.html', config=config)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.cookies.get('admin_auth') != 'logged_in':
        return redirect('/admin/login')
    
    saved = False
    if request.method == 'POST':
        site_settings['ads_enabled'] = True if request.form.get('ads_enabled') == 'on' else False
        site_settings['header_ad'] = request.form.get('header_ad', '')
        site_settings['ads_txt'] = request.form.get('ads_txt', '')
        site_settings['custom_header_code'] = request.form.get('custom_header_code', '')
        saved = True

    return render_template_string(ADMIN_HTML, settings=site_settings, saved=saved)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'admin123':
            resp = make_response(redirect('/admin'))
            resp.set_cookie('admin_auth', 'logged_in')
            return resp
        else:
            error = "بيانات الدخول غير صحيحة"
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/admin/logout')
def admin_logout():
    resp = make_response(redirect('/admin/login'))
    resp.set_cookie('admin_auth', '', expires=0)
    return resp

@app.route('/ads.txt')
def ads_txt():
    return site_settings['ads_txt'], 200, {'Content-Type': 'text/plain'}

@app.route('/word-counter')
def word_counter(): return render_template('word_counter.html')

@app.route('/char-counter')
def char_counter(): return render_template('char_counter.html')

@app.route('/remove-duplicate-lines')
def remove_duplicate_lines(): return render_template('remove_duplicate_lines.html')

@app.route('/seo-analyzer')
def seo_analyzer(): return render_template('seo_analyzer.html')
@app.route('/age-calculator')
def age_calculator(): return render_template('age_calculator.html')

@app.route('/qr-generator')
def qr_generator_page(): return render_template('qr_generator.html')

@app.route('/generate-qr')
def generate_qr_action():
    text = request.args.get('text', '')
    if not text: return "No text", 400
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/password-generator')
def password_generator(): return render_template('password_generator.html')

@app.route('/domain-checker')
def domain_checker(): return render_template('domain_checker.html')

@app.route('/text-to-speech')
def text_to_speech(): return render_template('text_to_speech.html')

@app.route('/download-speech')
def download_speech():
    text = request.args.get('text', '')
    if not text: return "No text", 400
    tts = gTTS(text=text, lang='ar', slow=False)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    return send_file(fp, mimetype='audio/mp3', as_attachment=True, download_name='smarttools-speech.mp3')

@app.route('/color-extractor')
def color_checker(): return render_template('color_extractor.html')

@app.route('/image-converter')
def image_converter(): return render_template('image_converter.html')

{