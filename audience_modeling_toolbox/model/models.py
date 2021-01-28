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
from scipy import special

import itertools
from abc import ABC, abstractmethod

from audience_modeling_toolbox.plotting import _plot_2d_reach

class AbstractADF(ABC):

    @abstractmethod
    def _f_reach(self, grs, freqs) :
        pass

    @abstractmethod
    def _fplus_reach(self, grs, freqs):
        pass

    @abstractmethod
    def _evaluate(self, xs) :
        pass

    def f_reach(self, grs, freqs) :
        """Calculates the reach as a function of frequencies.

        Args:
            grs (numpy ndarray): The gross ratings
            freqs (numpy ndarray): The frequencies

        Returns:
            The reach for each frequency as a numpy array. The arrays is the size of number of freq sets that was asked.
        """

        return np.prod(
            self._f_reach(
                np.reshape(grs,   [-1, 1, self.n_dims]),
                np.reshape(freqs, [1, -1, self.n_dims])
            ),
            axis=2
        )

    def fplus_reach(self, grs, freqs) :
        """Calculates the reach_plus as a function of frequencies.

        Args:
            grs (numpy ndarray): The gross ratings
            freqs (numpy ndarray): The frequencies

        Returns:
            The reach_plus for each frequency as a numpy array. The arrays is the size of number of freq sets that was asked.
        """

        return np.prod(
            self._fplus_reach(
                np.reshape(grs,   [-1, 1, self.n_dims]),
                np.reshape(freqs, [1, -1, self.n_dims])
            ),
            axis=2
        )

    def evaluate(self, xs) :
        """Evaluates the ADF for the given rates

        Args:
            xs (numpy array) : the rates for which to evaluate the ADF.

        Returns:
            The value of the ADF at the specific rates `xs`.
        """

        return self._evaluate(np.reshape(xs, [-1, self.n_dims]))

    def ftrunc_reach(self, grs, max_freq) :
        """Calculates the reach as a function of frequencies in a box. That is for all frequencies from [0, max_freq-1] and calculate the reach_plus for max_freq. This can be used as the values of a dataframe to generate the RFReport.

        Args:
            grs (numpy ndarray): The gross ratings
            max_freq (int): The maximum frequency of the box

        Returns:
            The tuple of (reaches, freqs) that is the rf_dataframe values for the box of [0, max_freq].
        """
        freqs = np.array(list(
            itertools.product(*[range(max_freq+1) for i in range(self.n_dims)])
            ))
        R = self._f_reach(np.reshape(grs, [-1, 1, self.n_dims]),
                          np.reshape(freqs, [1, -1, self.n_dims]))

        R_truncate = self._fplus_reach(np.reshape(grs, [-1, 1, self.n_dims]),
                                       max_freq * np.ones([1, 1, self.n_dims]))
        for n_freq, n_dim in itertools.product(range((max_freq+1)**self.n_dims), range(self.n_dims)) :
            if freqs[n_freq, n_dim] == max_freq :
                for n_gr in range(R.shape[0]) :
                    R[n_gr, n_freq, n_dim] = R_truncate[n_gr, 0, n_dim]

        return np.prod(R, axis=2)

    def plot_2d_reach(self, gr_values, dim_cols, max_freq, population_size, ax=None) :
        """Plot a two dimensional reach surface generated from adf reach function

        Args:
            gr_values (): The gross rating values to plot the reach function with.
            dim_cols (): The two dimensions to keep and plot.
            max_freq (): The maximum frequency to truncate from in the reach surface.
            population_size (): The size of the population to scale the reach function to.
            ax (): axis

        Returns:
            Axis with the reach plotted.
        """

        if self.n_dims != 2 :
            raise Exception("Plotting two dimensional reach is only supported for two dimesional ADFs")

        return _plot_2d_reach(
            (
                self.ftrunc_reach(gr_values, max_freq=max_freq) * population_size
            ).reshape([max_freq+1, max_freq+1]),
            dim_cols, ax=ax
        )

class NormalExponentialADF(AbstractADF) :
    """The class for normalized simple exponential ADF."""

    def __init__(self, gammas, bounds=(1.0e-10, np.inf)) :
        """Creates an instance of a normalized exponential distribution.


        Args:
            gammas (numpy vector): The parameters of the exponential distribution.
            bounds (tuple): The bounds of the variables are by default set between `1.0e-10` and `numpy.inf` (no bound)
        """
        self.n_dims     = len(gammas)
        self.parameters = gammas

        self.bounds     = {
            "lower" : [bounds[0] for i in range(self.n_dims)],
            "upper" : [bounds[1] for i in range(self.n_dims)]
        }

    @property
    def parameters(self) :
        return self._gammas

    @parameters.setter
    def parameters(self, gammas) :
        if not isinstance(gammas, np.ndarray) or gammas.shape != (self.n_dims,) :
            raise Exception("bad input gammas")
        self._gammas = gammas

    def randomize(self, rng=np.random.default_rng(None)) :
        gammas = rng.random(self.n_dims) * 10
        self.parameters = gammas

    def _f_reach(self, grs, freqs) :
        return np.power(self._gammas*grs, freqs) / np.power(1 + self._gammas*grs, freqs + 1)

    def _fplus_reach(self, grs, freqs) :
        return np.power((self._gammas*grs) / (1+ self._gammas*grs), freqs)

    def _evaluate(self, xs) :
        gammas = np.reshape(self._gammas, [1, self.n_dims])
        return np.prod(np.exp(-xs/gammas)/gammas, axis=1)

    def marginal(self, dims) :
        return type(self)(self.parameters[dims])

    def partial_evaluate(self, dims, values) :
        eval_gammas = np.reshape(self._gammas[dims], [1, len(dims)])
        np.prod(np.exp(-values/eval_gammas)/eval_gammas)
        dims_to_marginal = [d for d in list(range(self.n_dims)) if d not in dims]

    def cdf(self, value) :
        if self.n_dims > 1 :
            raise Exception("cdf method is only defined for a single dimension.")

        return 1 - np.exp(-value/self._gammas)

class NormalDeltaADF(AbstractADF) :
    """The class for normalized simple delta function ADF."""

    def __init__(self, positions, bounds=(1.0e-10, np.inf)) :
        """Creates an instance of a normalized delta function distribution.


        Args:
            positions (numpy vector): The parameters of the delta distribution.
            bounds (tuple): The bounds of the variables are by default set between `1.0e-10` and `numpy.inf` (no bound)
        """
        self.n_dims     = len(positions)
        self.parameters = positions

        self.bounds     = {
            "lower" : [bounds[0] for i in range(self.n_dims)],
            "upper" : [bounds[1] for i in range(self.n_dims)]
        }

    @property
    def parameters(self) :
        return self._positions

    @parameters.setter
    def parameters(self, positions) :
        if not isinstance(positions, np.ndarray) or positions.shape != (self.n_dims,) :
            raise Exception("bad input positions")
        self._positions = positions

    def randomize(self, rng=np.random.default_rng(None)) :
        positions = rng.random(self.n_dims) * 10
        self.parameters = positions

    def _f_reach(self, grs, freqs) :
        return np.power(self._positions*grs, freqs) * np.exp(-self._positions * grs) / special.gamma(freqs + 1)

    def _fplus_reach(self, grs, freqs) :
        return 1 - special.gammaincc(freqs, self._positions*grs)

    def _evaluate(self, xs) :
        pass
