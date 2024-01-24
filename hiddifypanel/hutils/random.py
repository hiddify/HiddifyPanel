import random
import string


def get_random_string(min_=10, max_=30):
    # With combination of lower and upper case
    length = random.randint(min_, max_)
    characters = string.ascii_letters + string.digits
    result_str = ''.join(random.choice(characters) for i in range(length))
    return result_str


def get_random_password(length: int = 16) -> str:
    '''Retunrns a random password with fixed length'''
    characters = string.ascii_letters + string.digits  # + '-'
    while True:
        passwd = ''.join(random.choice(characters) for i in range(length))
        if (any(c.islower() for c in passwd) and any(c.isupper() for c in passwd) and sum(c.isdigit() for c in passwd) > 1):
            return passwd
