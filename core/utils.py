import hashlib
from django.conf import settings


def generate_token(file_id):
    secret = settings.SECRET_KEY
    data = f"{file_id}{secret}"
    return hashlib.sha256(data.encode()).hexdigest()