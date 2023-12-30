
'''This file isn't a model, it's just an enum for roles'''
from strenum import StrEnum


class Role(StrEnum):
    super_admin = "super_admin"
    admin = "admin"
    agent = "agent"
    user = "user"


class AccountType(StrEnum):
    admin = "admin"
    user = "user"
