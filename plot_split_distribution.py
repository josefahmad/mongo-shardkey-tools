# Author: Josef Ahmad <josefahmad1@gmail.com>

import argparse
import collections
import dateutil.parser
import datetime
import json
import math
import numpy
import pymongo
import re
import time
from bson import ObjectId
from bson.son import SON
from bson.json_util import dumps
from bson.min_key import MinKey
from bson.max_key import MaxKey
from bson import CodecOptions, SON
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from progressbar import ProgressBar, Percentage, Bar
from pymongo import MongoClient

# TODO
# * handling comparison between datetime and other data types (e.g. MinKey/MaxKey)

verbose = False
no_progressbar = False
exclude_balancer_splits = False
only_balancer_splits = False

date_strfmt = "%Y-%m-%dT%H:%M:%S"

list_splits = []
final_list = []

splits_discarded = 0

def get_time_extent(db):

    t0 = db['changelog'].find({}, {'time': 1, '_id': 0}).sort(
        [('time', pymongo.ASCENDING)]).limit(1)[0]['time']
    t1 = db['changelog'].find({}, {'time': 1, '_id': 0}).sort(
        [('time', pymongo.DESCENDING)]).limit(1)[0]['time']

    return t0, t1


def get_time_delta_hours(t0, t1):

    delta = t1 - t0
    delta_hours_mod = divmod(delta.days * 86400 + delta.seconds, 3600)
    delta_hours = delta_hours_mod[0]
    if (delta_hours_mod[1] != 0):
        delta_hours += 1

    delta_str = str(delta_hours) + ' hours'
    if (delta_hours >= 96):
        delta_str = str(delta_hours / 24) + ' days'

    return delta_hours, delta_str


def onclick(event):

    if (isinstance(event.xdata, numpy.float64) == False):
        return

    xdata = int(round(event.xdata))

    chunk_range = len(final_list) / 64
    if (chunk_range == 0):
        chunk_range = 1

    min_range = xdata - chunk_range / 2
    max_range = xdata + chunk_range / 2

    if (min_range <= 0):
        min_range = 1
    if (min_range >= max_range):
        max_range = min_range + 1
    if (max_range > len(final_list)):
        max_range = len(final_list)

    for i in range(min_range - 1, max_range):
        if (final_list[i]['splits'] != 0):
            print('range[' + str(i) + ']: ' + dumps(final_list[i]))

def is_balancer_split(ns, split, split_time):

    changelog_son = db['changelog'].with_options(
        codec_options=CodecOptions(document_class=SON))
    actionlog_son = db['actionlog'].with_options(
        codec_options=CodecOptions(document_class=SON))

    # TODO noTimeout
    # TODO make it work with 3.4 (7 steps)

    # The algorithm uses the following method to determine whether a split is initiated
    # the balancer:
    # * The split occurred within the a balancer round, AND
    # * Before the split and within the balancer round, a failed moveChunk.from
    #   occurred for a chunk whose range matches the 'before' range in the split, AND
    # * The failed moveChunk.from aborted at step 3.

    # For non-prod environments consider the following indices to speed up the algo:
    # db.changelog.createIndex({what:1, ns:1, 'details.min':1, 'details.max':1, 'details.note':1, time:1})
    # db.actionlog.createIndex({what:1, time:1})

    for moveChunk in changelog_son.find({'what': 'moveChunk.from',
                                         'ns': ns,
					 'details.note': 'aborted',
					 'details.min': split['details']['before']['min'],
					 'details.max': split['details']['before']['max'],
					 # Server 3.4 has 7 moveChunk steps
					 '$or' : [ {'details.step 2 of 6': {'$exists': True}},  {'details.step 2 of 7': {'$exists': True}} ],
					 '$or' : [ {'details.step 3 of 6': {'$exists': False}}, {'details.step 3 of 7': {'$exists': False}} ],
					 'time' : {'$lt': split_time}}).sort([('time', pymongo.DESCENDING)]).limit(1):
        for bround in actionlog_son.find({'what': 'balancer.round', 'time' : {'$gte': split_time}}).sort([('time', pymongo.ASCENDING)]).limit(1):
	    # The failed moveChunk + split must have happened within the balancer round
            bround_start = bround['time'] - datetime.timedelta(milliseconds=bround['details']['executionTimeMillis'])
            if (bround_start <= moveChunk['time'] and bround_start <= split_time):
                if (verbose):
                    print('balancer initiated split: ' + dumps(split))
                return True
            break

        break

    return False

def fieldorder_cmp(a, b, op):

    aiv = a.itervalues()
    biv = b.itervalues()

    while True:
        try:
            av = next(aiv)
            bv = next(biv)

            if (isinstance(av, collections.OrderedDict) or isinstance(bv, collections.OrderedDict)):
                if (fieldorder_cmp(av, bv, op)):
                    return True
            else:
                if (op == 'lt'):
                    if (av < bv):
                        return True
                elif (op == 'lte'):
                    if (av <= bv):
                        return True
                elif (op == 'gte'):
                    if (av >= bv):
                        return True
                elif (op == 'gt'):
                    if (av > bv):
                        return True
                else:
                    raise Exception('Unknown operator ' + str(op))

        except StopIteration:
            break
        except TypeError as e:
            # datetime cannot compare with other types. Typically this exception happens
            # when comparing with MinKey/MaxKey
            if (isinstance(av, datetime.datetime) or isinstance(bv, datetime.datetime)):
                if (op == 'gt' or op == 'gte'):
                    if av == MaxKey:
                        return True
                    if av == MinKey:
                        return False
                    if bv == MaxKey:
                        return False
                    if bv == MinKey:
                        return True
                if (op == 'lt' or op == 'lte'):
                    if av == MaxKey:
                        return False
                    if av == MinKey:
                        return True
                    if bv == MaxKey:
                        return True
                    if bv == MinKey:
                        return False

            else:
                raise e

    return False


def find_split(list_splits, bookmark, chunk):
    iterated = False

    if (bookmark == -1):
        return None, bookmark

    for i in range(bookmark, len(list_splits)):
        iterated = True
        split = list_splits[i]

        try:
            if chunk['min'] == split['min']:
                # This chunk was originated by a split in the list.
                return split, i + 1

            if (fieldorder_cmp(chunk['min'], split['min'], 'lt')):
                # The current chunk is lower than the next split.
                return None, bookmark
        except TypeError as e:
            print('typeerror: split: ' + dumps(split) +
                  ', chunk: ' + dumps(chunk))
            print(e)

    if (iterated == True):
        print('Warning: [' + str(bookmark) + '] split: ' + dumps(split),
              ' found to be ahead of chunk: ' + dumps(chunk['min']))
        return None, i

    # From now on, no more splits, just keep appending chunks.
    return None, -1


def build_split_list(db, ns, t0, t1):

    global splits_discarded

    changelog_son = db['changelog'].with_options(
        codec_options=CodecOptions(document_class=SON))

    split_pattern = re.compile('split')
    splits_count = db['changelog'].count(
        {'ns': ns, 'what': split_pattern, 'details.number': {'$ne': 1}, 'time': {'$gte': t0}})

    print('Building splits...')

    if (no_progressbar == False):
        pbar = ProgressBar(
            widgets=[Percentage(), Bar()], maxval=splits_count).start()
        bar_i = 0

    pipeline = [
        {'$match': {'ns': ns, 'what': split_pattern,
                    'details.number': {'$ne': 1}, 'time': {'$gte': t0}}},
        {'$project': {'_id': 0, 'details.before.min': 1, 'details.before.max': 1, 'time': 1}},
        {'$sort': SON([('details.before.min', 1)])}]

    bookmark = 0
    bar_i = 0

    for split in changelog_son.aggregate(pipeline, allowDiskUse=True):

        discard = False

        if (no_progressbar == False):
            pbar.update(bar_i)
	    bar_i = bar_i + 1

        if exclude_balancer_splits == True:
            if (is_balancer_split(ns, split, split['time'])):
	        splits_discarded = splits_discarded + 1
		discard = True

        if only_balancer_splits == True:
            if (is_balancer_split(ns, split, split['time']) == False):
	        splits_discarded = splits_discarded + 1
		discard = True

        found = False
        try:
            for ix in range(bookmark, len(list_splits)):
                chunk = list_splits[ix]
                bookmark = ix
                if (fieldorder_cmp(split['details']['before']['min'], chunk['min'], 'gte') and
                        fieldorder_cmp(split['details']['before']['max'], chunk['max'], 'lte')):
                    found = True
                    chunk['splits'] = chunk['splits'] + 1
		    if (discard):
                        chunk['discards'] = chunk['discards'] + 1
                    break
        except TypeError as e:
            print('typeerror: split: ' + dumps(split) +
                  ', chunk: ' + dumps(chunk))
            print(e)

        if found:
            if(verbose):
                print(
                    'Found: ' + dumps(split['details']['before']) + ' included in ' + dumps(chunk))
        else:
            new = collections.OrderedDict()
            new['min'] = split['details']['before']['min']
            new['max'] = split['details']['before']['max']
            new['splits'] = 1
            new['discards'] = 0
            if (discard):
                new['discards'] = 1
            list_splits.append(new)
            if(verbose):
                print('New! ' + dumps(new))

    if (no_progressbar == False):
        pbar.finish()


def print_stats(db, ns, list_splits, t0, t1):

    split_pattern = re.compile('split')
    length_splits = len(list_splits)
    chunks_total = db.chunks.count({'ns': ns})
    splits_total = db.changelog.count(
        {'what': split_pattern, 'ns': ns, 'details.number': {'$ne': 1}, 'time': {'$gte': t0}})

    if (verbose):
        print('Ranges that underwent a split:')
        for chunk in list_splits:
            print('  ' + dumps(chunk))

    print('Statistics:')

    print('   Splits: ' + str(splits_total - splits_discarded))

    print('   Ranges involved in a split: ' + str(length_splits))

    if (exclude_balancer_splits):
        reason = '   Splits discarded because initiated by the balancer: '

    if (only_balancer_splits):
        reason = '   Splits discarded because not initiated by the balancer: '

    if (exclude_balancer_splits or only_balancer_splits):
        print(reason +
	      str(splits_discarded) + '/' + str(splits_total) + ' (' +
	      str(round(float(splits_discarded)/float(splits_total) * 100, 2)) + '%)')

    print('   Chunks in the collection at ' +
          str(t0) + ': ' + str(chunks_total - splits_total))
    print('   Chunks in the collection at ' +
          str(t1) + ': ' + str(chunks_total))


def build_split_distribution(db, ns, no_timeout):

    print('Building split distribution...')

    chunks_son = db['chunks'].with_options(
        codec_options=CodecOptions(document_class=SON))
    i_splits = 0

    chunks_count = db['chunks'].count({'ns': ns})

    if (no_progressbar == False):
        pbar = ProgressBar(
            widgets=[Percentage(), Bar()], maxval=chunks_count).start()
        bar_i = 0

    bookmark = 0
    chunks_cursor = chunks_son.find({'ns': ns}, {
                                    '_id': 0, 'min': 1, 'max': 1}, no_cursor_timeout=no_timeout).sort([('min', pymongo.ASCENDING)])
    while(1):
        try:
            chunk_son = chunks_cursor.next()
        except StopIteration:
            break

        chunk = collections.OrderedDict()
        chunk['min'] = chunk_son['min']
        chunk['max'] = chunk_son['max']
        (split, bookmark) = find_split(list_splits, bookmark, chunk)
        if (split != None):
            # Insert the split, offset by split count
	    chunk['splits'] = split['splits'] - split['discards']
            final_list.append(chunk)
            try:
                for skip in range(split['splits']):
                    chunks_cursor.next()
            except StopIteration:
                print('Warning: unexpected end of iteration')
                print('skip ' + str(skip) + ' of ' + str(split['splits']))
                break
        else:
            # insert chunk
            chunk['splits'] = 0
            final_list.append(chunk)

        if (no_progressbar == False):
            bar_i = bar_i + 1
            pbar.update(bar_i)

    if (no_progressbar == False):
        pbar.finish()


def plot_results(t0, t1):

    length_final_list = len(final_list)

    if length_final_list <= 1:
        print('Not enough chunks to plot results. Please specify a higher --starttime.')
        return

    x = [None] * length_final_list
    y = [None] * length_final_list

    i = 0
    for entry in final_list:
        x[i] = i
        y[i] = entry['splits']
        i = i + 1

    fig, ax = plt.subplots()

    plt.xlim(0, len(final_list) - 1)
    # plt.ylim(bottom=0)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))

    (delta_hours, delta_str) = get_time_delta_hours(t0, t1)

    plt.suptitle('Split distribution: ' + ns, fontsize=14)
    plt.title(t0.strftime(date_strfmt) + ' -> ' + t1.strftime(date_strfmt) +
              ' (' + delta_str + ')', fontsize=10)
    plt.ylabel('Splits')
    plt.xlabel('Ranges')

    cid = fig.canvas.mpl_connect('button_press_event', onclick)

    ax.plot(x, y)
    plt.show()


def get_starttime(t0, t1, args):

    tstart = t0

    if args.starttime:
        tstart = dateutil.parser.parse(args.starttime)

    if tstart < t0 or tstart > t1:
        raise Exception('starttime of ' + str(tstart) +
                        ' is not within the time window [' + str(t0) + ', ' + str(t1) + ']')
    else:
        t0 = tstart

    return t0, t1


def validate_actionlog(db, t0):

    # TODO:
    # Check for heterogenous data types - warn out if so (this script doesn't support full BSON type ordering)
    for resharded in db['changelog'].find({'ns': ns, 'what': 'shardCollection.end', 'time': {'$gte': t0}}).sort([('time', pymongo.DESCENDING)]).limit(1):
        resharded_time = resharded['time']
        print(ns + ' was sharded on ' + str(resharded_time) +
              ', current starttime: ' + str(t0) + '. Please specify a higher --starttime.')
        raise Exception('Time window cannot cover shardCollection')

    for merged in db['changelog'].find({'ns': ns, 'what': 'merge', 'time': {'$gte': t0}}).sort([('time', pymongo.DESCENDING)]).limit(1):
        merged_time = merged['time']
        print(ns + ' underwent a chunk merge on ' + str(merged_time) + ', current starttime: ' +
              str(t0) + '. This tool does not support mergeChunk. Please specify a higher --starttime.')
        raise Exception('Time window cannot cover chunk merge')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--mongo_uri', type=str,
                        help='connection string')
    parser.add_argument('-s', '--starttime', type=str,
                        help='specify a start time (UTC 8601)')
    parser.add_argument('-v', '--verbose',
                        help='print verbose information', action='store_true')
    parser.add_argument('-n', '--no_progressbar',
                        help='disable progress bar', action='store_true')
    parser.add_argument(
        '-N', '--no_timeout', help='use noCursorTimeout (advanced)', action='store_true')
    parser.add_argument(
        '-x', '--no_balancer_splits', help='try to exclude balancer initiated splits (slow)', action='store_true')
    parser.add_argument(
        '-b', '--only_balancer_splits', help='try to visualise only balancer initiated splits (slow)', action='store_true')
    parser.add_argument('namespace', nargs=1, type=str, help='namespace')
    args = parser.parse_args()

    if args.mongo_uri:
        uri = args.mongo_uri
    else:
        uri = 'mongodb://localhost:27017'

    if args.verbose:
        verbose = True

    if args.no_progressbar:
        no_progressbar = True

    # TODO mutually exclusive

    if args.no_balancer_splits:
        exclude_balancer_splits = True

    if args.only_balancer_splits:
        only_balancer_splits = True

    ns = args.namespace[0]

    db = MongoClient(uri)['config']

    if db['collections'].count({'_id': ns, 'dropped': False}) == 0:
        raise Exception('Namespace ' + ns +
                        ' does not exist or is not sharded')

    (t0, t1) = get_time_extent(db)
    (t0, t1) = get_starttime(t0, t1, args)

    validate_actionlog(db, t0)

    print('Time window: [' + str(t0) + ', ' + str(t1) + ']')

    build_split_list(db, ns, t0, t1)
    build_split_distribution(db, ns, args.no_timeout)

    print_stats(db, ns, list_splits, t0, t1)
    plot_results(t0, t1)
