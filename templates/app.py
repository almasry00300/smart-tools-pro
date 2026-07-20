from flask import Flask, render_template

app = Flask(__name__)

# مسار الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('index.html')

# مسار الأداة الأولى: عداد الكلمات المتقدم
@app.route('/word-counter')
def word_counter():
    return render_template('word_counter.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
