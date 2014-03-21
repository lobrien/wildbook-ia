from __future__ import division, print_function
import numpy as np
from .util_inject import inject
print, print_, printDBG, rrr, profile = inject(__name__, '[alg]')


def normalize(array, dim=0):
    return norm_zero_one(array, dim)


def norm_zero_one(array, dim=0):
    'normalizes a numpy array from 0 to 1'
    array_max  = array.max(dim)
    array_min  = array.min(dim)
    array_exnt = np.subtract(array_max, array_min)
    return np.divide(np.subtract(array, array_min), array_exnt)


def find_std_inliers(data, m=2):
    return abs(data - np.mean(data)) < m * np.std(data)


def choose(n, k):
    import scipy.misc
    return scipy.misc.comb(n, k, True)


def cartesian(arrays, out=None):
    '''
    Generate a cartesian product of input arrays.

    Parameters
    ----------
    arrays : list of array-like
        1-D arrays to form the cartesian product of.
    out : ndarray
        Array to place the cartesian product in.
    Returns
    -------
    out : ndarray
        2-D array of shape (M, len(arrays)) containing cartesian products
        formed of input arrays.
    Examples
    --------
    >>> cartesian(([1, 2, 3], [4, 5], [6, 7]))
    array([[1, 4, 6], [1, 4, 7], [1, 5, 6], [1, 5, 7],
           [2, 4, 6], [2, 4, 7], [2, 5, 6], [2, 5, 7],
           [3, 4, 6], [3, 4, 7], [3, 5, 6], [3, 5, 7]])
    '''
    arrays = [np.asarray(x) for x in arrays]
    dtype = arrays[0].dtype

    n = np.prod([x.size for x in arrays])
    if out is None:
        out = np.zeros([n, len(arrays)], dtype=dtype)
    m = n // arrays[0].size
    out[:, 0] = np.repeat(arrays[0], m)
    if arrays[1:]:
        cartesian(arrays[1:], out=out[0:m, 1:])
        for j in xrange(1, arrays[0].size):
            out[j * m:(j + 1) * m, 1:] = out[0:m, 1:]
    return out


def almost_eq(a, b, thresh=1E-11):
    return abs(a - b) < thresh
