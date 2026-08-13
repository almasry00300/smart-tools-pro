from flask import Blueprint, render_template, request, redirect, session, current_app
import os

admin_bp = Blueprint('admin', __name__)

# مفتاح أمان الجلسات لتفادي خطأ 500
@admin_bp.before_app_request
def setup_secret_key():
    if not current_app.secret_key:
        current_app.secret_key = 'smarttools_secret_key_super_safe'

db = None
try:
    import pymongo
    MONGO_URI = os.environ.get('MONGO_URI', '')
    if MONGO_URI:
        client = pymongo.MongoClient(MONGO_URI)
        db = client.smarttools
except Exception:
    db = None

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            return redirect('/admin')
        else:
            error = "اسم المستخدم أو كلمة السر غير صحيحة"
            
    return render_template('admin.html', view='login', error=error)

@admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    settings = {}
    if db is not None:
        try:
            settings = db.settings.find_one({"_id": "config"}) or {}
        except Exception:
            settings = {}
            
    return render_template('admin.html', view='dashboard', settings=settings)

@admin_bp.route('/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    config_data = {
        "_id": "config",
        "ads_enabled": True if request.form.get('ads_enabled') else False,
        "header_ad": request.form.get('header_ad'),
        "ads_txt": request.form.get('ads_txt'),
        "custom_header_code": request.form.get('custom_header_code')
    }
    
    if db is not None:
        try:
            db.settings.replace_one({"_id": "config"}, config_data, upsert=True)
        except Exception:
            pass
        
    return redirect('/admin')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')
