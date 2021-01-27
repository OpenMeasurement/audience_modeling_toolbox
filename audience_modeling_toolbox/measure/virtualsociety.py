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

class AbstractVirtualSociety(ABC) :
    """Abstract class for the virtual society."""

    @property
    @abstractmethod
    def population(self):
        "The population of the virtual society."
        pass

class VirtualSociety(AbstractVirtualSociety) :
    """The class for the virtual society"""

    def __init__(self, dataframe, media_cols, id_col='vid') :
        """

        Args:
            dataframe (pandas dataframe): The dataframe of individuals in the society.
            media_cols (list of string): The list of media cols
            id_col (string): The identiy column (must be unique)
        """

        if id_col not in dataframe.columns :
            raise Exception(f"The id_col {id_col} does not exist.")
        self.id_col = id_col

        id_duplicates = dataframe[id_col].duplicated()
        if id_duplicates.any() :
            raise Exeption(f"Found duplicated IDs in column {id_col} : {is_duplicates.head()}")
        self.population_size = len(dataframe.index)
        self.dataframe = dataframe

        if any([c not in dataframe.columns for c in media_cols]) :
            raise Exception(f"Dataframe doens't have one or more of the media_cols {media_cols}")
        self.media_cols      = media_cols


    @property
    def population(self):
        return self.dataframe[self.id_col]

    # @classmethod
    # def random(cls, population_size, media_cols, mode="exp_mixture") :
    #     """Generates a random virtual society

    #     Args:
    #         population_size (int): The size of the virtual socitey population
    #         mode (string): Choose the activity function of the virtual society
    #     """

    #     if mode == "exp_mixture" :
    #         adf = MixtureOfExponentials(n_exps=6, n_dims=len(media_cols))
    #         return adf.generate_virtual_society(population_size, media_cols)
    #     else :
    #         raise Exception(f"mode {mode} is undefined!")

    def probability_ranges(self, media_col, normalize=True):
        """Returns the probability ranges across a single dimension (media)

        Args:
            media_col (string) : label of the column for which to calculate the probability ranges

        Returns:
            A dataframe that contains the id_col as well as the media_col and two probability ranges "prob_<" and "prob_>="
        """

        df = self.dataframe[[self.id_col, media_col]].sort_values(media_col).reset_index(drop=True)

        col = df[media_col].cumsum()
        if normalize :
            col = col / self.population_size

        df["prob_>"] = col.shift(1).fillna(0)
        df["prob_<="] = col

        return df


    def simulate_impressions(self, impressions_size):
        """Simulate the impressions of a campaign given the total GRP for each medium

        Args:
            impressions_size (array of int): The number of impressions for each medium.

        Returns:
            A dataframe of impressions
        """

        if len(impressions_size) != len(self.media_cols) :
            raise Exception("The size of the impressions_array doesn't match the number of media_cols!")

        impressions_list = []
        for n in range(len(impressions_size)) :
            impressions = pd.DataFrame(np.random.random(impressions_size[n]), columns=['probability'])
            media = self.media_cols[n]
            df_prob = self.probability_ranges(media)
            impressions[self.id_col] = impressions['probability'].apply(lambda p : df_prob[self.id_col].iloc[df_prob['prob_<='].searchsorted(p)])
            impressions['media'] = media
            impressions_list.append(impressions[[self.id_col, 'media']])

        return pd.concat(impressions_list, axis=0)


    def assign_impressions(self, impressions, media_col='media') :
        """Given an impressions table, assign virtual ids to each impression

        Args:
        impressions (dataframe): The dataframe containing the impression logs.
        """

        media = impressions[media_col].unique().tolist()
        impressions['probability'] = np.random.random(len(impressions.index))
        df_prob = { m : self.probability_ranges(m) for m in media}
        impressions[self.id_col] = impressions[[media_col, 'probability']].apply(
            lambda x : df_prob[x[0]][self.id_col].iloc[
                df_prob[x[0]]['prob_<='].searchsorted(x[1])
            ],
            axis=1
        )
        return impressions
