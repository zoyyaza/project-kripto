from flask import Flask, render_template, request, jsonify
import base64
import random
import urllib.parse

app = Flask(__name__)

# --- FUNGSI GENERATE OTP ACAK ---
def generate_otp():
    # Membuat 6 digit angka acak sebagai kunci pengganti Vigenere manual
    return str(random.randint(100000, 999999))

# --- FUNGSI KRIPTOR VIGENERE (Sistem yang menentukan kunci memakai OTP) ---
def vigenere_encrypt(plaintext, key):
    cipher_text = []
    key = key.upper()
    for i, char in enumerate(plaintext):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('A')
            if char.isupper():
                cipher_text.append(chr((ord(char) - ord('A') + shift) % 26 + ord('A')))
            else:
                cipher_text.append(chr((ord(char) - ord('a') + shift) % 26 + ord('a')))
        else:
            cipher_text.append(char)
    return "".join(cipher_text)

def vigenere_decrypt(ciphertext, key):
    plain_text = []
    key = key.upper()
    for i, char in enumerate(ciphertext):
        if char.isalpha():
            shift = ord(key[i % len(key)]) - ord('A')
            if char.isupper():
                plain_text.append(chr((ord(char) - ord('A') - shift) % 26 + ord('A')))
            else:
                plain_text.append(chr((ord(char) - ord('a') - shift) % 26 + ord('a')))
        else:
            plain_text.append(char)
    return "".join(plain_text)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# --- 1. PROSES OTP & DIRECT LINK WA ---
@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    nama = data.get('nama', '')
    whatsapp = data.get('whatsapp', '')
    pesan = data.get('pesan', '')
    
    if not pesan or not whatsapp:
        return jsonify({'error': 'Nomor WA dan Pesan wajib diisi!'}), 400
        
    # Format nomor WA agar seragam menggunakan standar internasional (62)
    if whatsapp.startswith('0'):
        whatsapp = '62' + whatsapp[1:]
    elif whatsapp.startswith('+'):
        whatsapp = whatsapp.replace('+', '')
        
    # OTOMATISASI: Sistem membuat kunci OTP sendiri secara rahasia
    otp_key = generate_otp()
    
    # Lapis 1: Enkripsi pesan dengan kunci OTP otomatis
    ciphertext = vigenere_encrypt(pesan, otp_key)
    
    # Lapis 2: Token hanya berisi Nama dan Ciphertext (Kunci OTP tidak dibocorkan di URL!)
    raw_token = f"{nama}|{ciphertext}"
    secure_token = base64.b64encode(raw_token.encode('utf-8')).decode('utf-8')
    
    base_url = request.url_root
    full_crypto_link = f"{base_url}decrypt_link?token={secure_token}"
    
    # Isi pesan teks yang langsung ditembak ke WhatsApp tujuan
    wa_text = f"🔒 *BEAR-LOCK SECURE MAIL*\n\nHalo, ada pesan rahasia khusus untuk Anda dari *{nama}*.\n\n🔗 *Link Akses Pesan*:\n{full_crypto_link}\n\n🔑 *KODE OTP DEKRIPSI ANDA*:\n{otp_key}\n\n_(Jangan bocorkan kode OTP ini kepada siapapun)_"
    
    # Bypass langsung menggunakan parameter phone=
    wa_direct_link = f"https://api.whatsapp.com/send?phone={whatsapp}&text={urllib.parse.quote(wa_text)}"
    
    return jsonify({
        'token': secure_token,
        'wa_link': wa_direct_link
    })

# --- 2. GERBANG VERIFIKASI OTP ---
@app.route('/decrypt_link', methods=['GET', 'POST'])
def decrypt_link():
    token = request.args.get('token', '')
    if not token:
        return "Token Kadaluwarsa atau Tidak Valid!", 400
        
    try:
        decoded_str = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        nama, ciphertext = decoded_str.split('|')
    except:
        return "Token mengalami kerusakan struktur!", 400

    if request.method == 'GET':
        return render_template('index.html', mode='challenge', nama=nama, token=token)
        
    # Memeriksa OTP yang dimasukkan penerima di web
    otp_input = request.form.get('otp_input', '')
    original_pesan = vigenere_decrypt(ciphertext, otp_input)
    
    return render_template('index.html', mode='success', nama=nama, pesan=original_pesan, kunci=otp_input)

if __name__ == '__main__':
    app.run(debug=True)