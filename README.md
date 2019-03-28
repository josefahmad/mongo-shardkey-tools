# mongo-shardkey-tools
A set of tools to support the design and evaluation of a MongoDB shard key.

plot_split_distribution
-------------------------

Plot and inspect the distribution of chunk splits in a collection.

Visualise the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of a shard key and whether the key is [monotonically changing](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
Both aspects affect write scalability.

### Output

The collection on the left hand side indicates that the shard key has an even split distribution,
the one on the right hand side displays poor distribution.

Even distribution             | Uneven distribution
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

The split distribution covers the time frame stored in the [changelog](https://docs.mongodb.com/manual/reference/config-database/#config.changelog) collection, which is a [capped collection](https://docs.mongodb.com/manual/core/capped-collections/) storing the most recent splits.

The X axis displays the number of chunks in the cluster at the earliest time in the changelog. The Y axis displays the number of chunk splits per chunk that occurred across the changelog.

Clicking the plot shows the chunks nearby and the number of splits they underwent:
```
Chunk[100]: {"min": {"x": "caa"}, "max": {"x": "czw"}, "splits": 3}
Chunk[101]: {"min": {"x": "czw"}, "max": {"x": "dab"}, "splits": 2}
Chunk[102]: {"min": {"x": "dab"}, "max": {"x": "euj"}, "splits": 10}
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
