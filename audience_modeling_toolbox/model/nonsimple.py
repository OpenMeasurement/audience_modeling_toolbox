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
import pandas as pd
import scipy
from scipy.optimize import least_squares

import itertools
import warnings

from audience_modeling_toolbox.model.models import AbstractADF, NormalExponentialADF, NormalDeltaADF
from audience_modeling_toolbox.measure import VirtualSociety

class MixtureADF(AbstractADF) :
    """Generic class for mixture of simple normalized ADFs

    """

    def __init__(self, amplitudes, simple_adfs, normalize=True) :
        """
        Args:
            amplitudes (list of floats) : amplitudes of each simple ADFs.
            simple_adfs (list of ADFs) : The list of ADFS.
        """
        if len(amplitudes) != len(simple_adfs) :
            raise Exception("The number of amplitudes and adfs don't match.")

        n_dims = simple_adfs[0].n_dims
        adf_n_dims = [adf.n_dims == n_dims for adf in simple_adfs]

        if not all(adf_n_dims) :
            raise Exception(f"The dimensions of simple_adfs do not match: {adf_n_dims}")

        self.n_dims = n_dims
        self.n_simples   = len(amplitudes)
        self.amplitudes  = amplitudes
        self.simple_adfs = simple_adfs

        if not np.isclose(np.sum(amplitudes), 1.0) and normalize :
            warnings.warn("The amplitudes are not normalized, normalizing them ...")
            self.normalize()

    @property
    def amplitudes(self):
        return self._amplitudes

    @amplitudes.setter
    def amplitudes(self, amplitudes) :
        if not isinstance(amplitudes, np.ndarray) \
           or amplitudes.shape != (self.n_simples,):
            raise Exception(f"Invalid amplitudes {amplitudes}")
        self._amplitudes = amplitudes

    @property
    def parameters(self) :
        return np.hstack([
            simple_adf.parameters for simple_adf in self.simple_adfs
        ]).flatten()

    @parameters.setter
    def parameters(self, parameters) :
        index = 0
        for simple_adf in self.simple_adfs :
            n = len(simple_adf.parameters)
            simple_adf.parameters = parameters[index: index+n]
            index += n

    def randomize(self, rng=np.random.default_rng(None)) :
        """Randomize the paramters of the mixture ADF."""
        amplitudes = rng.random(self.n_simples)
        amplitudes.sort()
        self.amplitudes = np.flip(amplitudes) / np.sum(amplitudes)

        for simple_adf in self.simple_adfs :
            simple_adf.randomize(rng)

    def normalize(self) :
        """Normalize the amplitude of the mixture of ADFs to sum up to 1."""
        self.amplitudes = self.amplitudes/np.sum(self.amplitudes)
        return self

    ### TODO: the below three functions are all linear. Can they be merged into one?
    def _f_reach(self, grs, freqs) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf._f_reach(grs, freqs) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

    def _fplus_reach(self, grs, freqs) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf._fplus_reach(grs, freqs) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

    def ftrunc_reach(self, grs, max_freq) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf.ftrunc_reach(grs, max_freq) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
            )

    def _evaluate(self, xs) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf._evaluate(xs) for simple_adf in self.simple_adfs]),
            axes = ([0], [0])
        )

    def _parameters_bounds(self, which="upper") :
        bounds = []
        for simple_adf in self.simple_adfs :
            bounds = bounds + simple_adf.bounds[which]

        return bounds

    def _residuals(self, reports, ps_vector, what="reach_truncate") :
        n = self.n_simples
        self.amplitudes = np.array(ps_vector[:n])
        self.parameters = np.array(ps_vector[n:])

        residuals = []
        for report in reports :
            reaches, freqs = report.reach_freq_values(normalized=True, max_freq=report.max_freq)
            grs            = report.gr_values
            ## NOTE: It is assumed that the ftrunc_reach returns frequencies in the itertools.product order...
            residuals.append(reaches - self.ftrunc_reach(grs, report.max_freq))

        return np.array(residuals).flatten()

    def train(self, *reports, what="reach_truncate") :
        """trains the mixture ADF against a set of `reports`

        Args:
            reports: The reports used to train the
        """
        old_amplitudes = self.amplitudes
        old_parameters = self.parameters

        residual_fn = lambda xs : self._residuals(reports, xs, what=what)

        x0  = [*self.amplitudes, *self.parameters]

        bounds = ([1.0e-5] * self.n_simples + self._parameters_bounds(which="lower"),
                  [1.0]    * self.n_simples + self._parameters_bounds(which="upper"))

        print(x0)
        print(bounds)
        try:
            result = least_squares(residual_fn, x0=x0, bounds=bounds, max_nfev=5000)

            xs = result.x
            #print("xs", xs)

        except Exception as e:
            #print(e)
            self.amplitudes = old_amplitudes
            self.parameters = old_parameters
            raise Exception("Even one exp didn't fit!")

    def marginal(self, dims):
        """The marginal distribution of the ADF.

        Args:
            dims (list of int) : The indices of the dimensions to keep for the marginal

        Returns:
            The marginal ADF of the same kind.
        """

        return type(self)(
            self.amplitudes,
            [simple_adf.marginal(dims=dims) for simple_adf in self.simple_adfs]
        )

    def conditional(self, dims, values) :
        dims_unconditioned = [d for d in range(self.n_dims) if d not in dims]
        amplitude_factors = np.array([simple_adf.marginal(dims).evaluate(values) for simple_adf in self.simple_adfs]).flatten()
        factor = np.sum(amplitude_factors)
        return type(self)(
            self.amplitudes * amplitude_factors/factor,
            [simple_adf.marginal(dims=dims_unconditioned) for simple_adf in self.simple_adfs]
        )

    def cdf(self, X) :
        return np.tensordot(
            self.amplitudes,
            np.array([simple_adf.cdf(X) for simple_adf in self.simple_adfs]),
            axes=([0], [0])
        )

    def sample(self, uniform_sample) :
        """sample the ADF using a given uniform sampling

        Args:
            uniform_sample (numpy array) : a sample of numbers from uniform distribution of [0, 1)

        Returns:
            The corresponding sample (to the input sample that was chosen from uniform) from the ADF.
        """

        rs = np.array([uniform_sample]) if np.isscalar(uniform_sample) else np.array(uniform_sample)
        if rs.shape[-1] != self.n_dims :
            raise Exception("dimensions don't match!")

        res = np.zeros(self.n_dims)
        if self.n_dims == 1 :
            res[0] = scipy.optimize.root(lambda X: self.cdf(X) - rs[0], 0.0).x[0]
        else :
            res[0] = self.marginal(dims=[0]).sample(rs[0])
            res[1:] = self.conditional(dims=[0], values=rs[0]).sample(rs[1:])

        return res

    def generate_virtual_society(self, population_size, media_cols, id_col="vid", mode="random") :
        """Generates a virtual society that follows the ADF.

        Args:
            population_size (int) : the size of the virtual population.
            media_cols (list of string) : the list of media labels.
        """

        if self.n_dims != len(media_cols) :
            raise Exception(f"Number of media lables {media_cols} don't match the dimension.")

        if mode == "uniform" :
            Ns = np.ceil(np.power(population_size, 1/len(media_cols))).astype('int') * np.ones(len(media_cols), dtype='int')
            xs = [np.linspace(1/(N+1), 1, N+1)[:-1] for N in Ns]
            uniform_samples = np.array(list(itertools.product(*xs)))

        elif mode == "random" :
            uniform_samples = np.random.random([population_size, len(media_cols)])


        activities = np.array([
            self.sample(uniform_samples[i, :])
            for i in range(population_size)
        ])

        ## TODO: Document the normalization of activities in more detail
        #normalizing activities
        factors = np.reshape(np.sum(activities, axis=0) / population_size, [1, -1])
        activities = activities / factors

        dataframe = pd.concat([
            pd.DataFrame(np.arange(population_size, dtype='int'), columns=[id_col]),
            pd.DataFrame(activities, columns=media_cols)
        ], axis=1)

        return VirtualSociety(dataframe, media_cols=media_cols, id_col=id_col)

class MixtureOfExponentials(MixtureADF) :
    """Class for mixture of exponential ADFs."""

    def __init__(self, amplitudes, simple_adfs) :
        for simple_adf in simple_adfs :
            if not isinstance(simple_adf, NormalExponentialADF) :
                raise Exception("A MixtureOfExponentials only accepts NormalExponentialADF as simple adfs")
        super().__init__(amplitudes, simple_adfs)

    @classmethod
    def random(cls, n_exps, n_dims, rng=np.random.default_rng(None)) :
        """Generate a random instance of mixture of exponentials.

        Args:
            n_exps (int): Number of exponential distributions.
            n_dims (int): The dimension of space each exponential distribution lives on.
            rng : The random number generator (default np.random.default_rng(None))

        """
        o = cls.ones(n_exps, n_dims)
        o.randomize(rng)
        return o

    @classmethod
    def ones(cls, n_exps, n_dims) :
        """Generate an eqaul amplitude instance of mixture of exponentials with all paramters set to 1.0.

        Args:
            n_exps (int): Number of exponential distributions.
            n_dims (int): The dimension of space each exponential distribution lives on.

        """
        amplitudes = np.ones(n_exps) / n_exps
        simple_adfs = []
        for i in range(n_exps) :
            simple_adfs.append(NormalExponentialADF(gammas=np.ones(n_dims)))

        return cls(amplitudes, simple_adfs)

class MixtureOfDeltas(MixtureADF) :
    """Class for mixture of delta ADFs."""

    def __init__(self, amplitudes, simple_adfs) :
        for simple_adf in simple_adfs :
            if not isinstance(simple_adf, NormalDeltaADF) :
                raise Exception("A MixtureOfDeltass only accepts NormalDeltaADF as simple adfs")
        super().__init__(amplitudes, simple_adfs)

    @classmethod
    def random(cls, n_deltas, n_dims, rng=np.random.default_rng(None)) :
        """Generate a random instance of mixture of deltas.

        Args:
            n_deltass (int): Number of delta distributions.
            n_dims (int): The dimension of space each delta distribution lives on.
            rng : The random number generator (default np.random.default_rng(None))

        """
        o = cls.ones(n_deltas, n_dims)
        o.randomize(rng)
        return o

    @classmethod
    def ones(cls, n_deltas, n_dims) :
        """Generate an eqaul amplitude instance of mixture of deltas with all paramters set to 1.0.

        Args:
            n_deltas (int): Number of delta distributions.
            n_dims (int): The dimension of space each delta distribution lives on.

        """
        amplitudes = np.ones(n_deltas) / n_deltas
        simple_adfs = []
        for i in range(n_deltas) :
            simple_adfs.append(NormalDeltaADF(positions=np.ones(n_dims)))

        return cls(amplitudes, simple_adfs)
