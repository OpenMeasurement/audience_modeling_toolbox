# MIT License

# Copyright (c) 2020 OpenMeasurement

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np

def _reshape_grs(grs, n_dims) :
    "reshapes/broadcast the grs to the three dimensional of (n_grs, n_freqs, n_dims) for reach/frequency functions."
    n_grs = 0

    shape = np.array(grs).shape
    if len(shape) == 0 :
        if n_dims == 1 :
            n_grs = 1

    elif len(shape) == 1 :
        if n_dims == 1:
            n_grs = len(grs)

        elif n_dims == len(grs) :
            n_grs = 1

    elif len(shape) == 2 :
        if n_dims == shape[1] :
            n_grs = shape[0]

    if n_grs > 0:
        return np.reshape(grs, [n_grs, 1, n_dims])

    raise Exception(f"invalid grs of shape {grs.shape} with n_dims {n_dims}")

def _reshape_grs_freqs(grs, freqs, n_dims) :
    "reshapes/broadcast the grs to the three dimensional of (n_grs, n_freqs, n_dims) for the reach/frequency functions."

    n_grs, n_freqs = 0, 0

    shape = np.array(grs).shape
    if len(shape) == 0 :
        if n_dims == 1 :
            n_grs = 1
            n_freqs = len(freqs)

    elif len(shape) == 1 :
        if n_dims == 1:
            n_grs = len(grs)
            n_freqs = len(freqs)

        elif n_dims == len(grs) :
            if freqs.shape == 2:
                n_grs = 1
                n_freqs = freqs.shape[0]

    elif len(shape) == 2 :
        if n_dims == shape[1] and freqs.shape == 2 and freqs.shape[1] == n_dims:
            n_grs = shape[0]
            n_freqs = freqs.shape[0]

    if n_grs > 0 and n_freqs > 0:
        return np.reshape(grs, [n_grs, 1, n_dims]), np.reshape(freqs, [1, n_freqs, n_dims])

    raise Exception(f"invalid grs of shape {grs.shape} and freqs of shape {freqs.shape} with n_dims {n_dims}")
