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

import matplotlib
import matplotlib.pyplot as plt

def _plot_2d_reach(data, dims, ax=None) :

    if ax is None:
        fig, ax = plt.subplots()

    data_size = data.shape[0]
    freq_label_jump = 2
    tickrange = range(0, data_size+1, freq_label_jump)
    ticklabels = [str(i) for i in range(0, 21, freq_label_jump)]
    ticklabels[-1] = ticklabels[-1] + "+"

    im = ax.imshow(data,
                   norm=matplotlib.colors.LogNorm(),
                   vmin=1,
                   vmax=2.e3,
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
