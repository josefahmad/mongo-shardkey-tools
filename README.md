# mongo-shardkey-tools
A set of tools to support the design and evaluation of a MongoDB shard key.

plot_split_distribution
-------------------------

Plot and inspect the distribution of chunk splits in a collection.

Visualise the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of a shard key and whether the key is [monotonically changing](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
Both aspects affect write scalability.

### Sample Output

The collection on the left hand side indicates that the shard key has an even split distribution,
the one on the right hand side displays poor distribution.

Even distribution             | Uneven distribution
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

The X axis displays the chunks in the cluster at the earliest time available. The leftmost chunk is the minKey chunk, the rightmost chunk is the maxKey chunk.<br/> 
The Y axis displays the number of chunk splits per chunk that occurred during the time frame. A chunk split usually indicates write activity.

The left-hand example covers a time frame of 79 hours. The right-hand example covers 125 days. The time frame defaults to the earliest time available and is configurable.

Click a chunk to display its range and the number of splits it underwent:
```
Chunk[7851]: {"min": {"key": "caa"}, "max": {"key": "cba"}, "splits": 3}
```

### Getting Started

1. Download this repository.
2. Install dependencies.
   ```
   pip install matplotlib numpy progressbar pymongo

   ```
3. Spin up a MongoDB instance with sample sharding metadata. `sample_config.gz` includes metadata for a sample [namespace](https://docs.mongodb.com/manual/reference/glossary/#term-namespace) called `db.coll`.
   ```
   mlaunch init --single
   mongorestore --gzip --archive=sample_data/sample_config.gz
   ```
4. Launch the tool.
   ```
   python plot_split_distribution.py db.coll
   ```

### Usage

```
# python plot_split_distribution.py db.coll
```

Where `db.coll` is the target namespace. 

Optional arguments:
* `-u MONGO_URI`: the [connection string](https://docs.mongodb.com/manual/reference/connection-string/). Defaults to `localhost:27017`.
* `-s STARTTIME`: custom start time, in UTC 8601. Defaults to the head of the changelog.

Disclaimer
----------

This software is not supported by [MongoDB, Inc.](https://www.mongodb.com>)
under any of their commercial support subscriptions or otherwise. Any usage of
mongo-shardkey-tools is at your own risk. Bug reports, feature requests and
questions can be posted in the [Issues](https://github.com/josefahmad/mongo-shardkey-tools/issues?state=open>)
section on GitHub.
