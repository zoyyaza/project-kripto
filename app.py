from flask import Flask, render_template, request, redirect
import os
import base64
import urllib.parse

app = Flask(__name__)

# RUMUS ENKRIPSI LAPIS 1: VIGENERE ASCII
def vigenere_encrypt(plaintext, key):
    ciphertext = ""
    key_length = len(key)
    for i, char in enumerate(plaintext):
        c_ascii = (ord(char) + ord(key[i % key_length])) % 256
        ciphertext += chr(c_ascii)
    return ciphertext

# RUMUS ENKRIPSI LAPIS 2: BASE64
def double_layer_encrypt(plaintext, key):
    vigenere_result = vigenere_encrypt(plaintext, key)
    # Mengubah hasil vigenere menjadi teks Base64 yang rapi
    bytes_result = vigenere_result.encode('utf-8', errors='surrogateescape')
    base64_result = base64.b64encode(bytes_result).decode('utf-8')
    return base64_result

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nama = request.form.get('nama', 'Anonim')
        pesan = request.form.get('pesan', '')
        kunci = request.form.get('kunci', 'BEAR')
        
        # Jalankan enkripsi dua lapis
        hasil_rahasia = double_layer_encrypt(pesan, kunci)
        
        # Susun teks rahasia untuk dikirim ke WhatsApp
        teks_wa = (
            f"🧸 *TUGAS UAS KRIPTOGRAFI* 🧸\n\n"
            f"*Nama Pengirim:* {nama}\n"
            f"*Pesan Asli:* {pesan}\n"
            f"*Kunci Rahasia:* {kunci}\n"
            f"*Hasil Enkripsi (Double Layer):* {hasil_rahasia}\n"
        )
        
        # Encode teks agar bisa dibaca oleh link WhatsApp
        teks_encoded = urllib.parse.quote(teks_wa)
        
        # Langsung alihkan halaman ke WhatsApp!
        return redirect(f"https://api.whatsapp.com/send?text={teks_encoded}")
        
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)