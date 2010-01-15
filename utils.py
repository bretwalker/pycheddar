import re


def to_underscores(key):
    """Utility method to convert a camel-cased key (like what is generally used in CheddarGetter)
    to an underscored key (like what is generally used in Python)."""
    
    match = re.search(r'([A-Z])', key)
    while match:
        char = match.groups()[0]
        key = key.replace(char, '_' + char.lower())
        match = re.search(r'([A-Z])', key)
    
    return key
    
    
def to_camel_case(key):
    """Convert an underscored key (like what is generally used in Python code)
    to a camel-cased key (like what is generally used in CheddarGetter)."""
    
    while '_' in key:
        ix = key.index('_')
        next = key[ix + 1].upper()
        key = key[0:ix] + next + key[ix + 2:]
        
    return key