"""
    Iterator for transforming loc trees

"""




class TransformPriorityException(Exception):
    '''Is raised when a lower priority is required to parse the current token'''
    def __init__(self, num):
        self.num = num

    def __int__(self):
        return self.num


class TransformIter:
    '''Pseudo-iterator for performing tree-list transforms relative to the current node'''

    def __init__(self, arr, i, parent=None):
        self.arr = arr
        self.i = i
        self.parent = parent # TODO: If specified index shifts on this iterator bubble up to the parent

        self.set_priority(0)

    def __radd__(self, other):
        return self.i

    def __len__(self):
        return len(self.arr)

    def get(self, key):
        if isinstance(key, (tuple, list)): # Get a range of tokens
            start = self.i + key[0] if key[0] != None else None
            stop = self.i + key[1] if key[1] != None else None

            return self.arr[start:stop]
        else:
            i = self.i + key
            if i < 0 or i >= len(self.arr):
                return None

            return self.arr[i]

    def __getitem__(self, key):
        if type(key) is slice:
            return self.get([key.start, key.stop])
            #raise Error() # slicing in Python 2 is unreliable for negatives
        else:
            return self.get(key)


    def set(self, key, value):
        if isinstance(key, (tuple, list)):
            if not isinstance(value, list):
                value = [value]

            start = self.i + key[0] if key[0] != None else None
            stop = self.i + key[1] if key[1] != None else None

            self.arr[start:stop] = value

            # Perform the operation and set the iterator to the last set element
            self.i = (start + len(value) - 1) if start != None else len(value) - 1
        else:
            i = self.i + key
            if i < 0 or i >= len(self.arr):
                raise Error()

            self.arr[self.i + key] = value

    def __setitem__(self, key, value):
        if type(key) is slice:
            return self.set([key.start, key.stop], value)
            #raise Error() # slicing in Python 2 is unreliable for negatives
        else:
            return self.set(key, value)


    def __delitem__(self, key):
        i = self.i + key

        if i < 0 or i >= len(self.arr):
            raise Error()

        if i <= self.i:
            self.i = self.i - 1

        del self.arr[i]



    def next(self):
        i = self.i + 1
        if i >= len(self.arr):
            return None
        else:
            it = TransformIter(self.arr, i, self.parent if self.parent else self)
            it.set_priority(self._priority)
            return it


    def set_priority(self, num):
        self._priority = num

    def priority(self, num):
        if self._priority < num:
            raise TransformPriorityException(num)
        return


    def zip(self, f):
        '''Combine everything before the current node and everything after using the current node as the delimeter and the given operation f'''
        left = self.get([None, 0])
        right = self.get([1, None])
        self.set([None, None], f(left, right))
