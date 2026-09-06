from flask import Flask
from routes.tools import tools_bp
from routes.blog import blog_bp

app = Flask(__name__)

# تسجيل الأجزاء المنظمة (Blueprints)
app.register_blueprint(tools_bp)
app.register_blueprint(blog_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
