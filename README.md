# mongo-shardkey-tools
A set of tools to support the design of a MongoDB shard key.

plot_split_distribution
-------------------------

Visualise and inspect the distribution of chunk splits in a collection.

Useful to determine the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of the shard key and whether the shard key is [monotonically changing](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
These two aspects are key requirements to write scalability in a sharded cluster. 

### Output Examples

Two different collections, one using a shard key with even split distribution,
the other with uneven distribution.

Even distribution             | Uneven distribution 
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

### Usage

TODO

Disclaimer
----------

This software is not supported by [MongoDB, Inc.](https://www.mongodb.com>)
under any of their commercial support subscriptions or otherwise. Any usage of
mongo-shardkey-tools is at your own risk. Bug reports, feature requests and
questions can be posted in the [Issues](https://github.com/josefahmad/mongo-shardkey-tools/issues?state=open>)
section on GitHub.

