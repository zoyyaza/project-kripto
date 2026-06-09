from flask import Flask, render_template, request, jsonify
import base64
import random
import urllib.parse
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

app = Flask(__name__)

# --- ENGINE CRYPTO BARU: AES-256 CBC MODE ---
def get_aes_key_and_iv(otp_string):
    """Mengubah OTP 6-digit menjadi Kunci 32-byte (AES-256) & IV 16-byte menggunakan SHA-256"""
    hashed = hashlib.sha256(otp_string.encode('utf-8')).digest()
    key = hashed          # 32 byte untuk AES-256
    iv = hashed[:16]      # 16 byte pertama sebagai Initialization Vector (IV)
    return key, iv

def aes_encrypt(plaintext, otp_key):
    key, iv = get_aes_key_and_iv(otp_key)
    
    # Tambahkan padding PKCS7 agar panjang data sesuai kelipatan blok AES (16 byte)
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode('utf-8')) + padder.finalize()
    
    # Proses Enkripsi AES-CBC
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    
    return ciphertext.hex()

def aes_decrypt(ciphertext_hex, otp_key):
    try:
        key, iv = get_aes_key_and_iv(otp_key)
        ciphertext = bytes.fromhex(ciphertext_hex)
        
        # Proses Dekripsi AES-CBC
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Lepaskan padding PKCS7 untuk mengambil teks asli
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(decrypted_padded_data) + unpadder.finalize()
        return plaintext.decode('utf-8')
    except Exception:
        # Jika OTP salah, paksa sistem mengeluarkan teks acak buatan
        karakter_acak = "#$%^&*@!~+=?><ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        return "eits no no kepo ya" + "".join(random.choices(karakter_acak, k=30))

# --- ROUTES FLASK ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    nama = data.get('nama', '')
    whatsapp = data.get('whatsapp', '')
    pesan = data.get('pesan', '')
    
    if not pesan or not whatsapp:
        return jsonify({'error': 'Nomor WA dan Pesan wajib diisi!'}), 400
        
    if whatsapp.startswith('0'):
        whatsapp = '62' + whatsapp[1:]
    elif whatsapp.startswith('+'):
        whatsapp = whatsapp.replace('+', '')
        
    # Generate 6 Digit OTP otomatis oleh sistem
    otp_key = str(random.randint(100000, 999999))
    
    # EKSEKUSI AES-256
    ciphertext_hex = aes_encrypt(pesan, otp_key)
    
    # Token Base64 (Hanya berisi nama dan teks hex AES)
    raw_token = f"{nama}|{ciphertext_hex}"
    secure_token = base64.b64encode(raw_token.encode('utf-8')).decode('utf-8')
    
    base_url = request.url_root
    full_crypto_link = f"{base_url}decrypt_link?token={secure_token}"
    
    wa_text = f"<b> BEAR-LOCK SECURE MAIL (AES-256)</b>\n\nHalo, ada pesan rahasia khusus untuk Anda dari *{nama}*.\n\n🔗 *Link Akses*:\n{full_crypto_link}\n\n🔑 *KODE OTP VALIDASI ANDA*:\n{otp_key}\n\n<i>(Pesan dilindungi enkripsi blok AES-256, jangan bocorkan OTP ini)</i>"
    
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
        nama, ciphertext_hex = decoded_str.split('|')
    except:
        return "Token rusak atau dimanipulasi!", 400

    if request.method == 'GET':
        return render_template('index.html', mode='challenge', nama=nama, token=token)
        
    otp_input = request.form.get('otp_input', '')
    original_pesan = aes_decrypt(ciphertext_hex, otp_input)
    
    return render_template('index.html', mode='success', nama=nama, pesan=original_pesan, kunci=otp_input)

if __name__ == '__main__':
    app.run(debug=True)