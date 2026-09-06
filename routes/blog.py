from flask import Blueprint, render_template
import json
import os

blog_bp = Blueprint('blog', __name__)

_cached_blog_data = None

def get_fast_blog_data():
    global _cached_blog_data
    if _cached_blog_data is not None:
        return _cached_blog_data
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(current_dir, 'site_content.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            _cached_blog_data = json.load(f)
            return _cached_blog_data
    except:
        return {"blog_posts": []}

@blog_bp.route('/blog')
def blog_section():
    try:
        with open('site_content.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"blog_posts": []}
    return render_template('blog.html', posts=data.get("blog_posts", []))

@blog_bp.route('/blog/post/<post_id>')
def view_full_post(post_id):
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(current_dir, 'site_content.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"blog_posts": []}
    post = next((p for p in data.get("blog_posts", []) if p.get("id") == str(post_id)), None)
    if not post: return "المقال غير موجود أو تم حذفه", 404
    return render_template('post.html', post=post)

@blog_bp.route('/blog-speed')
def fast_blog_index():
    data = get_fast_blog_data()
    return render_template('blog.html', posts=data.get("blog_posts", []))

@blog_bp.route('/blog/post-speed/<post_id>')
def fast_view_post(post_id):
    data = get_fast_blog_data()
    post = next((p for p in data.get("blog_posts", []) if p.get("id") == str(post_id)), None)
    if not post: return "المقال غير موجود", 404
    return render_template('post.html', post=post)

@blog_bp.route('/privacy-policy-fast')
def fast_privacy_page():
    data = get_fast_blog_data()
    pages_data = data.get("pages", {})
    privacy_content = pages_data.get("privacy", "جاري تحديث المحتوى...")
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>سياسة الخصوصية وشروط الاستخدام</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, -apple-system, sans-serif; }}
            body {{ background-color: #0b1329; color: #f8fafc; padding: 25px 20px; line-height: 1.8; }}
            .container {{ max-width: 650px; margin: 0 auto; width: 100%; }}
            .nav-back {{ margin-bottom: 25px; }}
            .btn-back {{ text-decoration: none; color: #94a3b8; background: #1e293b; padding: 8px 16px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; display: inline-block; }}
            h1 {{ font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-bottom: 15px; border-right: 4px solid #ea580c; padding-right: 10px; }}
            .content {{ font-size: 1.05rem; text-align: justify; white-space: pre-line; color: #cbd5e1; background: #111827; padding: 20px; border-radius: 12px; border: 1px solid #1f2937; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav-back"><a href="/" class="btn-back">← العودة للرئيسية</a></div>
            <h1>سياسة الخصوصية وشروط الاستخدام</h1>
            <hr style="border: 0; border-top: 1px solid #1e293b; margin: 20px 0;">
            <div class="content">{privacy_content}</div>
        </div>
    </body>
    </html>
    """

@blog_bp.route('/privacy-policy')
def official_privacy_page():
    data = get_fast_blog_data()
    privacy_content = data.get("pages", {}).get("privacy", "جاري تحديث المحتوى...")
    return render_template('privacy.html', content=privacy_content)
