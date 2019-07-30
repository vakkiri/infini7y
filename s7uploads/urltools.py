import re

def strip_get_tags(get_str):
    get_str = re.sub(r'tags=[^&]*?$', '', get_str)
    get_str = re.sub(r'&+?', '&', get_str)
    return get_str

