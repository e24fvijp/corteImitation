from cryptography.fernet import Fernet
import os
import base64

def generate_key():
    """暗号化キーを生成"""
    return Fernet.generate_key()

def encrypt_env_file(key, input_file='.env', output_file='APIs/.env.encrypted'):
    if not os.path.exists('APIs'):
        os.makedirs('APIs')
    """.envファイルを暗号化"""
    # 暗号化キーをファイルに保存
    with open('APIs/key.key', 'wb') as key_file:
        key_file.write(key)
    
    # .envファイルの内容を読み込み
    with open(input_file, 'rb') as file:
        env_data = file.read()
    
    # 暗号化
    f = Fernet(key)
    encrypted_data = f.encrypt(env_data)
    
    # 暗号化されたデータを保存
    with open(output_file, 'wb') as file:
        file.write(encrypted_data)
    
    print(f"暗号化が完了しました。暗号化キーは 'key.key' に保存されています。")
    print(f"暗号化された.envファイルは '{output_file}' に保存されています。")

if __name__ == "__main__":
    key = generate_key()
    encrypt_env_file(key) 