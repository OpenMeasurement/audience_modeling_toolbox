# MIT License

# Copyright (c) 2021 OpenMeasurement

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
import matplotlib
import matplotlib.pyplot as plt

def _log_colormap(x, vmin, vmax, cmap=matplotlib.cm.viridis) :
    norm = matplotlib.colors.LogNorm(vmin=vmin, vmax=vmax)
    return cmap(norm(x))

def _freq_ticks(max_freq=20, jump=2) :
    tickrange = range(0, max_freq+1, jump)
    ticklabels = [str(i) for i in range(0, max_freq, jump)]
    ticklabels[-1] = ticklabels[-1] + "+"
    return tickrange, ticklabels

def _plot_1d_reach(data, dim, ax) :
    if ax is None:
        fig, ax = plt.subplots()

    data_size = len(data)
    tickrange, ticklabels = _freq_ticks(max_freq=data_size, jump=2)

    ax.bar(np.arange(data_size), data,
           color=[_log_colormap(v, vmin=1, vmax=np.max(data)) for v in data])
    ax.set_xlabel(dim)
    ax.set_ylabel("Reach")
    ax.set_yscale("log")
    ax.set_xticks(tickrange)
    ax.set_xticklabels(ticklabels)

    return ax

def _plot_2d_reach(data, dims, ax=None) :

    if ax is None:
        fig, ax = plt.subplots()

    data_size = data.shape[0]
    tickrange, ticklabels = _freq_ticks(max_freq=data_size, jump=2)

    vmax = np.max(data)
    im = ax.imshow(data,
                   norm=matplotlib.colors.LogNorm(
                       vmin=1,
                       vmax=vmax
                   ),
                   origin="lower"
    )
    ax.set_ylabel(dims[0])
    ax.set_xlabel(dims[1])

    ax.set_xticks(tickrange)
    ax.set_xticklabels(ticklabels)
    ax.set_yticks(tickrange)
    ax.set_yticklabels(ticklabels)

    plt.gcf().colorbar(im, ax=ax)

    return ax
