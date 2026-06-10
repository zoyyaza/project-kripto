import os
import sqlite3
import hashlib
import base64
from flask import Flask, render_template, request, flash, redirect, url_for
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding

app = Flask(__name__)
app.secret_key = "BEARLOCK_SECRET_KEY"
DATABASE = 'crypto.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_name TEXT NOT NULL,
            whatsapp_number TEXT NOT NULL,
            ciphertext TEXT NOT NULL,
            otp_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def aes_encrypt(plaintext, otp_string):
    key = hashlib.sha256(otp_string.encode()).digest()
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(iv + ciphertext).decode('utf-8')

def aes_decrypt(ciphertext_b64, otp_string):
    try:
        key = hashlib.sha256(otp_string.encode()).digest()
        raw_data = base64.b64decode(ciphertext_b64)
        iv = raw_data[:16]
        actual_ciphertext = raw_data[16:]
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.unsafe_decryptor() if hasattr(cipher, 'unsafe_decryptor') else cipher.decryptor()
        padded_plaintext = decryptor.update(actual_ciphertext) + decryptor.finalize()
        unpadded_context = padding.PKCS7(128).unpadder()
        plaintext = unpadded_context.update(padded_plaintext) + unpadded_context.finalize()
        return plaintext.decode('utf-8')
    except Exception:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sender = request.form.get('sender_name')
        whatsapp = request.form.get('whatsapp_number')
        pesan = request.form.get('message')
        otp = request.form.get('otp')
        
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        ciphertext = aes_encrypt(pesan, otp)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (sender_name, whatsapp_number, ciphertext, otp_hash)
            VALUES (?, ?, ?, ?)
        ''', (sender, whatsapp, ciphertext, otp_hash))
        conn.commit()
        message_id = cursor.lastrowid
        conn.close()
        
        share_url = url_for('view_message', id=message_id, _external=True)
        whatsapp_url = f"https://api.whatsapp.com/send?phone={whatsapp}&text=Halo,%20ada%20pesan%20rahasia%20BearLock%20untukmu.%20Buka%20link:%20{share_url}%20dan%20masukkan%20OTP:%20{otp}"
        
        return render_template('index.html', whatsapp_url=whatsapp_url, share_url=share_url)
        
    return render_template('index.html')

@app.route('/view/<int:id>', methods=['GET', 'POST'])
def view_message(id):
    conn = get_db_connection()
    message = conn.execute('SELECT * FROM messages WHERE id = ?', (id,)).fetchone()
    conn.close()
    
    if message is None:
        return "Pesan tidak ditemukan", 404

    if request.method == 'POST':
        input_otp = request.form.get('otp', '').strip()
        input_otp_hash = hashlib.sha256(input_otp.encode()).hexdigest()
        
        if input_otp_hash != message['otp_hash']:
            flash("OTP salah! Akses ditolak.", "danger")
            return redirect(url_for('view_message', id=id))
        
        decrypted_text = aes_decrypt(message['ciphertext'], input_otp)
        if decrypted_text is None:
            flash("Gagal mendekripsi pesan.", "danger")
            return redirect(url_for('view_message', id=id))
            
        return render_template('challenge.html', plaintext=decrypted_text, sender=message['sender_name'], success=True)

    return render_template('challenge.html', success=False)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)