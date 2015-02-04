#coding: utf-8
# The contents of this file are subject to the Python Software Foundation
# License Version 2.3 (the License).  You may not copy or use this file, in
# either source code or executable form, except in compliance with the License.
# You may obtain a copy of the License at http://www.python.org/license.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Petru Paler

# Minor modifications made by Andrew Resch to replace the BTFailure errors with Exceptions

import logging
log = logging.getLogger(__name__)

def decode_int(x, f):
    f += 1
    newf = x.index('e', f)
    n = int(x[f:newf])
    if x[f] == '-':
        if x[f + 1] == '0':
            raise ValueError
    elif x[f] == '0' and newf != f+1:
        raise ValueError
    return (n, newf+1)

def decode_string(x, f):
    colon = x.index(':', f)
    n = int(x[f:colon])
    if x[f] == '0' and colon != f+1:
        raise ValueError
    colon += 1
    return (x[colon:colon+n], colon+n)

def decode_list(x, f):
    r, f = [], f+1
    while x[f] != 'e':
        v, f = decode_func[x[f]](x, f)
        r.append(v)
    return (r, f + 1)

def decode_dict(x, f):
    r, f = {}, f+1
    while x[f] != 'e':
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f]](x, f)
    return (r, f + 1)

decode_func = {}
decode_func['l'] = decode_list
decode_func['d'] = decode_dict
decode_func['i'] = decode_int
decode_func['0'] = decode_string
decode_func['1'] = decode_string
decode_func['2'] = decode_string
decode_func['3'] = decode_string
decode_func['4'] = decode_string
decode_func['5'] = decode_string
decode_func['6'] = decode_string
decode_func['7'] = decode_string
decode_func['8'] = decode_string
decode_func['9'] = decode_string

def bdecode(x):
    try:
        r, l = decode_func[x[0]](x, 0)
    except (IndexError, KeyError, ValueError):
        raise Exception("not a valid bencoded string")

    return r

class Bencached(object):

    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s

def encode_bencached(x, r):
    r.append(x.bencoded.encode())

def encode_int(x, r):
    r.extend((b'i', str(x).encode(), b'e'))

def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)

def encode_string(x, r):
    r.extend((str(len(x)).encode(), b':', x))

def encode_utf8(x, r):
    x = x.encode('utf-8')
    r.extend((str(len(x)).encode(), b':', x))

def encode_list(x, r):
    r.append(b'l')
    for i in x:
        encode_func[type(i)](i, r)
    r.append(b'e')

def encode_dict(x, r):
    r.append(b'd')
    ilist = x.items()
    ilist = sorted(ilist)
    for k, v in ilist:
        r.extend((str(len(k)).encode(), b':', k.encode()))
        encode_func[type(v)](v, r)
    r.append(b'e')

encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[int] = encode_int
encode_func[int] = encode_int
encode_func[bytes] = encode_string
encode_func[str] = encode_utf8
encode_func[list] = encode_list
encode_func[tuple] = encode_list
encode_func[dict] = encode_dict
encode_func[bool] = encode_bool

def bencode(x):
    r = []
    encode_func[type(x)](x, r)
    return b''.join(r)
