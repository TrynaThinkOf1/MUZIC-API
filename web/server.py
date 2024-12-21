from flask import Flask, render_template, request, redirect

site = Flask(__name__)

@site.route('/')
def index():
    return render_template("index.html")

@site.route('/admin')
def admin():
    return render_template("admin.html")

if __name__ == '__main__':
    site.run(debug=True, host='0.0.0.0')