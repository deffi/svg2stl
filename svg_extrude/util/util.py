from typing import Iterable, Generator, Sequence
from contextlib import contextmanager
from collections import defaultdict

# TODO factor out util.iter?


def filter_repetition(items: Sequence) -> Generator:
    if items:
        i = items[0]
        yield i

        for item in items[1:]:
            if item != i:
                i = item
                yield i


# TODO rename to each_with_remaining
def with_remaining(items: Sequence):
    """For each items, yields a tuple with (a) that item, and (b) a slice of the
    original sequence containing all items after that item."""
    for index in range(len(items)):
        yield items[index], items[index+1:]


def group_by(items: Iterable, key_function) -> dict:
    """Returns a dict where the keys are determined by calling key_function with
    an item and the values are lists of items that resulted in that key."""
    result = defaultdict(list)
    for item in items:
        result[key_function(item)].append(item)
    return result


def arg_min(candidates: Iterable, target=lambda x: x):
    # """Returns the value from candidates where the target function returns the
    # lowest value. The target function is called once for each candidate."""

    minimum_candidate = None
    minimum_tgt = None

    for candidate in candidates:
        tgt = target(candidate)
        if minimum_tgt is None or tgt < minimum_tgt:
            minimum_candidate = candidate
            minimum_tgt = tgt

    return minimum_candidate


def identity(x):
    return x


# TODO unit test and review
@contextmanager
def conditional(condition, generator, alternative):
    if condition:
        with generator as gen:
            yield gen
    else:
        yield alternative