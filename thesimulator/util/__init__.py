import random
import string


def short_uuid():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
