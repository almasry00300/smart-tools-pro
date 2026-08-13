from flask import Blueprint, render_template_string, request, redirect, session
import os

admin_bp = Blueprint('admin', __name__)

# تعيين مفتاح أمان الجلسات فور تشغيل السيرفر وقبل أي طلب
@admin_bp.record_once
def on_load(state):
    app = state.app
    if not app.secret_key:
        app.secret_key = 'smarttools_super_secret_key_2026'

# الواجهة مدمجة بالكامل لمنع أي خطأ في الملفات (TemplateNotFound)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم | SmartToolsPro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.rtl.min.css" rel="stylesheet">
</head>
<body class="bg-light">

{% if view == 'login' %}
<div class="container mt-5" style="max-width: 400px;">
    <div class="card p-4 shadow-sm">
        <h4 class="text-center mb-3">تسجيل الدخول للوحة التحكم</h4>
        {% if error %}<div class="alert alert-danger p-2">{{ error }}</div>{% endif %}
        <form action="/admin/login" method="POST">
            <div class="mb-3">
                <label>اسم المستخدم</label>
                <input type="text" name="username" class="form-control" required>
            </div>
            <div class="mb-3">
                <label>كلمة السر</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">دخول</button>
        </form>
    </div>
</div>
{% else %}
<div class="container my-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>لوحة إعدادات الموقع والإعلانات</h2>
        <a href="/admin/logout" class="btn btn-outline-danger">تسجيل خروج</a>
    </div>

    <form action="/admin/save-settings" method="POST" class="card p-4 shadow-sm">
        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" name="ads_enabled" {% if settings.get('ads_enabled') %}checked{% endif %}>
            <label class="form-check-label fw-bold">تفعيل الإعلانات</label>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">شفرة إعلان الهيدر (Header Ad)</label>
            <textarea name="header_ad" class="form-control" rows="3">{{ settings.get('header_ad', '') }}</textarea>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">محتوى ملف Ads.txt</label>
            <textarea name="ads_txt" class="form-control" rows="3">{{ settings.get('ads_txt', '') }}</textarea>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold">كود Header المخصص (Google Analytics / Meta)</label>
            <textarea name="custom_header_code" class="form-control" rows="3">{{ settings.get('custom_header_code', '') }}</textarea>
        </div>
        <button type="submit" class="btn btn-success btn-lg">حفظ التغييرات</button>
    </form>
</div>
{% endif %}

</body>
</html>
"""

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
            
    return render_template_string(HTML_TEMPLATE, view='login', error=error)

@admin_bp.route('/')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    
    return render_template_string(HTML_TEMPLATE, view='dashboard', settings={})

@admin_bp.route('/save-settings', methods=['POST'])
def save_settings():
    if not session.get('admin_logged_in'):
        return redirect('/admin/login')
    return redirect('/admin')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')
