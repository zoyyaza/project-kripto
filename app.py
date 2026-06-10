from flask import Flask, render_template, request, jsonify, session
import base64
import random
import urllib.parse
import urllib.request
import hashlib
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

app = Flask(__name__)
app.secret_key = "BEAR_LOCK_SUPER_SECRET_KEY_SANGAT_RAHASIA"

# --- HELPER SHORTLINK (Mengubah Link Panjang Jadi Pendek via TinyURL) ---
def shorten_url(long_url):
    try:
        api_url = f"http://tinyurl.com/api-create.php?url={urllib.parse.quote(long_url)}"
        with urllib.request.urlopen(api_url, timeout=5) as response:
            return response.read().decode('utf-8')
    except Exception:
        return long_url # Jika gagal/timeout, kembalikan link asli agar aplikasi tidak crash

# --- ENGINE CRYPTO AES-256 CBC MODE ---
def get_aes_key_and_iv(otp_string):
    hashed = hashlib.sha256(otp_string.encode('utf-8')).digest()
    return hashed, hashed[:16]

def aes_encrypt(plaintext, otp_key):
    key, iv = get_aes_key_and_iv(otp_key)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return (encryptor.update(padded_data) + encryptor.finalize()).hex()

def aes_decrypt(ciphertext_hex, otp_key):
    try:
        key, iv = get_aes_key_and_iv(otp_key)
        ciphertext = bytes.fromhex(ciphertext_hex)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        return (unpadder.update(decrypted_padded_data) + unpadder.finalize()).decode('utf-8')
    except Exception:
        return None

# --- ROUTES FLASK ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    nama = data.get('nama', '')
    penerima = data.get('penerima', '') # Input baru: Nama Penerima
    whatsapp = data.get('whatsapp', '')
    pesan = data.get('pesan', '')
    
    if not pesan or not whatsapp or not penerima:
        return jsonify({'error': 'Semua kolom input wajib diisi!'}), 400
        
    if whatsapp.startswith('0'):
        whatsapp = '62' + whatsapp[1:]
    elif whatsapp.startswith('+'):
        whatsapp = whatsapp.replace('+', '')
        
    otp_key = str(random.randint(100000, 999999))
    ciphertext_hex = aes_encrypt(pesan, otp_key)
    
    otp_hash = hashlib.sha256(otp_key.encode('utf-8')).hexdigest()
    raw_token = f"{nama}|{ciphertext_hex}|{otp_hash}"
    secure_token = base64.b64encode(raw_token.encode('utf-8')).decode('utf-8')
    
    base_url = request.url_root
    full_crypto_link = f"{base_url}decrypt_link?token={secure_token}"
    
    # Eksekusi pemendek link otomatis
    short_crypto_link = shorten_url(full_crypto_link)
    
    # Format teks pesan WhatsApp bersih tanpa tag HTML (Menggunakan format markdown WA)
    wa_text = f"Halo *{penerima}*, ada pesan rahasia khusus untuk Anda dari *{nama}*.\n\n🔗 *Link Akses*:\n{short_crypto_link}\n\n🔑 *KODE OTP VALIDASI ANDA*:\n{otp_key}\n\n_ (Pesan hanya bisa dibuka 1x dan maksimal 3x percobaan OTP!)_"
    wa_direct_link = f"https://api.whatsapp.com/send?phone={whatsapp}&text={urllib.parse.quote(wa_text)}"
    
    return jsonify({
        'token': secure_token,
        'wa_link': wa_direct_link
    })

@app.route('/decrypt_link', methods=['GET', 'POST'])
def decrypt_link():
    token = request.args.get('token', '')
    if not token:
        return "Token Tidak Valid!", 400
        
    try:
        decoded_str = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        nama, ciphertext_hex, otp_hash = decoded_str.split('|')
    except:
        return "Token rusak atau dimanipulasi!", 400

    token_key = hashlib.md5(token.encode('utf-8')).hexdigest()
    
    if token_key not in session:
        session[token_key] = {'attempts': 0, 'is_burned': False}
        
    state = session[token_key]

    if state.get('is_burned'):
        return render_template('index.html', mode='challenge', nama=nama, token=token, error_msg="Pesan ini sudah hangus karena telah dibuka sekali!")

    if state.get('attempts') >= 3:
        return render_template('index.html', mode='challenge', nama=nama, token=token, error_msg="Akses diblokir! Anda telah salah memasukkan OTP sebanyak 3 kali.")

    if request.method == 'GET':
        return render_template('index.html', mode='challenge', nama=nama, token=token)
        
    otp_input = request.form.get('otp_input', '')
    input_hash = hashlib.sha256(otp_input.encode('utf-8')).hexdigest()
    
    if input_hash != otp_hash:
        state['attempts'] += 1
        session[token_key] = state
        sisa = 3 - state['attempts']
        
        if sisa <= 0:
            msg = "Akses diblokir! Anda telah salah memasukkan OTP sebanyak 3 kali."
        else:
            msg = f"Kode OTP salah! Sisa percobaan Anda: {sisa} kali lagi."
            
        return render_template('index.html', mode='challenge', nama=nama, token=token, error_msg=msg)

    original_pesan = aes_decrypt(ciphertext_hex, otp_input)
    
    state['is_burned'] = True
    session[token_key] = state

    return render_template('index.html', mode='success', nama=nama, pesan=original_pesan, kunci=otp_input)

if __name__ == '__main__':
    app.run(debug=True)