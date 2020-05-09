# mongo-shardkey-tools

A set of tools to visualise and inspect the performance and scalability of a MongoDB shard key.

At this time `plot_split_distribution` is the only tool.

plot_split_distribution
-------------------------

This tool visualises the distribution of chunk splits over the shard key ranges in a collection.

It provides visual feedback on the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of a shard key, and reveals whether the shard key has a [monotonically changing pattern](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
Both aspects affect write scalability and workload distribution.

### Sample Output

The left hand plot displays even split distribution;
the plot on the right hand side displays poor distribution.

Even distribution             | Uneven distribution
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

The distribution covers a time window which defaults to the available changelog and is configurable. The left-hand example covers 79 hours, the right-hand 125 days.

* The X axis are contiguous ranges of shard key values, sorted from [minKey](https://docs.mongodb.com/manual/reference/operator/query/type/#minkey-and-maxkey) (leftmost) to [maxKey](https://docs.mongodb.com/manual/reference/operator/query/type/#minkey-and-maxkey) (rightmost). These ranges correspond to the chunks at the start of the changelog, and do not necessarily reflect the _current_ chunks layout.
* The Y axis is the number of chunk splits that occurred on a range since the start of the changelog.


Click a range to display its boundaries and the number of splits it underwent. The below shows three splits in the shard key range "aa" (inclusive) to "az" (exclusive).
```
range[7851]: {"min": {"shardkey": "aa"}, "max": {"shardkey": "az"}, "splits": 3}
```

### Getting Started

1. Download this repository.
2. Install dependencies.
   ```
   $ pip install -r requirements.txt

   ```
3. Launch the tool.
  ```
  $ python plot_split_distribution.py [ -u 'URI' ] mydb.mycoll
  ```
  Replace `mydb.mycoll` with the collection [namespace](https://docs.mongodb.com/manual/reference/glossary/#term-namespace).

  The optional `-u URI` connects to the cluster. Replace `URI` with the [connection string](https://docs.mongodb.com/manual/reference/connection-string/) (defaults to `mongodb://localhost:27017`).

It is also possible to explore the tool with the sample `db.coll` included in `sample_config.gz`.
```
$ mlaunch init --single
$ mongorestore --gzip --archive=sample_data/sample_config.gz
$ python plot_split_distribution.py db.coll
```

### Caveats

The following aspects may affect or skew the analysis. Depending on the frequency of these events,
the resulting distribution may not accurately reflect actual write activity.
* The [balancer](https://docs.mongodb.com/manual/tutorial/manage-sharded-cluster-balancer/) can perform a split as part of a chunk migration.
* A [range that is not divisible](https://docs.mongodb.com/manual/core/sharding-data-partitioning/#indivisible-chunks) cannot be split, therefore the lack of split activity for an invidisible range does not necessarily imply lack of writes to that range.
* If manual splitting is performed, that split activity may not necessarly relate to actual write activity.

For more accurate results, ensure that the ranges are divisible and that the balancer is disabled during the time of interest.

Disclaimer
----------

This software is not supported by [MongoDB, Inc.](https://www.mongodb.com>)
under any of their commercial support subscriptions or otherwise. Any usage of
mongo-shardkey-tools is at your own risk. Bug reports, feature requests and
questions can be posted in the [Issues](https://github.com/josefahmad/mongo-shardkey-tools/issues?state=open>)
section on GitHub.
