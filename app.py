from flask import Flask, render_template, request, send_file, jsonify, render_template_string, redirect, make_response
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
SUPABASE_URL = "https://supabase.co"
SUPABASE_KEY = "sb_publishable_DsdesyOGwBszyysrtoFrgg_pWHepUJy"

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
        if res: return res
    except: pass
    return {
        "header_color": "#ea580c", "card_color": "#f1f5f9", "bg_color": "#ffffff",
        "fb_url": "#", "tw_url": "#", "yt_url": "#", "tt_url": "#", "ig_url": "#", "tg_url": "#",
        "ads_txt": "",
        "header_ad": "",
        "custom_header_code": "",
        "ads_enabled": False
    }

def _normalize_settings(cfg):
    # Supabase may return a list of records — take the first
    if isinstance(cfg, list) and len(cfg) > 0:
        return cfg[0]
    return cfg

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
<div class="container my-4" style="max-width: 900px;">
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
            <label class="form-label fw-bold">لون الهيدر</label>
            <input type="color" name="header_color" value="{{ settings.header_color }}" class="form-control form-control-color">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">لون البطاقات</label>
            <input type="color" name="card_color" value="{{ settings.card_color }}" class="form-control form-control-color">
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">لون الخلفية</label>
            <input type="color" name="bg_color" value="{{ settings.bg_color }}" class="form-control form-control-color">
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
                <label class="form-label">اسم المستخدم (اختياري)</label>
                <input type="text" name="username" class="form-control" >
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

@app.route('/')
def home():
    config = _normalize_settings(get_site_config())
    return render_template('index.html', config=config)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.cookies.get('admin_auth') != 'logged_in':
        return redirect('/admin/login')

    saved = False
    if request.method == 'POST':
        new_settings = {
            "id": 1,
            "header_color": request.form.get('header_color', '#ea580c'),
            "card_color": request.form.get('card_color', '#f1f5f9'),
            "bg_color": request.form.get('bg_color', '#ffffff'),
            "fb_url": request.form.get('fb_url', '#'),
            "tw_url": request.form.get('tw_url', '#'),
            "yt_url": request.form.get('yt_url', '#'),
            "tt_url": request.form.get('tt_url', '#'),
            "ig_url": request.form.get('ig_url', '#'),
            "tg_url": request.form.get('tg_url', '#'),
            "ads_enabled": True if request.form.get('ads_enabled') == 'on' or request.form.get('ads_enabled') == 'checked' else False,
            "header_ad": request.form.get('header_ad', ''),
            "ads_txt": request.form.get('ads_txt', ''),
            "custom_header_code": request.form.get('custom_header_code', '')
        }
        save_site_config(new_settings)
        saved = True

    config = _normalize_settings(get_site_config())
    return render_template_string(ADMIN_HTML, settings=config, saved=saved)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password')
        # allow password-only login for compatibility; prefer env var for real password
        ADMIN_PASS = os.environ.get('ADMIN_PASSWORD', 'admin123')
        if password and password == ADMIN_PASS:
            resp = make_response(redirect('/admin'))
            resp.set_cookie('admin_auth', 'logged_in', httponly=True, samesite='Lax')
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
    cfg = _normalize_settings(get_site_config())
    return cfg.get('ads_txt', ''), 200, {'Content-Type': 'text/plain'}

# (باقي التطبيق كما كان)

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

@app.route('/image-compressor')
def image_compressor(): return render_template('image_compressor.html')

@app.route('/pdf-to-images')
def pdf_to_images(): return render_template('pdf_to_images.html')

@app.route('/convert-pdf', methods=['POST'])
def convert_pdf_to_images():
    if 'pdf_file' not in request.files: return jsonify({'error': 'No file'}), 400
    file = request.files['pdf_file']
    if file.filename == '': return jsonify({'error': 'No file'}), 400
    try:
        reader = PdfReader(file)
        images_data = []
        for page_num, page in enumerate(reader.pages, start=1):
            for count, image_file_object in enumerate(page.images, start=1):
                img_io = io.BytesIO(image_file_object.data)
                img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')
                images_data.append({
                    'page': page_num, 'name': f"page_{page_num}_img_{count}.png", 'base64': f"data:image/png;base64,{img_base64}"
                })
        return jsonify({'images': images_data})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/pdf-tools')
def pdf_tools_page(): return render_template('pdf_tools.html')

@app.route('/merge-pdfs', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('pdf_files')
    if not files or len(files) < 2: return "Need 2 files", 400
    try:
        writer = PdfWriter()
        for file in files:
            reader = PdfReader(file)
            for page in reader.pages: writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return send_file(output, mimetype='application/pdf', as_attachment=True, download_name='smarttools-merged.pdf')
    except Exception as e: return str(e), 500

@app.route('/meta-analyzer')
def meta_analyzer(): return render_template('meta_analyzer.html')

@app.route('/fetch-meta', methods=['POST'])
def fetch_meta_tags():
    url = request.json.get('url', '').strip()
    if not url: return jsonify({'error': 'No URL'}), 400
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=7) as response: html = response.read()
        soup = BeautifulSoup(html, 'html.parser')
        meta_data = {
            'title': soup.title.string.strip() if soup.title else 'N/A',
            'description': 'N/A', 'keywords': 'N/A', 'og_title': 'N/A', 'og_desc': 'N/A'
        }
        for tag in soup.find_all('meta'):
            name = tag.get('name', '').lower()
            prop = tag.get('property', '').lower()
            content = (tag.get('content') or '').strip()
            if name == 'description': meta_data['description'] = content
            elif name == 'keywords': meta_data['keywords'] = content
            elif prop == 'og:title': meta_data['og_title'] = content
            elif prop == 'og:description': meta_data['og_desc'] = content
        return jsonify(meta_data)
    except Exception as e: return jsonify({'error': 'Error'}), 500

@app.route('/broken-links')
def broken_links_page(): return render_template('broken_links.html')

@app.route('/check-links', methods=['POST'])
def check_page_links():
    url = request.json.get('url', '').strip()
    if not url: return jsonify({'error': 'No URL'}), 400
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(response.text, 'html.parser')
        links_to_check = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            full_url = urljoin(url, href)
            if urlparse(full_url).scheme in ('http', 'https'): links_to_check.append(full_url)
        unique_links = list(set(links_to_check))[:10]
        results = []
        for link in unique_links:
            try:
                res = requests.head(link, headers=headers, timeout=3, allow_redirects=True)
                status = res.status_code
            except: status = "Fail"
            results.append({'url': link, 'status': status})
        return jsonify({'links': results})
    except Exception as e: return jsonify({'error': 'Error'}), 500

@app.route('/sitemap-generator')
def sitemap_generator_page(): return render_template('sitemap_generator.html')

@app.route('/generate-sitemap', methods=['POST'])
def generate_sitemap_action():
    url = request.json.get('url', '').strip()
    if not url: return jsonify({'error': 'No URL'}), 400
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == urlparse(url).netloc: links.append(full_url)
        unique_links = list(set(links))[:20]
        return jsonify({'links': unique_links})
    except Exception as e: return jsonify({'error': 'Error'}), 500

@app.route('/robots-generator')
def robots_generator_page(): return render_template('robots_generator.html')

@app.route('/hash-generator')
def hash_generator_page(): return render_template('hash_generator.html')

@app.route('/calculate-hash', methods=['POST'])
def calculate_hash_action():
    text = request.json.get('text', '').encode('utf-8')
    algo = request.json.get('algo', 'md5')
    if algo == 'sha256': res = hashlib.sha256(text).hexdigest()
    elif algo == 'sha1': res = hashlib.sha1(text).hexdigest()
    else: res = hashlib.md5(text).hexdigest()
    return jsonify({'hash': res})

@app.route('/site-speed')
def site_speed_page(): return render_template('site_speed.html')

@app.route('/check-speed', methods=['POST'])
def check_speed_action():
    url = request.json.get('url', '').strip()
    if not url: return jsonify({'error': 'No URL'}), 400
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        start_time = time.time()
        res = requests.get(url, headers=headers, timeout=10)
        end_time = time.time()
        load_time = round((end_time - start_time), 2)
        status = res.status_code
        size = round(len(res.content) / 1024, 2)
        return jsonify({'load_time': load_time, 'status': status, 'size': size})
    except Exception as e: return jsonify({'error': 'Fail'}), 500


@app.route('/about')
def about_page():
    return render_template('about.html')

@app.route('/contact')
def contact_page():
    return render_template('contact.html')

@app.route('/privacy')
def privacy_page():
    return render_template('privacy.html')

@app.route('/terms')
def terms_page():
    return render_template('terms.html')

@app.route('/disclaimer')
def disclaimer_page():
    return render_template('disclaimer.html')



# ============================================================
# نظام الشروحات التلقائية لأدوات SmartToolsPro
# ============================================================

TOOL_GUIDES = {
    "word-counter": {
        "title": "عداد الكلمات",
        "description": "أداة مجانية لعد الكلمات والحروف والأسطر في النصوص بسرعة وسهولة.",
        "what_is": "عداد الكلمات هو أداة تساعدك على معرفة عدد الكلمات والحروف والأسطر الموجودة في أي نص. وهي مفيدة ل...",
        "how_to": "اكتب أو الصق النص داخل أداة عداد الكلمات، وستظهر لك الإحصائيات الخاصة بالنص بشكل مباشر.",
        "features": "حساب عدد الكلمات، حساب عدد الحروف، معرفة عدد الأسطر، والعمل مباشرة من المتصفح بدون الحاجة إلى تثبيت.",
        "benefits": "تساعدك الأداة على التحكم في طول المقالات والمنشورات والنصوص، كما توفر طريقة سريعة لمعرفة حجم المحتوى.",
        "faqs": [
            {"question": "هل الأداة مجانية؟", "answer": "نعم، يمكنك استخدام الأداة مجانًا من خلال موقع SmartToolsPro."},
            {"question": "هل أحتاج إلى تثبيت برنامج؟", "answer": "لا، تعمل الأداة مباشرة من المتصفح."}
        ]
    }
}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
