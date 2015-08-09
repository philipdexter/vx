from unicodedata import category

def is_printable(key):
    if isinstance(key, bytes):
        key = key.decode('utf8')
    try:
        if category(key)[0] != 'C':
            return True
    except UnicodeDecodeError:
        pass
    return False
