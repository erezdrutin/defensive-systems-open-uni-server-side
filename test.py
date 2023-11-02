from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import binascii


def decrypt_aes_cbc(encrypted_hex, key_bytes):
    # Convert hex to bytes for the encrypted message
    encrypted_bytes = binascii.unhexlify(encrypted_hex)

    # Extract IV and ciphertext
    iv = encrypted_bytes[:16]
    ciphertext = encrypted_bytes[16:]

    # Decrypt using AES CBC
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    decrypted_bytes = unpad(cipher.decrypt(ciphertext), AES.block_size)

    return decrypted_bytes.decode('utf-8')


if __name__ == "__main__":
    encrypted_message = "71d1ab4205d488817a8b22f0928c190966c8d8f3f49a83cf2b64d3350573d1da"
    key_bytes = b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F"

    decrypted_message = decrypt_aes_cbc(encrypted_message, key_bytes)
    print("Decrypted Message:", decrypted_message)
