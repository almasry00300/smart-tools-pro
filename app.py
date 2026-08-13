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
from jinja2 import TemplateNotFound

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

TOOL_GUIDES = {
    "word-counter": {
        "title": "عداد الكلمات",
        "description": "أداة مجانية لعد الكلمات والحروف والأسطر في النصوص بسرعة وسهلة.",
        "what_is": "عداد الكلمات هو أداة تساعدك على معرفة عدد الكلمات والحروف والأسطر الموجودة في أي نص. وهي مفيدة ل.[...],",
        "how_to": "اكتب أو الصق النص داخل أداة عداد الكلمات، وستظهر لك الإحصائيات الخاصة بالنص بشكل مباشر.",
        "features": "حساب عدد الكلمات، حساب عدد الحروف، معرفة عدد الأسطر، والعمل مباشرة من المتصفح بدون الحاجة إلى ت[...],",
        "benefits": "تساعدك الأداة على التحكم في طول المقالات والمنشورات والنصوص، كما توفر طريقة سريعة لمعرفة حجم ا�[...],",
        "faqs": [
            {"question": "هل الأداة مجانية؟", "answer": "نعم، يمكنك استخدام الأداة مجانًا من خلال موقع SmartToolsPro."},
            {"question": "هل أحتاج إلى تثبيت برنامج؟", "answer": "لا، تعمل الأداة مباشرة من المتصفح."}
        ]
    }
}

@app.route('/tool/<tool_slug>')
def tool_guide(tool_slug):
    # Try dedicated template names using hyphen and underscore variants
    candidates = [f"{tool_slug}.html", f"{tool_slug.replace('-', '_')}.html"]
    for tpl in candidates:
        try:
            return render_template(tpl)
        except TemplateNotFound:
            continue

    tool = TOOL_GUIDES.get(tool_slug)

    if not tool:
        return "الأداة غير موجودة", 404

    tool["url"] = "/" + tool_slug

    return render_template(
        "tool_info.html",
        tool=tool
    )

@app.route('/robots-generator')
def robots_generator_page(): return render_template('robots_generator.html')

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

@app.route('/robots.txt')
def robots_txt():
    return """User-agent: *
Allow: /

Sitemap: https://smart-tools-pro.vercel.app/sitemap.xml
""", 200, {'Content-Type': 'text/plain'}

@app.route('/google11655a0f321b5df3.html')
def google_verification():
    return "google-site-verification: google11655a0f321b5df3.html"

@app.route('/sitemap.xml')
def sitemap_xml():
    urls = [
        'https://smart-tools-pro.vercel.app/',
        'https://smart-tools-pro.vercel.app/about',
        'https://smart-tools-pro.vercel.app/contact',
        'https://smart-tools-pro.vercel.app/privacy',
        'https://smart-tools-pro.vercel.app/terms',
        'https://smart-tools-pro.vercel.app/disclaimer',
        'https://smart-tools-pro.vercel.app/word-counter',
        'https://smart-tools-pro.vercel.app/char-counter',
        'https://smart-tools-pro.vercel.app/age-calculator',
        'https://smart-tools-pro.vercel.app/color-extractor',
        'https://smart-tools-pro.vercel.app/domain-checker',
        'https://smart-tools-pro.vercel.app/hash-generator',
        'https://smart-tools-pro.vercel.app/image-compressor',
        'https://smart-tools-pro.vercel.app/image-converter',
        'https://smart-tools-pro.vercel.app/meta-analyzer',
        'https://smart-tools-pro.vercel.app/password-generator',
        'https://smart-tools-pro.vercel.app/pdf-to-images',
        'https://smart-tools-pro.vercel.app/pdf-tools',
        'https://smart-tools-pro.vercel.app/qr-generator',
        'https://smart-tools-pro.vercel.app/remove-duplicate-lines',
        'https://smart-tools-pro.vercel.app/robots-generator',
        'https://smart-tools-pro.vercel.app/seo-analyzer',
        'https://smart-tools-pro.vercel.app/site-speed',
        'https://smart-tools-pro.vercel.app/sitemap-generator',
        'https://smart-tools-pro.vercel.app/text-to-speech'
    ]

    xml = '<?xml version="1.0" encoding="UTF-8"?>'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for url in urls:
        xml += f'<url><loc>{url}</loc></url>'

    xml += '</urlset>'

    return xml, 200, {'Content-Type': 'application/xml; charset=utf-8'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
