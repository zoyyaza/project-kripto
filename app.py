from flask import Flask, render_template, request, jsonify
import base64
import urllib.parse

app = Flask(__name__)

# --- FUNGSI KRIPTOR (VIGENERE) ---
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

# --- 1. GENERATE LINK AMAN (TANPA MEMASUKKAN KUNCI DI LINK) ---
@app.route('/generate_link', methods=['POST'])
def generate_link():
    data = request.json
    nama = data.get('nama', '')
    pesan = data.get('pesan', '')
    kunci = data.get('kunci', '')
    
    if not pesan or not kunci:
        return jsonify({'error': 'Pesan dan Kunci wajib diisi'}), 400
        
    # Lapis 1: Enkripsi pesan asli dengan Vigenere
    vigenere_result = vigenere_encrypt(pesan, kunci)
    
    # Lapis 2: Token hanya berisi (Nama Pengirim | Teks Terenkripsi Vigenere) -> KUNCI TIDAK IKUT DIMASUKKAN
    raw_token = f"{nama}|{vigenere_result}"
    secure_token = base64.b64encode(raw_token.encode('utf-8')).decode('utf-8')
    
    base_url = request.url_root
    full_crypto_link = f"{base_url}decrypt_link?token={secure_token}"
    
    wa_text = f"🔒 *BEAR-LOCK SECURE MAIL*\n\nAda pesan rahasia dari *{nama}*.\n\n⚠️ Link ini dilindungi enkripsi.\nSilakan klik tautan di bawah ini dan masukkan Kunci Rahasia yang sudah disepakati untuk membaca isi pesan:\n\n{full_crypto_link}"
    wa_api_link = f"https://api.whatsapp.com/send?text={urllib.parse.quote(wa_text)}"
    
    return jsonify({
        'token': secure_token,
        'wa_link': wa_api_link
    })

# --- 2. HALAMAN TANTANGAN KUNCI & PROSES DEKRIPSI ---
@app.route('/decrypt_link', methods=['GET', 'POST'])
def decrypt_link():
    token = request.args.get('token', '')
    if not token:
        return "Token tidak valid!", 400
        
    try:
        # Bongkar Base64 untuk mengambil nama dan ciphertext-nya
        decoded_str = base64.b64decode(token.encode('utf-8')).decode('utf-8')
        nama, vigenere_result = decoded_str.split('|')
    except:
        return "Token rusak atau dimanipulasi!", 400

    # Jika user baru klik link dari WA (Masih metode GET)
    if request.method == 'GET':
        return render_template('index.html', mode='challenge', nama=nama, token=token)
        
    # Jika user sudah mengetikkan kunci lalu klik tombol "BONGKAR" (Metode POST)
    kunci_input = request.form.get('kunci_input', '')
    
    # Coba dekripsi menggunakan kunci yang diinput user
    original_pesan = vigenere_decrypt(vigenere_result, kunci_input)
    
    # Validasi sederhana: Jika hasilnya hancur atau tidak ada huruf alfabet yang terbaca normal
    # Kita kembalikan mode sukses tapi teksnya berupa kode hancur, atau beri tahu kuncinya salah.
    # Di Vigenere klasik, salah kunci = hasil teksnya jadi karakter acak berantakan.
    return render_template('index.html', mode='success', nama=nama, pesan=original_pesan, kunci=kunci_input)

if __name__ == '__main__':
    app.run(debug=True)