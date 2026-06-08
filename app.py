from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Halo! Ini adalah web Flask baru saya yang siap di-deploy dari nol."

if __name__ == '__main__':
    # Railway akan memberikan PORT secara otomatis melalui environment variable
    port = int(os.environ.get("PORT", 5000))
    # Host harus diatur ke 0.0.0.0 agar bisa diakses dari luar
    app.run(host='0.0.0.0', port=port)