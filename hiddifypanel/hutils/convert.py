def is_int(input: str) -> bool:
    try:
        int(input)
        return True
    except:
        return False


def to_int(s: str) -> int:
    '''Returns 0 if <s> is not a number'''
    try:
        return int(s)
    except:
        return 0
