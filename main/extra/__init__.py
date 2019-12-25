"""Mark as module for PyTest."""

def left(string, seq=(' ', '\t', '\r', '\n')):
    res = ""
    for c in string:
        if c in seq:
            res += c
        else:
            break
    return res

def right(string, seq=(' ', '\t', '\r', '\n')):
    return left(reversed(string), seq)
