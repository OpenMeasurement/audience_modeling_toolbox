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

from abc import ABC, abstractmethod
import itertools
import warnings

class AbstractRFReport(ABC) :
    """Abstract class for reach and frequency (RF) reports

    """

    @property
    @abstractmethod
    def gr_values(self):
        pass


class RFReport(AbstractRFReport) :
    """The class for the reach-frequency reports from a Pandas dataframe."""

    def __init__(self, dataframe, max_freq, dim_cols, reach_col="REACH", population_size=None):
        """Construct a RFReport from a report pandas dataframe.

        Args:
            dataframe (int): The reach and frequency Pandas dataframe. It is assumed to have complete information on the reach and frequency, that means  all the observed frequencies for each dimensions is present in the table, i.e. it is not trimmed.
            max_freq (int): The max_freq allowed in the dataframe, all higher frequencies will be
            dim_cols (list of str): The label for frequency dimension columns.
            reach_col (str): The label for the n_reach column.
            population_size (int): The size of the total population. If it is None, the dataframe should have the all zeros row so that the total count of reach column can be interpreted as the `population_size`.

        """

        if reach_col not in dataframe.columns :
            raise Exception(f"reach column \'{reach_col}\' doesnt exist in dataframe, {dataframe.columns}")

        if not all(c in dataframe.columns for c in dim_cols) :
            raise Exception(f"one or more dimension columns are not in dataframe: {dim_cols} compared with {dataframe.columns}")

        impressions = np.array([
            (dataframe[col] * dataframe[reach_col]).sum()
            for col in dim_cols ])
        self.impressions = impressions

        rfdata = dataframe.copy()

        # Aggregate all frequencies larger than the max_freq into the max_freq
        for col in dim_cols :
            rfdata[col]  = np.where(rfdata[col] >= max_freq, max_freq, rfdata[col])

        rfdata = rfdata.groupby(dim_cols)[reach_col].sum().reset_index()

        # Make sure all frequencies upto max_freq exist
        rfdata = (
            pd.merge(
                rfdata,
                pd.DataFrame(np.array(list(itertools.product(*[range(0, max_freq+1) for c in dim_cols]))),
                             columns=dim_cols),
                on = dim_cols,
                how='right'
            ).sort_values(dim_cols).reset_index(drop=True)
        )

        # Manage the total population size
        population_size_intable = rfdata[reach_col].sum()
        if pd.isnull(rfdata[reach_col].at[0]) :
            if population_size is None:
                raise Exception("population_size should be a value when dataframe doesn't have zeros")
            self.population_size = population_size
            rfdata[reach_col].at[0] = population_size - population_size_intable

        else :
            if population_size is not None:
                warnings.warn("population_size is dictated by the given reach of the zero-all frequencies.")
            self.population_size = population_size_intable

        self.rfdata          = rfdata.fillna(0)
        self.max_freq        = max_freq
        self.dim_cols        = dim_cols
        self.reach_col       = reach_col
        self.n_dims          = len(dim_cols)

    @property
    def impressions(self):
        """The number of impressions in the report for each dimension."""
        return self._impressions

    @impressions.setter
    def impressions(self, impressions) :
        self._impressions = impressions

    @property
    def gr_values(self):
        """The gross rating of the report, i.e. impressions divided by the population size."""
        return self._impressions / self.population_size

    @gr_values.setter
    def gr_values(self, grs) :
        self._impressions = (grs * self.population_size).astype('int')

    def _copy_and_trim_to_max_freq(self, ) :
        return

    def reach_freq_values(self, normalized=False, max_freq=None) :
        """Returns the the reach and frequencies values in the report.

        Args:
            normalized (Bool): If True devides the reach values by the population_size (default False)
            max_freq (int) : If given trims the frequencies to the max_freq. It must be less than or equal to the current max_freq of the report.

        Returns:
            The values as a tuple of `(reach, frequencies)`.
        """
        result = None
        if max_freq is None or max_freq == self.max_freq :
            max_freq = self.max_freq
            result = self.rfdata[self.reach_col].values, self.rfdata[self.dim_cols].values
        elif max_freq < self.max_freq :
            rfdata = self.rfdata.copy()
            for col in self.dim_cols :
                rfdata[col]  = np.where(rfdata[col] >= max_freq, max_freq, rfdata[col])

            rfdata = rfdata.groupby(dim_cols).sum().reset_index()
            result = rfdata[self.reach_col].values, rfdata[self.dim_cols].values
        else :
            raise Exception(f"max_freq should be less than or equal to {self.max_freq}")

        if normalized :
            return result[0]/self.population_size, result[1]
        else :
            return result

    def pivot_to_dim_cols(self, normalized=False, max_freq=None) :
        """pivot the report to the multidimensional dim_cols where the reach are the values.

        Args:
            normalized (Bool): If True, devides the dataframe, or the reach values by the population_size (default False)
            max_freq (int) : If given trims the frequencies to the max_freq. It must be less than or equal to the current max_freq of the report.

        Returns:
            The pivoted dataframe (currently only working for two dimensions)
        """

        # Only two dimensinal pivoting is obvious. Larger dimensions probably rrequires different API and specific treatments and options, etc.
        if self.n_dims > 2 :
            raise Exception("Currently only two dimensions are supported for pivoting!")

        result = None
        if max_freq is None or max_freq == self.max_freq :
            max_freq = self.max_freq
            result = self.rfdata.pivot(
                index=self.dim_cols[0],
                columns=self.dim_cols[1],
                values=self.reach_col
            )
        elif max_freq < self.max_freq :
            rfdata = self.rfdata.copy()
            for col in self.dim_cols :
                rfdata[col]  = np.where(rfdata[col] >= max_freq, max_freq, rfdata[col])

            rfdata = rfdata.groupby(self.dim_cols).sum().reset_index()
            result = rfdata.pivot(
                index=self.dim_cols[0],
                columns=self.dim_cols[1],
                values=self.reach_col
            )
        else :
            raise Exception(f"max_freq should be less than {self.max_freq}")

        if normalized :
            return result/self.population_size
        else :
            return result


    def remove_dim(self, dim_name) :
        """Removes a single dimension of the report and effectively generates a new report with one less dimension.

        Args:
            dim_name (string): Name of the column to be removed.

        Returns:
            RFReport with one less dimension.
        """

        if dim_name not in self.dim_cols:
            raise Exception(f"The to-be-removed dim_column \"{dim_name}\" does not exist.")

        dim_cols = self.dim_cols.copy()
        dim_cols.remove(dim_name)

        rfdata = self.rfdata.drop(dim_name, axis=1).groupby(dim_cols).sum().reset_index()

        return RFReport(rfdata, self.max_freq, dim_cols, self.reach_col, self.population_size)


def generate_report(impressions, population_size, max_freq, id_col="user_id", media_col="media") :
    """Generates a mutli-dim reach and frequency report from the table of impressions (event logs)

    """

    df = (
        impressions[[media_col, id_col]].reset_index()
        .groupby([media_col, id_col])
        .count().rename(columns={'index' : 'frequency'})
        .reset_index()
        .pivot(index=id_col, columns=media_col)
        .fillna(0)
    )
    df.columns = df.columns.droplevel(0)
    media_cols = df.columns.tolist()
    df = df.reset_index().groupby(media_cols).count().rename(columns={id_col:'reach'}).reset_index()

    return RFReport(df, max_freq=20, dim_cols=media_cols, reach_col='reach', population_size=10000)
