from flask import Flask, render_template, request, jsonify
import base64
import urllib.parse

app = Flask(__name__)

# --- FUNGSI KRIPTOR (VIGENERE + BASE64) ---
def vigenere_encrypt(plaintext, key):
    cipher_text = []
    key = key.upper()
    for i, char in enumerate(plaintext):
        if char.isalpha():
            # Menghitung pergeseran berdasarkan huruf kunci
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

# --- ROUTE UTAMA (DASHBOARD) ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# --- 1. API UNTUK GENERATE LINK OTOMATIS ---
@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    nama = data.get('nama', '')
    pesan = data.get('pesan', '')
    kunci = data.get('kunci', '')
    
    if not pesan or not kunci:
        return jsonify({'error': 'Pesan dan Kunci wajib diisi'}), 400
        
    # Lapis 1: Enkripsi Vigenere
    vigenere_result = vigenere_encrypt(pesan, kunci)
    
    # Lapis 2: Satukan data (Nama|VigenereText|Kunci) lalu di-Base64 agar menjadi Token
    raw_token = f"{nama}|{vigenere_result}|{kunci}"
    token_bytes = raw_token.encode('utf-8')
    secure_token = base64.b64encode(token_bytes).decode('utf-8')
    
    # Buat URL otomatis menuju domain Railway kita sendiri
    base_url = request.url_root
    full_crypto_link = f"{base_url}decrypt_link?token={secure_token}"
    
    # Buat teks pesan otomatis untuk dikirim ke WhatsApp
    wa_text = f"🔒 *BEAR-LOCK SECURE MAIL*\n\nAda pesan rahasia dari *{nama}*.\nKlik link di bawah ini untuk mendekripsi secara otomatis:\n\n{full_crypto_link}"
    wa_api_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_text)}"
    
    return jsonify({
        'token': secure_token,
        'crypto_link': full_crypto_link,
        'wa_link': wa_api_link
    })

# --- 2. API UNTUK DEKRIPSI OTOMATIS LEWAT LINK ---
@app.route('/decrypt_link', methods=['GET'])
def decrypt_link():
    token = request.args.get('token', '')
    if not token:
        return "Token tidak valid atau tidak ditemukan!", 400
        
    try:
        # Bongkar Lapis 2: Decode Base64 Token
        decoded_bytes = base64.b64decode(token.encode('utf-8'))
        decoded_str = decoded_bytes.decode('utf-8')
        
        # Pecah kembali datanya menggunakan pembatas "|"
        nama, vigenere_result, kunci = decoded_str.split('|')
        
        # Bongkar Lapis 1: Kembalikan Vigenere ke Teks Asli
        original_pesan = vigenere_decrypt(vigenere_result, kunci)
        
        # Kirim data hasil bongkaran ke halaman khusus preview
        return render_template('index.html', mode='decrypt', nama=nama, pesan=original_pesan, kunci=kunci)
    except Exception as e:
        return "Gagal mendekripsi data. Token telah rusak atau dimanipulasi!", 400

if __name__ == '__main__':
    app.run(debug=True)