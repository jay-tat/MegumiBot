import asyncio
import itertools
import random


class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def swap(self, x: int, y: int):
        temp = self._queue[x]
        self._queue[x] = self._queue[y]
        self._queue[y] = temp
        return

    def shuffle(self):
        random.shuffle(self._queue)

    def get_title(self, index: int):
        return self._queue[index].source.title

    def remove(self, index: int):
        del self._queue[index]
