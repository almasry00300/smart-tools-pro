from flask import Blueprint, render_template, request, redirect, session, url_for
import os
import pymongo

# إنشاء البلوبرينت للوحة التحكم
admin_bp = Blueprint('admin', __name__)

# رابط الاتصال بقاعدة البيانات (يجلب كلمة السر من Vercel أو يستخدم الرابط المباشر)
MONGO_URI = os.environ.get('MONGO_URI', 'Mongodb+srv://almasry0030:ضع_كلمة_السر_هنا@cluster0.tomwzzi.mongodb.net/?appName=Cluster0')

try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client.smarttools
except Exception as e:
    db = None
    print("خطأ في الاتصال بقاعدة البيانات:", e)

# ===============================================
# 🔐 مسارات لوحة التحكم (Admin Panel Routes)
# ===============================================

# 1. صفحة تسجيل الدخول للوحة
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # يمكنك تغيير اسم المستخدم وكلمة السر هنا
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error = "اسم المستخدم أو كلمة السر غير صحيحة"
            
    return render_template('admin.html', view='login', error=error)

# 2. الصفحة الرئيسية للوحة التحكم
@admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    settings = db.settings.find_one({"_id": "config"}) if db is not None else {}
    tools = list(db.tools.find()) if db is not None else []
    posts = list(db.posts.find()) if db is not None else []
    
    return render_template('admin.html', view='dashboard', settings=settings, tools=tools, posts=posts)

# 3. حفظ إعدادات الموقع والإعلانات و ads.txt
@admin_bp.route('/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    config_data = {
        "_id": "config",
        "site_name": request.form.get('site_name'),
        "ads_enabled": True if request.form.get('ads_enabled') else False,
        "header_ad": request.form.get('header_ad'),
        "footer_ad": request.form.get('footer_ad'),
        "in_tool_ad": request.form.get('in_tool_ad'),
        "ads_txt": request.form.get('ads_txt'),
        "custom_header_code": request.form.get('custom_header_code'),
        "custom_footer_code": request.form.get('custom_footer_code')
    }
    
    if db is not None:
        db.settings.replace_one({"_id": "config"}, config_data, upsert=True)
        
    return redirect('/admin')

# 4. حفظ وتعديل مقالات المدونة (CMS)
@admin_bp.route('/save-post', methods=['POST'])
def save_post():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    title = request.form.get('title')
    slug = request.form.get('slug') or title.lower().replace(' ', '-')
    content = request.form.get('content')
    
    post_data = {
        "title": title,
        "slug": slug,
        "content": content
    }
    
    if db is not None:
        db.posts.insert_one(post_data)
        
    return redirect('/admin')

# 5. تسجيل الخروج
@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')
