from __future__ import print_function
from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, SQLContext
from pyspark.sql.functions import explode, concat, col, lit, split, translate, row_number, arrays_zip
from pyspark.sql.types import *
from pyspark.sql.window import Window
import random
import re


def main(sc):

    # set file path
    path = '../../input_test'
    rdd = spark_context.wholeTextFiles(path, use_unicode=True)

    # replacement string for filename
    long_path = "file:/home/cheon/PycharmProjects/reverse-index-got/input_test/"

    # replacement for insignificant characters
    # regex_tgt = "[,.?;-\'\[\]]"
    regex_tgt = '[^a-zA-Z]+'

    # process data
    output = rdd.flatMap(lambda file: [(file[0].replace(long_path, ""), re.sub(regex_tgt, "", word)) for word in file[1].lower().split()]) \
        .map(lambda file_word: (file_word[1], [file_word[0]])) \
        .reduceByKey(lambda a, b: a + b) \
        .map(lambda word_files: (word_files[0], list(set(word_files[1])))) \
        .sortByKey(ascending=True)

    output.saveAsTextFile("output.txt")

    # for x in output.collect():
    #     print(x)


if __name__ == "__main__":
    """
    Setup Spark session
    """
    # set up spark context and session
    spark_context = SparkContext(conf=SparkConf().setAppName("Pi-Test"))
    spark = SparkSession.builder.appName("Pi-Test").getOrCreate()
    spark_context = spark.sparkContext

    # run main function
    main(spark_context)

    # stop spark session
    spark.stop()

