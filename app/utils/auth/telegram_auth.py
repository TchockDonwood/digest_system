import hashlib
import hmac
import time


# Проверяем хэш, который нам прислали и который мы получили от Telegram
def verify_telegram_auth(data: dict, bot_token: str):
    data = data.copy()

    telegram_hash = data.pop("hash") # Telegram просит присылать данные без хэша
    
    # Формируем строку, которую требует Telegram
    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(data.items())
        if value is not None
    )
    
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return calculated_hash == telegram_hash


# Проверяем, чтобы авторизация не устарела
def validate_auth_date(auth_date: int, max_age: int = 86400):
    now = int(time.time())
    
    if int(now) - int(auth_date) > max_age:
        return False
    return True
