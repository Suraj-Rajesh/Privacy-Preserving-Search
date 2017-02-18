from Crypto.Cipher import AES
from Crypto import Random
from base64 import b64encode
from  hashlib import sha256

AES_BS = 16

pad = lambda data: data + (AES_BS - len(data) % AES_BS) * chr(AES_BS - len(data) % AES_BS)
unpad = lambda data : data[:-ord(data[len(data)-1:])]

def generate_aes_key():
    passphrase = input("Enter AES passphrase: ")
    save_directory = input("Directory to save the key(relative or absolute): ")
    if save_directory[-1] != '/':
        save_directory = save_directory + "/"
    name_of_the_key = input("Name of the key: ")
    aes_key = sha256(passphrase.encode()).digest()
    print(len(aes_key))
    return aes_key

def aes_encrypt(plain_data, aes_key):
    plain_data = pad(plain_data)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return b64encode(iv + cipher.encrypt(plain_data))

def aes_decrypt(encrypted_data, aes_key):
    encrypted_data = base64.b64decode(encrypted_data)
    iv = encrypted_data[:16]
    cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data[16:]))
