from flask import Flask, render_template, request, send_file, jsonify
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
        requests.post(f"{SUPABASE_URL}/rest/v1/site_settings", json=settings, headers=headers, timeout=5)
    except: pass

def get_site_config():
    headers = { "apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}" }
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/site_settings?select=*", headers=headers, timeout=5).json()
        if res: return res
    except: pass
    return {
        "header_color": "#ea580c", "card_color": "#f1f5f9", "bg_color": "#ffffff",
        "fb_url": "#", "tw_url": "#", "yt_url": "#", "tt_url": "#", "ig_url": "#", "tg_url": "#"
    }

@app.route('/')
def home():
    config = get_site_config()
    return render_template('index.html', config=config)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password != "admin123": return "كلمة المرور خاطئة!", 403
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
            "tg_url": request.form.get('tg_url', '#')
        }
        save_site_config(new_settings)
        return "تم حفظ وتحديث الإعدادات أونلاين بنجاح! 🚀"
    config = get_site_config()
    return render_template('admin.html', config=config)

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
            content = tag.get('content', '').strip()
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
        "what_is": "عداد الكلمات هو أداة تساعدك على معرفة عدد الكلمات والحروف والأسطر الموجودة في أي نص. وهي مفيدة للكتاب والطلاب وأصحاب المواقع ومنشئي المحتوى.",
        "how_to": "اكتب أو الصق النص داخل أداة عداد الكلمات، وستظهر لك الإحصائيات الخاصة بالنص بشكل مباشر.",
        "features": "حساب عدد الكلمات، حساب عدد الحروف، معرفة عدد الأسطر، والعمل مباشرة من المتصفح بدون الحاجة إلى تثبيت برنامج.",
        "benefits": "تساعدك الأداة على التحكم في طول المقالات والمنشورات والنصوص، كما توفر طريقة سريعة لمعرفة حجم المحتوى قبل نشره.",
        "faqs": [
            {"question": "هل الأداة مجانية؟", "answer": "نعم، يمكنك استخدام الأداة مجانًا من خلال موقع SmartToolsPro."},
            {"question": "هل أحتاج إلى تثبيت برنامج؟", "answer": "لا، تعمل الأداة مباشرة من المتصفح."}
        ]
    },
    "char-counter": {
        "title": "عداد الحروف",
        "description": "احسب عدد الحروف والكلمات والأسطر في النص بسهولة.",
        "what_is": "عداد الحروف أداة تساعدك على معرفة عدد الأحرف الموجودة في النص مع إمكانية معرفة عدد الكلمات والأسطر.",
        "how_to": "الصق النص أو اكتبه داخل الأداة، وستظهر النتائج والإحصائيات تلقائيًا.",
        "features": "حساب إجمالي الحروف، الحروف بدون مسافات، الكلمات والأسطر بطريقة سهلة وسريعة.",
        "benefits": "مفيدة للكتابة وصناعة المحتوى والمنشورات التي تتطلب الالتزام بعدد محدد من الحروف أو الكلمات.",
        "faqs": [
            {"question": "هل تحسب الأداة المسافات؟", "answer": "تعرض الأداة إجمالي الحروف ويمكنها أيضًا حساب الحروف بدون المسافات."},
            {"question": "هل تعمل على الهاتف؟", "answer": "نعم، يمكنك استخدامها من الهاتف أو الكمبيوتر."}
        ]
    },
    "age-calculator": {
        "title": "حاسبة العمر",
        "description": "احسب عمرك بدقة باستخدام تاريخ الميلاد.",
        "what_is": "حاسبة العمر تساعدك على معرفة العمر بالسنوات والأشهر والأيام بناءً على تاريخ الميلاد.",
        "how_to": "اختر تاريخ ميلادك ثم استخدم زر الحساب للحصول على النتيجة.",
        "features": "حساب العمر بسرعة، واجهة بسيطة، واستخدام مباشر من المتصفح.",
        "benefits": "توفر طريقة سهلة لمعرفة العمر بدقة دون إجراء الحسابات يدويًا.",
        "faqs": [
            {"question": "هل الحساب مجاني؟", "answer": "نعم، الأداة مجانية."},
            {"question": "هل تعمل على الهاتف؟", "answer": "نعم، تعمل على مختلف الأجهزة."}
        ]
    },
    "qr-generator": {
        "title": "منشئ كود QR",
        "description": "حوّل الروابط والنصوص إلى كود QR بسهولة وسرعة.",
        "what_is": "منشئ QR هو أداة تحول النصوص والروابط إلى رمز QR يمكن مسحه باستخدام كاميرا الهاتف.",
        "how_to": "أدخل الرابط أو النص الذي تريد تحويله، ثم أنشئ كود QR واحفظ الصورة لاستخدامها.",
        "features": "إنشاء أكواد QR بسرعة، دعم الروابط والنصوص، وإمكانية استخدام الكود على الهواتف.",
        "benefits": "يساعدك على مشاركة الروابط والمعلومات بسرعة وربط المواد المطبوعة بالمحتوى الرقمي.",
        "faqs": [
            {"question": "هل يمكن استخدامه مع روابط المواقع؟", "answer": "نعم، يمكنك تحويل أي رابط إلى كود QR."},
            {"question": "هل يحتاج المستخدم إلى تطبيق خاص؟", "answer": "يمكن مسح الكود باستخدام تطبيق الكاميرا أو قارئ QR متوافق."}
        ]
    },
    "password-generator": {
        "title": "منشئ كلمات المرور",
        "description": "أنشئ كلمات مرور قوية وعشوائية لحماية حساباتك.",
        "what_is": "منشئ كلمات المرور يساعدك على إنشاء كلمات مرور عشوائية يصعب تخمينها.",
        "how_to": "حدد الإعدادات المطلوبة ثم أنشئ كلمة مرور قوية واستخدمها لحساباتك.",
        "features": "إنشاء كلمات مرور عشوائية، دعم الأحرف والأرقام والرموز، وسهولة الاستخدام.",
        "benefits": "يساعد استخدام كلمات مرور قوية وفريدة على تحسين مستوى حماية الحسابات الرقمية.",
        "faqs": [
            {"question": "هل يتم حفظ كلمات المرور؟", "answer": "الأداة مصممة لإنشاء كلمة المرور للاستخدام المباشر ولا تحتاج إلى حفظها داخل الموقع."},
            {"question": "هل يمكن استخدام كلمة المرور لأكثر من حساب؟", "answer": "يفضل استخدام كلمة مرور مختلفة وفريدة لكل حساب."}
        ]
    },
    "domain-checker": {
        "title": "فحص النطاق",
        "description": "افحص معلومات وأمان نطاق موقعك بسهولة.",
        "what_is": "أداة فحص النطاق تساعد أصحاب المواقع على مراجعة معلومات النطاق وبعض مؤشرات الأمان المرتبطة به.",
        "how_to": "أدخل اسم النطاق أو الرابط الذي تريد فحصه ثم ابدأ عملية الفحص.",
        "features": "واجهة بسيطة، فحص سريع، وإمكانية استخدام الأداة من المتصفح.",
        "benefits": "تساعد أصحاب المواقع على متابعة حالة النطاق وفهم بعض الجوانب التقنية المتعلقة بالموقع.",
        "faqs": [
            {"question": "هل الفحص مجاني؟", "answer": "نعم، يمكنك استخدام الأداة مجانًا."},
            {"question": "هل يمكن فحص أي موقع؟", "answer": "يمكنك إدخال نطاق أو رابط متاح للفحص عبر الإنترنت."}
        ]
    },
    "text-to-speech": {
        "title": "تحويل النص إلى كلام",
        "description": "حوّل النصوص العربية إلى صوت واستمع إليها بسهولة.",
        "what_is": "أداة تحويل النص إلى كلام تحول النص المكتوب إلى ملف صوتي يمكن الاستماع إليه.",
        "how_to": "أدخل النص الذي تريد تحويله ثم ابدأ عملية التحويل للحصول على الملف الصوتي.",
        "features": "تحويل النصوص العربية إلى صوت، استخدام مباشر من المتصفح، وإمكانية تحميل الملف الصوتي.",
        "benefits": "مفيدة للاستماع إلى النصوص والمقالات وتحويل المحتوى المكتوب إلى محتوى صوتي.",
        "faqs": [
            {"question": "هل تدعم اللغة العربية؟", "answer": "نعم، الأداة مهيأة لتحويل النصوص العربية إلى صوت."},
            {"question": "هل يمكن تحميل الملف الصوتي؟", "answer": "نعم، يمكن تحميل الملف الصوتي الناتج."}
        ]
    },
    "color-extractor": {
        "title": "استخراج الألوان من الصور",
        "description": "استخرج أكواد الألوان من الصور بسهولة.",
        "what_is": "أداة استخراج الألوان تساعد المصممين وأصحاب المواقع على معرفة أكواد الألوان المستخدمة في الصور.",
        "how_to": "ارفع الصورة أو استخدم الصورة داخل الأداة لاستخراج الألوان والأكواد المناسبة.",
        "features": "استخراج أكواد الألوان، استخدام سهل، ومناسبة للتصميم وتطوير المواقع.",
        "benefits": "تساعدك على بناء هوية بصرية متناسقة واختيار ألوان دقيقة لمشروعاتك الرقمية.",
        "faqs": [
            {"question": "ما صيغة كود اللون؟", "answer": "يمكن استخدام أكواد HEX في التصميم وتطوير المواقع."},
            {"question": "هل الأداة مفيدة للمصممين؟", "answer": "نعم، فهي تساعد على استخراج الألوان من الصور بسرعة."}
        ]
    },
    "image-converter": {
        "title": "تحويل صيغ الصور",
        "description": "حوّل الصور بين الصيغ المختلفة بسهولة.",
        "what_is": "أداة تحويل الصور تساعدك على تغيير صيغة الصورة لتناسب الاستخدام المطلوب.",
        "how_to": "اختر الصورة وحدد الصيغة المطلوبة ثم نفذ عملية التحويل.",
        "features": "تحويل الصور، واجهة سهلة، واستخدام مباشر.",
        "benefits": "تساعدك على تجهيز الصور للمواقع والتطبيقات ومختلف الاستخدامات الرقمية.",
        "faqs": [
            {"question": "هل الأداة سهلة الاستخدام؟", "answer": "نعم، تم تصميمها لتكون بسيطة ومباشرة."},
            {"question": "هل أحتاج إلى برنامج؟", "answer": "لا، يمكنك استخدامها من المتصفح."}
        ]
    },
    "image-compressor": {
        "title": "ضغط الصور",
        "description": "قلل حجم الصور للمساعدة في تحسين سرعة تحميل المواقع.",
        "what_is": "أداة ضغط الصور تساعد على تقليل حجم الملفات مع الحفاظ على جودة مناسبة للاستخدام.",
        "how_to": "اختر الصورة التي تريد ضغطها ثم نفذ عملية الضغط واحفظ النتيجة.",
        "features": "تقليل حجم الصور، سهولة الاستخدام، وتجهيز الصور للويب.",
        "benefits": "الصور الأصغر حجمًا يمكن أن تساعد في تقليل وقت تحميل الصفحات وتحسين تجربة المستخدم.",
        "faqs": [
            {"question": "لماذا أضغط الصور؟", "answer": "لتقليل حجم الملفات والمساعدة في تحسين سرعة تحميل الصفحات."},
            {"question": "هل يؤثر الضغط على الجودة؟", "answer": "قد تختلف النتيجة حسب مستوى الضغط المستخدم."}
        ]
    },
    "pdf-to-images": {
        "title": "تحويل PDF إلى صور",
        "description": "استخرج الصور الموجودة داخل ملفات PDF بسهولة.",
        "what_is": "أداة PDF إلى صور تساعدك على استخراج الصور الموجودة داخل ملف PDF.",
        "how_to": "ارفع ملف PDF إلى الأداة ثم ابدأ عملية الاستخراج للحصول على الصور.",
        "features": "استخراج الصور من ملفات PDF، معالجة مباشرة، وواجهة سهلة.",
        "benefits": "توفر وقتًا كبيرًا عند الحاجة إلى استخراج الصور من مستندات PDF.",
        "faqs": [
            {"question": "هل يمكن استخدام ملفات PDF متعددة؟", "answer": "يعتمد ذلك على طريقة استخدام الأداة وحجم الملفات."},
            {"question": "هل الأداة تعمل على الهاتف؟", "answer": "نعم، يمكن استخدامها من المتصفح على الهاتف."}
        ]
    },
    "pdf-tools": {
        "title": "أدوات PDF",
        "description": "مجموعة أدوات للتعامل مع ملفات PDF عبر الإنترنت.",
        "what_is": "توفر أدوات PDF وظائف مفيدة للتعامل مع المستندات والملفات بصيغة PDF.",
        "how_to": "اختر الوظيفة التي تحتاج إليها ثم ارفع الملفات المطلوبة واتبع التعليمات.",
        "features": "أدوات PDF سهلة الاستخدام، معالجة مباشرة، وواجهة مناسبة للمستخدمين.",
        "benefits": "تساعدك على إنجاز مهام PDF بسرعة دون الحاجة إلى تثبيت برامج متخصصة.",
        "faqs": [
            {"question": "هل الأدوات مجانية؟", "answer": "يمكنك استخدام الأدوات المتاحة على الموقع مجانًا."},
            {"question": "هل تعمل على الهاتف؟", "answer": "نعم، يمكن الوصول إليها من المتصفح."}
        ]
    },
    "meta-analyzer": {
        "title": "محلل Meta Tags",
        "description": "حلل بيانات Meta Tags الخاصة بصفحات المواقع.",
        "what_is": "محلل Meta Tags يساعد أصحاب المواقع على الاطلاع على العنوان والوصف وبعض البيانات المهمة للصفحة.",
        "how_to": "أدخل رابط الصفحة التي تريد تحليلها ثم ابدأ الفحص.",
        "features": "عرض عنوان الصفحة، الوصف، الكلمات المفتاحية وبيانات Open Graph المتاحة.",
        "benefits": "يساعدك على مراجعة البيانات الأساسية التي تظهر لمحركات البحث وبعض منصات المشاركة.",
        "faqs": [
            {"question": "هل الأداة مفيدة لتحسين SEO؟", "answer": "نعم، يمكنها مساعدتك في مراجعة بعض عناصر الصفحة المهمة للسيو."},
            {"question": "هل يمكن تحليل أي رابط؟", "answer": "يمكن تحليل الصفحات التي تسمح بالوصول إليها عبر الإنترنت."}
        ]
    },
    "broken-links": {
        "title": "فحص الروابط المعطلة",
        "description": "افحص الروابط الموجودة في صفحة موقعك واكتشف الروابط التي قد تواجه مشاكل.",
        "what_is": "أداة فحص الروابط المعطلة تساعد أصحاب المواقع على مراجعة الروابط الموجودة داخل صفحاتهم.",
        "how_to": "أدخل رابط الصفحة ثم ابدأ الفحص لعرض الروابط وحالات الاستجابة.",
        "features": "فحص الروابط، عرض حالات HTTP، والمساعدة في اكتشاف الروابط التي تحتاج إلى مراجعة.",
        "benefits": "مراجعة الروابط تساعد في تحسين تجربة المستخدم والحفاظ على جودة الموقع.",
        "faqs": [
            {"question": "هل الفحص يشمل كل الموقع؟", "answer": "الأداة الحالية تفحص الروابط الموجودة في الصفحة التي تدخل رابطها."},
            {"question": "هل النتيجة دقيقة دائمًا؟", "answer": "قد تختلف النتائج حسب إعدادات الخوادم والروابط الخارجية."}
        ]
    },
    "sitemap-generator": {
        "title": "منشئ Sitemap",
        "description": "اكتشف روابط موقعك وساعد محركات البحث على فهم بنية الموقع.",
        "what_is": "منشئ Sitemap يساعدك على جمع روابط الصفحات الموجودة داخل موقعك لاستخدامها في إنشاء خريطة موقع.",
        "how_to": "أدخل رابط موقعك ثم ابدأ الفحص للحصول على قائمة بالروابط المكتشفة.",
        "features": "اكتشاف الروابط الداخلية، واجهة سهلة، ومساعدة في تجهيز بيانات خريطة الموقع.",
        "benefits": "خريطة الموقع المنظمة تساعد محركات البحث على اكتشاف صفحات الموقع وفهم هيكله.",
        "faqs": [
            {"question": "هل Sitemap مهمة للسيو؟", "answer": "يمكن أن تساعد محركات البحث على اكتشاف صفحات الموقع بشكل أفضل."},
            {"question": "هل تضمن ظهور الموقع في Google؟", "answer": "لا، لكنها تساعد في عملية اكتشاف الصفحات ولا تضمن الفهرسة أو الترتيب."}
        ]
    },
    "robots-generator": {
        "title": "منشئ Robots.txt",
        "description": "أنشئ إعدادات Robots.txt لمساعدة محركات البحث على فهم الصفحات المسموح بزحفها.",
        "what_is": "ملف robots.txt يستخدم لإعطاء تعليمات لروبوتات محركات البحث حول المسارات التي يمكن الزحف إليها.",
        "how_to": "حدد الإعدادات المطلوبة ثم أنشئ النص المناسب لملف robots.txt.",
        "features": "إنشاء تعليمات Robots.txt، دعم Sitemap، وواجهة سهلة.",
        "benefits": "يساعدك على إدارة تعليمات الزحف الأساسية الخاصة بموقعك.",
        "faqs": [
            {"question": "هل Robots.txt يمنع الفهرسة بشكل مضمون؟", "answer": "لا، ملف robots.txt مخصص لتعليمات الزحف وليس وسيلة مضمونة لمنع الفهرسة."},
            {"question": "هل يجب إضافة Sitemap؟", "answer": "يمكن إضافة رابط Sitemap لمساعدة محركات البحث على اكتشاف الخريطة."}
        ]
    },
    "hash-generator": {
        "title": "مولد Hash",
        "description": "أنشئ قيم Hash للنصوص باستخدام خوارزميات مختلفة.",
        "what_is": "مولد Hash يحول النص إلى قيمة رقمية ثابتة باستخدام خوارزمية تجزئة محددة.",
        "how_to": "أدخل النص واختر الخوارزمية ثم احصل على قيمة Hash الناتجة.",
        "features": "دعم MD5 وSHA-1 وSHA-256، وسهولة الاستخدام.",
        "benefits": "مفيد للتعلم وفهم مفهوم التجزئة ومقارنة القيم الناتجة عن النصوص.",
        "faqs": [
            {"question": "هل Hash هو تشفير؟", "answer": "لا، التجزئة تختلف عن التشفير ولا تهدف إلى استعادة النص الأصلي."},
            {"question": "ما الخوارزميات المتاحة؟", "answer": "الأداة الحالية تدعم MD5 وSHA-1 وSHA-256."}
        ]
    },
    "site-speed": {
        "title": "فحص سرعة الموقع",
        "description": "احصل على قياس تقريبي لوقت استجابة وتحميل صفحة الموقع.",
        "what_is": "أداة فحص سرعة الموقع تقيس الوقت الذي يستغرقه طلب الصفحة وتعرض حجم الاستجابة وحالة HTTP.",
        "how_to": "أدخل رابط الصفحة ثم ابدأ الفحص للحصول على النتائج.",
        "features": "قياس وقت الاستجابة، حالة HTTP، وحجم المحتوى المستلم.",
        "benefits": "توفر مؤشرًا أوليًا يساعدك على متابعة أداء الموقع وملاحظة التغييرات.",
        "faqs": [
            {"question": "هل هذه نتيجة اختبار سرعة شامل؟", "answer": "لا، هي قراءة تقريبية لزمن الطلب وحجم الاستجابة وليست بديلًا عن أدوات قياس الأداء المتخصصة."},
            {"question": "هل تختلف النتيجة؟", "answer": "نعم، قد تختلف حسب الخادم والشبكة وموقع المستخدم."}
        ]
    },
    "seo-analyzer": {
        "title": "محلل SEO",
        "description": "أداة تساعدك على مراجعة بعض عناصر تحسين محركات البحث.",
        "what_is": "محلل SEO يساعد أصحاب المواقع على مراجعة بعض العناصر الأساسية المرتبطة بتحسين ظهور الصفحات في محركات البحث.",
        "how_to": "أدخل البيانات أو الرابط المطلوب تحليله ثم راجع النتائج والتوصيات.",
        "features": "تحليل عناصر SEO الأساسية، واجهة سهلة، ومساعدة في اكتشاف نقاط التحسين.",
        "benefits": "تساعد المراجعة الدورية على تحسين جودة صفحات الموقع وتجربة المستخدم.",
        "faqs": [
            {"question": "هل التحليل يضمن تصدر Google؟", "answer": "لا توجد أداة تضمن الترتيب، فالنتائج تعتمد على عوامل كثيرة."},
            {"question": "هل يمكن استخدام الأداة للمواقع الجديدة؟", "answer": "نعم، يمكن استخدامها لمراجعة الصفحات وتحسينها."}
        ]
    },
    "remove-duplicate-lines": {
        "title": "إزالة الأسطر المكررة",
        "description": "نظف النصوص وأزل الأسطر المتكررة بسرعة.",
        "what_is": "أداة إزالة الأسطر المكررة تساعدك على تنظيف القوائم والنصوص التي تحتوي على بيانات مكررة.",
        "how_to": "الصق النص داخل الأداة ثم نفذ عملية إزالة التكرار للحصول على قائمة أنظف.",
        "features": "إزالة التكرارات، معالجة النصوص بسرعة، وسهولة الاستخدام.",
        "benefits": "مفيدة لتنظيف القوائم والبيانات النصية وتوفير الوقت في المعالجة اليدوية.",
        "faqs": [
            {"question": "هل تحذف الأداة النصوص الأصلية؟", "answer": "يمكنك استخدام الناتج الجديد بعد إزالة الأسطر المتكررة."},
            {"question": "هل تعمل مع القوائم الطويلة؟", "answer": "يمكن استخدامها مع النصوص والقوائم حسب إمكانيات المتصفح."}
        ]
    }
}

@app.route('/tool/<tool_slug>')
def tool_guide(tool_slug):
    tool = TOOL_GUIDES.get(tool_slug)

    if not tool:
        return "الأداة غير موجودة", 404

    tool["url"] = "/" + tool_slug

    return render_template(
        "tool_info.html",
        tool=tool
    )

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
