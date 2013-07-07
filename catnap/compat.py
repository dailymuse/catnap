import sys

if sys.version_info >= (3,):
    from io import StringIO
    import urllib.parse as urllib

    _oldbytes = bytes
    bytes = lambda b: _oldbytes(b, "ascii")
    str = str
else:
    try:
        from cStringIO import StringIO
    except:
        from StringIO import StringIO

    import urllib
    bytes = str
    str = unicode
