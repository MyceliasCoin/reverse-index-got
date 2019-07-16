from __future__ import print_function
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, SQLContext
from pyspark.sql.functions import explode, concat, col, lit, split, translate, row_number, arrays_zip
from pyspark.sql.types import *
from pyspark.sql.window import Window
import random


def inside(p):
    x, y = random.random(), random.random()
    return x*x + y*y < 1


if __name__ == "__main__":
    """
    Setup Spark session
    """
    # set up spark context and session
    spark_context = SparkContext(conf=SparkConf().setAppName("Tx-Reverse-Lookup"))
    spark = SparkSession.builder.appName("Tx-Reverse-Lookup").getOrCreate()
    spark_context = spark.sparkContext

    num_samples = 1000000

    count = spark_context.parallelize(range(0, num_samples)).filter(inside).count()

    print("Pi is roughly %f" % (4.0 * count / num_samples))

    # stop spark session
    spark.stop()

