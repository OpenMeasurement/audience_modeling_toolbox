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

from numpy.random import random

# Inverse probability distribution transformation
def udf_rates(m, population, alpha) :
    """Inverse probability distribution transformation"""

    return (m * ((1- np.arange(0, 1, 1/population)) ** (-1/alpha) - 1)).tolist()

def udf_sum(rates) :
    return np.sum(np.array(rates, dtype=float))

def udf_impressions(rate_impressions, rng=np.random.default_rng(None)):
    """Function to make a random choice of impressions based on rate"""

    r = rng.random()
    n = int(rate_impressions // 1)
    rem = rate_impressions % 1
    if r > rem :
        return n
    else :
        return n + 1

def udf_ts_list(start, end, n):
    return np.random.randint(start, end, n).tolist()


def gen_people_table_udf(census, demo_cols, m=1.0, alpha=20) :
    """
    Starting from a census file, generate the population and assign rates according
    to the power-law or Lomax (Pareto type II) distribution).
    -- version using a udf function --

    Returns a table of people with demographics and rate of impression generation.
    """
    population_total = df_census.agg(F.sum("population")).collect()[0][0]

    df_people = (
        df_census
        .withColumn("ratio", F.col("population")/F.lit(population_total))
        .withColumn("m", F.lit(m))
        .withColumn("alpha", F.lit(alpha))
        .withColumn("rates", udf_rates(F.col("m"), F.col("population"), F.col("alpha")))
        .withColumn("rate", F.explode(F.col("rates")))
        .withColumn("user_id", F.row_number().over(Window.orderBy(*demo_cols, F.col("rate"))))
        .select(
            "user_id",
            *demo_cols,
            "population",
            "ratio",
            "rate")
    )
    return df_people


def gen_people_table(df_census, demo_cols, m=1.0, alpha=20) :
    """
    Starting from a census file, generate the population and assign rates according
    to the power-law or Lomax (Pareto type II) distribution).

    Returns a table of people with demographics and rate of impression generation.
    """
    population_total = df_census.agg(F.sum("population")).collect()[0][0]
    max_population = df_census.agg(F.max("population")).collect()[0][0]

    spark = SparkSession.builder.getOrCreate()
    spark_range = spark.range(max_population - 1)

    df_people = (
        df_census
        .crossJoin(F.broadcast(spark_range))
        .where("id < population")
        .withColumn("ratio", F.col("population")/F.lit(population_total))
        .withColumn("m", F.lit(m))
        .withColumn("alpha", F.lit(alpha))
        .withColumn("rate", F.col("m") * (
            (F.lit(1) - F.col("id") / F.col("population"))**(-F.lit(1)/F.col("alpha")) - F.lit(1))
                   )
        .withColumn("user_id", F.row_number().over(Window.orderBy(*demo_cols, F.col("rate"))))
        .select(
            "user_id",
            *demo_cols,
            "population",
            "ratio",
            "rate")
    )
    return df_people

def add_n_impressions(df_people, I, population_total) :
    """
    Assign a certain number of impressions for each person based on their rates.
    Note that this is a probabilistic process.
    """
    sum_rates = df_people.agg(F.sum("rate")).collect()[0][0]
    df = (
        df_people
        .withColumn("rate", F.col("rate") * F.lit(population_total/sum_rates))
        .withColumn("rate_impressions", F.col("rate") * I/population_total)
        .withColumn("n_impressions", udf_impressions(F.col("rate_impressions")))
        .cache()
        .where("n_impressions > 0")
    )
    return df

def gen_synthetic_impressions(df_people_n, start_ts, end_ts, demo_cols) :
    """
    Given a `df_people_n` dataframe of people with a column `n_impressions`
    that indicates the total number of impressions for that person, generate
    and impression table and randomly assign the timestamps.
    """
    df_impressions = (
        df_people_n
        .withColumn("timestamp_list",
                udf_ts_list(
                    F.unix_timestamp(F.lit(start_ts)),
                    F.unix_timestamp(F.lit(end_ts)),
                    F.col("n_impressions"))
                   )
        .withColumn("timestamp_int", F.explode(F.col("timestamp_list")))
        .withColumn("timestamp", F.from_unixtime(F.col("timestamp_int")))
        .select(
            "user_id",
            *demo_cols,
            "timestamp_int",
            "timestamp"
        )
        .sort("timestamp")
    )
    return df_impressions
