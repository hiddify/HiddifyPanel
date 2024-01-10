from hiddifypanel import hutils
from slugify import slugify


def fill_username(model) -> None:
    if model.username:
        return
    base_username = model.name or ''
    minimum_username_length = 10

    if len(base_username) < minimum_username_length:
        base_username += hutils.utils.get_random_string(minimum_username_length-len(base_username), minimum_username_length)

    if len(base_username) > 100:
        base_username = base_username[0:100]
    model.username = base_username

    while not model.is_username_unique():
        rand_str = hutils.utils.get_random_string(2, 4)
        model.username += rand_str


def fill_password(model) -> None:
    # TODO: hash the password
    if not model.password or len(model.password) < 16:
        model.password=hutils.utils.get_random_password(length = 16)
