import os
import sys
from random import shuffle

try:  # if Python >= 3.3 use new high-res counter
    from time import perf_counter as time
except ImportError:  # else select highest available resolution counter
    if sys.platform[:3] == 'win':
        from time import clock as time
    else:
        from time import time


def write_test(block_size, blocks_count):
    f = os.open("testfile", os.O_CREAT | os.O_WRONLY, 0o777)

    took = []
    for i in range(blocks_count):
        buff = os.urandom(block_size)
        start = time()
        os.write(f, buff)
        os.fsync(f)
        t = time() - start
        took.append(t)

    os.close(f)
    return took


def read_test(block_size, blocks_count):
    f = os.open("testfile", os.O_RDONLY, 0o777)

    offsets = list(range(0, blocks_count * block_size, block_size))
    shuffle(offsets)

    took = []
    for i, offset in enumerate(offsets, 1):
        start = time()
        os.lseek(f, offset, os.SEEK_SET)
        buff = os.read(f, block_size)
        t = time() - start
        if not buff: break
        took.append(t)

    os.close(f)
    return took


def disk_test():
    results = {}
    write_time = write_test(2048, 512)
    read_time = read_test(2048, 512)
    results['write'] = write_time[0]
    results['read'] = read_time[0]
    return results
