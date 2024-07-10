import base64
from typing import Tuple, Any
from uuid import UUID


def is_uuid_valid(uuid: str, version: int = 4) -> bool:
    try:
        uuid_obj = UUID(uuid, version=version)
    except Exception:
        return False
    return str(uuid_obj) == uuid


def get_uuid_from_url_path(path: str, section_index: int = 2) -> str | None:
    """
    Takes a URL path and extracts the UUID at the specified section index.

    Args:
        path (str): The URL path from which to extract the UUID.
        section_index (int, optional): The index of the section in the URL path where the UUID is located. Defaults to 2, because in past the UUID was in the second section of path of url.

    Returns:
        str | None: The extracted UUID as a string if found, or None if not found.
    """
    s_index = 1
    for section in path.lstrip('/').split('/'):
        if is_uuid_valid(section, 4):
            if s_index == section_index:
                return section
        s_index += 1
    return None


def parse_login_id(raw_id: str) -> Tuple[Any | None, str | None]:
    """
    Parses the given raw ID to extract the account type and ID.
    Args:
        raw_id (str): The raw ID to be parsed.
    Returns:
        Tuple[Any | None, str | None]: A tuple containing the account type and ID.
            The account type is either AccountType.admin or AccountType.user
            and the ID is a string. If the raw ID cannot be parsed, None is returned
            for both the account type and ID.
    """
    splitted = raw_id.split('_')
    if len(splitted) < 2:
        return None, None
    admin_or_user, id = splitted
    from hiddifypanel.models.role import AccountType
    account_type = AccountType.admin if admin_or_user == 'admin' else AccountType.user
    if not id or not account_type:
        return None, None
    return account_type, id


def add_basic_auth_to_url(url: str, username: str, password: str) -> str:
    if 'https://' in url:
        return url.replace('https://', f'https://{username}:{password}@')
    elif 'http://' in url:
        return url.replace('http://', f'http://{username}:{password}@')
    else:
        return url

# region unused(never mentioned in codebase)


# def is_uuid_in_url_path(path: str) -> bool:
#     for section in path.split('/'):
#         if is_uuid_valid(section, 4):
#             return True
#     return False


# def get_basic_auth_from_auth_header(auth_header: str) -> str | None:
#     if auth_header.startswith('Basic'):
#         return auth_header.split('Basic ')[1].strip()
#     return None


# def parse_basic_auth_header(auth_header: str) -> tuple[str, str] | None:
#     if not auth_header.startswith('Basic'):
#         return None
#     header_value = auth_header.split('Basic ')
#     if len(header_value) < 2:
#         return None
#     username, password = map(lambda item: item.strip(), base64.urlsafe_b64decode(header_value[1].strip()).decode('utf-8').split(':'))
#     return (username, password) if username and password else None
# endregion
