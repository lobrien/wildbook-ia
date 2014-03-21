from __future__ import division, print_function
import hashlib
from .util_inject import inject
print, print_, printDBG, rrr, profile = inject(__name__, '[hash]')


def hashstr_arr(arr, lbl='arr', **kwargs):
    if isinstance(arr, list):
        arr = tuple(arr)
    if isinstance(arr, tuple):
        arr_shape = '(' + str(len(arr)) + ')'
    else:
        arr_shape = str(arr.shape).replace(' ', '')
    arr_hash = hashstr(arr, **kwargs)
    arr_uid = ''.join((lbl, '(', arr_shape, arr_hash, ')'))
    return arr_uid


def hashstr(data, trunc_pos=8):
    if isinstance(data, tuple):
        data = repr(data)
    # Get a 128 character hex string
    hashstr = hashlib.sha512(data).hexdigest()
    # Convert to base 57
    hashstr2 = hex2_base57(hashstr)
    # Truncate
    hashstr = hashstr2[:trunc_pos]
    return hashstr


#def valid_filename_ascii_chars():
    ## Find invalid chars
    #ntfs_inval = '< > : " / \ | ? *'.split(' ')
    #other_inval = [' ', '\'', '.']
    ##case_inval = map(chr, xrange(97, 123))
    #case_inval = map(chr, xrange(65, 91))
    #invalid_chars = set(ntfs_inval + other_inval + case_inval)
    ## Find valid chars
    #valid_chars = []
    #for index in xrange(32, 127):
        #char = chr(index)
        #if not char in invalid_chars:
            #print index, chr(index)
            #valid_chars.append(chr(index))
    #return valid_chars
#valid_filename_ascii_chars()
ALPHABET = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9',  'a', 'b', 'c',
            'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
            'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', ';', '=', '@',
            '[', ']', '^', '_', '`', '{', '}', '~', '!', '#', '$', '%', '&',
            '+', ',']

BIGBASE = len(ALPHABET)


def hex2_base57(hexstr):
    x = int(hexstr, 16)
    if x == 0:
        return '0'
    sign = 1 if x > 0 else -1
    x *= sign
    digits = []
    while x:
        digits.append(ALPHABET[x % BIGBASE])
        x //= BIGBASE
    if sign < 0:
        digits.append('-')
        digits.reverse()
    newbase_str = ''.join(digits)
    return newbase_str


def hashstr_md5(data):
    hashstr = hashlib.md5(data).hexdigest()
    #bin(int(my_hexdata, scale))
    return hashstr
