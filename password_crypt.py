import bcrypt

def verify_password(password=None, hashed_password=None):
    hashed_bytes_password = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    return bcrypt.checkpw(password.encode('utf-8'), hashed_bytes_password)

