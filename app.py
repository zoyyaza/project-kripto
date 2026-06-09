# --- FUNGSI KRIPTOR VIGENERE UPGRADE (MENGACAK SEMUA KARAKTER TERMASUK SPASI) ---
def vigenere_encrypt(plaintext, key):
    cipher_text = []
    # Mengacak menggunakan jangkauan karakter ASCII dapat diketik (32 sampai 126)
    # Total ada 95 karakter unik (termasuk spasi, angka, dan simbol)
    for i, char in enumerate(plaintext):
        char_code = ord(char)
        if 32 <= char_code <= 126:
            shift = ord(key[i % len(key)])
            # Rumus pergeseran total karakter printable ASCII
            new_code = 32 + ((char_code - 32 + shift) % 95)
            cipher_text.append(chr(new_code))
        else:
            cipher_text.append(char)
    return "".join(cipher_text)

def vigenere_decrypt(ciphertext, key):
    plain_text = []
    for i, char in enumerate(ciphertext):
        char_code = ord(char)
        if 32 <= char_code <= 126:
            shift = ord(key[i % len(key)])
            # Rumus membalikkan pergeseran printable ASCII
            new_code = 32 + ((char_code - 32 - shift) % 95)
            plain_text.append(chr(new_code))
        else:
            plain_text.append(char)
    return "".join(plain_text)