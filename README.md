# mongo-shardkey-tools

A set of tools to visualise and inspect the performance and scalability of a MongoDB shard key. At this time `plot_split_distribution` is the only tool.

plot_split_distribution
-------------------------

This tool visualises the distribution of chunk splits over the shard key domain.

It provides visual feedback on the [frequency](https://docs.mongodb.com/manual/core/sharding-shard-key/#shard-key-frequency)
of a shard key, and reveals whether the shard key has a [monotonically changing pattern](https://docs.mongodb.com/manual/core/sharding-shard-key/#monotonically-changing-shard-keys).
Both aspects affect write scalability and workload distribution.

### Sample Output

The left hand plot displays even split distribution;
the plot on the right hand side displays poor distribution.

Even distribution             | Uneven distribution
:-------------------------:|:-------------------------:
![img-good-key](img/good.png "Good shard key")|  ![img-bad-key](img/bad.png "Bad shard key")

The distribution covers a time window which defaults to the available changelog and is configurable (`--starttime`). The left-hand example covers 79 hours, the right-hand 125 days.

* The X axis are contiguous ranges of shard key values, sorted from [minKey](https://docs.mongodb.com/manual/reference/operator/query/type/#minkey-and-maxkey) (leftmost) to [maxKey](https://docs.mongodb.com/manual/reference/operator/query/type/#minkey-and-maxkey) (rightmost). These ranges correspond to the chunks at the start of the changelog, and do not necessarily reflect the _current_ chunks layout.
* The Y axis is the number of chunk splits that occurred on a range since the start of the changelog.


Click a range to display its boundaries and the number of splits it underwent. The below shows three splits in the shard key range "aa" (inclusive) to "az" (exclusive).
```
range[7851]: {"min": {"shardkey": "aa"}, "max": {"shardkey": "az"}, "splits": 3}
```

### Getting Started

1. Download this repository.
2. Install dependencies: `$ pip install -r requirements.txt`
3. Launch the tool: `$ python plot_split_distribution.py [ -u 'URI' ] mydb.mycoll`

Don't have a sharded cluster at hand and want to explore the tool? Here's sample data to play with.
```
$ mlaunch init --single
$ mongorestore --gzip --archive=sample_data/sample_config.gz
$ python plot_split_distribution.py db.coll
```

### Gotchas

The following aspects may affect or skew the analysis. Depending on the frequency of these events,
the resulting distribution may not accurately reflect actual write activity.
* The [balancer](https://docs.mongodb.com/manual/tutorial/manage-sharded-cluster-balancer/) can perform a split during a migration. `--no_balancer_splits` filters out balancer splits.
* A [range that is not divisible](https://docs.mongodb.com/manual/core/sharding-data-partitioning/#indivisible-chunks) cannot be split: lack of split activity for an invidisible range does not necessarily imply that that range is not written to.
* Any manual splitting activity does not necessarly relate to actual write activity.

This software is not officially supported by [MongoDB, Inc.](https://www.mongodb.com>)
Bug report, feature request? Please go a head and file a new [issue](https://github.com/josefahmad/mongo-shardkey-tools/issues?state=open>).
