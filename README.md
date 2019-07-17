# Game of Thrones: Reverse Indexing

![Image of Cover](images/intro.jpeg)

Castle Black's library is home to hundreds of thousands of rare and invaluable texts.

Our goal is to enable easier and more efficient search across documents based on keywords.

We will be using a vector representation of book documents called reverse indexing (a.k.a. inverted indexing).


# Table of Contents
1. [Motivation](README.md#Motivation)
2. [Dataset](README.md#Dataset)
3. [Methodology](README.md#Methodology)
4. [MapReduce](README.md#Architecture)
5. [Installation](README.md#Installation)

## Motivation

We are ultimately trying to generate a vector representation of documents, which is a common type of document representation used by search engines.
Vector representation enables use of mathematical tools such as distance, similarity and dimension reduction.

An inverted index of documents can significantly speed up calculations.
These calculations are often based on dot products that consume a lot of CPU and memory.
Having an inverted index greatly simplifies those dot products.

Here we aim to write an efficient implementation to build an inverted index of a large collection of documents.


## Dataset

Our dataset is a collection of N documents - think of each document simply as a book or text.

We have one file per document and the name of a file is simply the index of the document as shown below.

![Figure 1](images/files.png)


## Methodology

We want a dictionary that matches every word from the documents with a unique id:

![Image of Method1](images/method1.png)


### Inverted Index

Using both the dataset and the previous dictionary, we can build an inverted index that provides, for every word, the list of documents it appears in:

![Image of Method2](images/method2.png)

An ideal solution should be able to work on a massive dataset and run on a distributed system so we are not limited by the amount of storage, memory and
CPU of a single machine. Spark is a likely a good candidate for running our solution.


### Algorithm

The required algorithm involves four key steps:

1. Read the documents and collect every pair (wordID, docID)
2. Sort those pairs by wordID and by docID
3. For every wordID, group the pairs so you have its list of documents
4. Merge the intermediate results to get the final inverted index


## MapReduce

![Image of Pipeline](images/pipelinefinal.png)

### Data Acquisition

Data is acquired by running JSON-RPC calls from a full Bitcoin Core node.

Run `./json-rpc-pase-all-blocks.sh` in `/src/bash` directory to deserialize Bitcoin block data into JSON and write into dedicated AWS S3 bucket.
This must be run from a full Bitcoin Core node with transaction indexing enabled (see [here](https://www.buildblockchain.tech/blog/btc-node-developers-guide) for setup instructions)


### Ingestion

BitWatch runs on top of a Spark cluster (one c5.large for master, three c5.2xlarge for workers) and a single PostgreSQL instance (one m4.large).

Data is ingested with Spark from an S3 bucket that holds JSON files (one file for each blockchain block).

Results are then written out to PostgreSQL in a tabular format in a `transactions` table (each row represents one transaction).

(See Installation section below) Run `process-json.py` in `src/spark` directory using `spark-submit` command in PySpark to ingest JSON files from AWS S3 bucket.


### Compute

BitWatch uses Spark GraphFrames (built on top of a vertex DataFrame and edge DataFrame) to run `.connectedComponents()` method for generating address clusters.

`.connectedComponents()` is an implementation of the Disjoint Set (a.k.a. Union Find) algorithm to cluster addresses across Bitcoin transactions.

Using a graph model for processing transaction data is crucial as Disjoint Set on a relational model is much slower compared to a graph model.

(See Installation section below) run `tx-lookup-cluster.py` in `src/spark` directory using `spark-submit` command in PySpark to process `transactions` table in PostgreSQL and generate address clusters.


## Installation

Spark installation will occur on local machine, but installation instructions are equally applicable to an AWS EC2 cluster.

Before going through the below instructions, please familiarize yourself with setting up security groups in AWS [here](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html).


### Spark

We will set up Spark on a local machine for testing purposes, but below instructions are applicable to a full AWS EC2 cluster (master + workers).

When installing only on local machine, ignore any worker-specific instructions below.

We will launch four EC2 instances, each using the **Ubuntu Server 18.04 LTS (HVM), SSD Volume Type** 1 x m5.large (master), 3x m5.2xlarge (workers) image type and set root volume storage to 100 GB.
Then [SSH into the instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/AccessingInstancesLinux.html) and run the following commands:

    # run update and install java and scala
	sudo apt update
	sudo apt install openjdk-8-jre -y
	sudo apt install scala -y
	
	# install sbt
    echo "deb https://dl.bintray.com/sbt/debian /" | sudo tee -a /etc/apt/sources.list.d/sbt.list
    sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2EE0EA64E40A89B84B2DF73499E82A75642AC823
    sudo apt-get update
    sudo apt-get install sbt
    
    # install Spark 2.4.3
    wget http://apache.mirrors.tds.net/spark/spark-2.4.3/spark-2.4.3-bin-hadoop2.7.tgz -P ~/Downloads
    sudo tar zxvf ~/Downloads/spark-2.4.3-bin-hadoop2.7.tgz -C /usr/local
    sudo mv /usr/local/spark-2.4.3-bin-hadoop2.7 /usr/local/spark
    sudo chown -R ubuntu /usr/local/spark
    
    # edit ~/.profile
    nano ~/.profile
    
    # add in following lines to ~/.profile
    export SPARK_HOME=/usr/local/spark
    export PATH=$PATH:$SPARK_HOME/bin
    export PYSPARK_PYTHON=python3
    
    # update environment variables
    source ~/.profile
    
    # configure Spark
    cp /usr/local/spark/conf/spark-env.sh.template /usr/local/spark/conf/spark-env.sh
    
    # edit spark-env.sh
    nano /usr/local/spark/conf/spark-env.sh
    
    # add in following lines to spark-env.sh
    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
    export SPARK_PUBLIC_DNS="<MASTER-public-dns>" (i.e., like ec2-x-xx-xxxx-xx.compute1.amazonaws.com)

Go to master node and run:

    touch $SPARK_HOME/conf/slaves
    
Add each worker to the file by opening $SPARK_HOME/conf/slaves and copying the public DNS (one per line):

    nano $SPARK_HOME/conf/slaves
    
Connect master node to worker nodes (commands are only for master node):

    sudo apt install openssh-server openssh-client
    cd ~/.ssh
    ssh-keygen -t rsa -P ""
    
    Generating public/private rsa key pair.
    Enter file in which to save the key: id_rsa
    Your identification has been saved in id_rsa.
    Your public key has been saved in id_rsa.pub.
    
Manually copy id_rsa.pub key top worker nodes:

    # on master:
    cat ~/.ssh/id_rsa.pub
    
    # on slaves:
    vi ~/.ssh/authorized_keys
    # paste the key
    
    # test connection from master to workers
    ssh ubuntu@ec2.x--x-x-x-x-x
    
Start Spark server (should see Spark ASCII art):

    # start Spark server
    sh /usr/local/spark/sbin/start-all.sh
    
Check everything is working by going to the master_public_ip:8080 (requires port 8080 open).
If you see the SparkUI with your workers up, Spark setup is complete.

Install PySpark:

    # install pip3
    sudo apt install python3-pip -y
    
    # install pyspark and findspark
    pip3 install pyspark
    pip3 install findspark --user
    
We should now be able to submit PySpark scripts (i.e., `reverse-index.py`) files using `spark-submit` and run in Spark.

