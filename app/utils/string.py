import string
import random


def gen_random_string(le: int) -> str:
    text = string.digits + string.ascii_lowercase + string.ascii_uppercase + string.punctuation
    return ''.join([random.choice(text) for _ in range(le)])
