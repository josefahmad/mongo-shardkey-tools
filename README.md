# mongo-shardkey-tools
A set of tools to support the design of a MongoDB shard key.

plot_split_distribution
-------------------------

Plot and inspect the distribution of chunk splits in a collection.

This tool can be useful to visualise the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of the shard key and can help determine whether the shard key is [monotonically changing](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
These two aspects affect write scalability.


### Sample Output

Below are two different sample collections, one displaying a shard key with even split distribution,
the other one with uneven distribution.

Even distribution             | Uneven distribution
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

The split distribution covers the time frame stored in the [changelog](https://docs.mongodb.com/manual/reference/config-database/#config.changelog) collection, which is a [capped collection](https://docs.mongodb.com/manual/core/capped-collections/) storing the most recent splits. In the _even distribution_ example, the changelog covers 79 hours (Dec 2nd to Dec 5th).

The X axis displays the number of chunks in the cluster at the earliest time in the changelog.

The Y axis displays the number of chunk splits per chunk that occurred across the changelog.

A mouse click in the plot shows the chunks nearby and the number of splits they underwent:
```
Chunk[100]: {"min": {"x": "caa"}, "max": {"x": "czw"}, "splits": 3}
Chunk[101]: {"min": {"x": "czw"}, "max": {"x": "dab"}, "splits": 2}
Chunk[102]: {"min": {"x": "dab"}, "max": {"x": "euj"}, "splits": 10}
```


### Usage

```
# python plot_split_distribution.py namespace
```

Where _namespace_ is the `db.collection` [namespace](https://docs.mongodb.com/manual/reference/glossary/#term-namespace).

For more accurate results, it is recommended to run plot_split_distribution against a standalone instance running a copy of the [config database](https://docs.mongodb.com/manual/reference/config-database/), rather than an operating cluster.

Main arguments:
* `-u MONGO_URI`: the [connection string](https://docs.mongodb.com/manual/reference/connection-string/) to the deployment. Defaults to `localhost:27017`.
* `-s STARTTIME`: specify a start time (UTC 8601). Defaults to the earliest time in the changelog window.

Examples:
```
# python plot_split_distribution.py db.collection
```
```
# python plot_split_distribution.py db.collection -u mongodb://192.168.1.1:3000 -s "2019-01-10T04:56"
```


### Dependencies

```
pip install progressbar pymongo
```

Disclaimer
----------

This software is not supported by [MongoDB, Inc.](https://www.mongodb.com>)
under any of their commercial support subscriptions or otherwise. Any usage of
mongo-shardkey-tools is at your own risk. Bug reports, feature requests and
questions can be posted in the [Issues](https://github.com/josefahmad/mongo-shardkey-tools/issues?state=open>)
section on GitHub.
