from __future__ import annotations

import datetime
import hashlib
import uuid
import random
import string
import sys
import warnings
from contextlib import contextmanager

import numpy as np
import dataclasses

from typing import Dict


MAX_SEAT_CAPACITY = sys.maxsize  # A very large int, because np.inf is a float


def get_short_uuid():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


def get_uuid():
    return uuid.uuid4().hex


def get_datetime_yymmddHHSS():
    return datetime.datetime.now().strftime("%y%m%d%H%M")


class smartVectorize:
    """
    Method decorator for TransportSpace and its subclasses.

    Wraps methods to make them handle both operations
    on single space coordinates, and array-like bunches of coordinates.
    * checks whether dimensions of coordinates match with the space
    * loops over method handling single coordinates as arguments
    * dispatches to vectorized version of the function is existent

    Use like:
    ```
    @smartVectorize
    def foo(self, u, v):
        return magic(u, v)
    ```
    and optionally in addition
    ```
    @foo.vectorized
    def foo(self, u, v):
        return np.magic(u, v)
    ```
    """

    def __init__(self, base_fn, vectorized_fn=None, self_=None):
        # when the decorator is first applied to a class method,
        # only base_fn will be supplied and stored
        self.base_fn = base_fn
        self.vectorized_fn = vectorized_fn
        self.self_ = self_

    def __get__(self, obj, objtype=None):
        # when the decorated method is called, a reference to the
        # instance of the class that the decorated method belongs to
        # will be stored in smartVectorize().self_ to be able to later access
        # the classes n_dim attribute
        self.self_ = obj
        return self

    def __call__(self, *args, **kwargs):
        # When the decorated method is called, check the following things:
        # 1) If multiple args or kwargs or both are supplied, the shapes of the
        #    data supplied shall match. This may be up for debate, as hypothetically
        #    it could e.g. be useful to be able to supply both "vectors", i.e. coordinates,
        #    *and* scalars. Currently this is not implemented, though.

        shape = None

        # check homogenous shape for all positional arguments
        if args:
            shape = np.shape(args[0])
            if not all(np.shape(arg) == shape for arg in args[1:]):
                raise ValueError("vector shapes must match")

        # check homogenous shape for all keyword arguments and, if applicable,
        # make sure they also match the positional arguments' ones
        if kwargs:
            if shape is None:
                shape = np.shape(list(kwargs.values())[0])
            if not all(np.shape(v) == shape for v in kwargs.values()):
                raise ValueError("vector shapes must match")

        # 2) now determine whether we are dealing with a single coordinate per
        #    argument, or with multiple, i.e. an array of arguments

        # if the number of dimensions of the arguments matches
        # (mind that a single number here has dimensionality 0)
        # the number of dimensions of the transport space, we are dealing
        # with single coordinate vectors. Hence we call the base_fn normally.
        # NOTE: this may produce weird errors if the "correct" shape is not detected by np.shape, e.g.
        # for a pd.Series of coordinate tuples. In this case, the condition will evaluate true and feed
        # the series to base_fn
        if len(shape) == self.self_.n_dim - 1:
            return self.base_fn(self.self_, *args, **kwargs)
        # if however we have dimensionality of the space plus one,
        # we need to iterate over multiple coordinate vectors.
        elif len(shape) == self.self_.n_dim:
            # if there is no dedicated vectorized version, we need to use a for-loop
            if self.vectorized_fn is None:
                # in case we have only positional arguments, this is easy:
                if args and not kwargs:
                    res = [self.base_fn(self.self_, *arg) for arg in zip(*args)]
                elif not args and kwargs:
                    # if we only have keyword arguments, we need to unpack them accordingly
                    # and feed them to the base function which only takes single
                    # coordinate vectors:
                    res = [
                        self.base_fn(self.self_, **kwarg)
                        for kwarg in map(
                            dict,
                            zip(*[[(k, vv) for vv in v] for k, v in kwargs.items()]),
                        )
                    ]
                else:
                    # if we have both, we just zip both of the variants above together
                    # and continue as before
                    res = [
                        self.base_fn(self.self_, *arg, **kwarg)
                        for arg, kwarg in zip(
                            zip(*args),
                            map(
                                dict,
                                zip(
                                    *[[(k, vv) for vv in v] for k, v in kwargs.items()]
                                ),
                            ),
                        )
                    ]

                return np.array(res)

            # ...if however there is a dedicated vectorized function,
            #    we just forward everything and return
            else:
                return self.vectorized_fn(self.self_, *args, **kwargs)

        # If the dimensions of the input do not match the dimensions of the space, we complain.
        else:
            raise ValueError(
                f"Got {len(shape)}-dimensional object "
                f"instead of expected {self.self_.n_dim} dimensions"
            )

    def vectorized(self, vectorized_fn):
        # to add a vectorized implementation of the decorated method,
        # it is decorated with smartVectorize().vectorized, which adds a reference
        # to the vectorized method to the smartVectorize instance
        self.vectorized_fn = vectorized_fn
        return self


def make_dict(item, raise_errors: bool = True) -> Dict:
    """
    Convert data structure object to dict
    Parameters
    ----------
    item
        the object to convert
    raise_errors
        If true, raise TypeError

    Returns
    -------
    resulting dictionary

    """
    if dataclasses.is_dataclass(item):
        return dataclasses.asdict(item)
    elif hasattr(item, "asdict"):
        return item.asdict()
    elif raise_errors:
        raise TypeError(f"Cannot convert object of type {type(item)} to dict")


def make_repr(cls, dct):
    return f"{cls}(" + ", ".join((map(lambda s: f"{s[0]}={s[1]!r}", dct.items()))) + ")"


def make_sim_id(params_json: str):
    return hashlib.sha224(params_json.encode("ascii", errors="strict")).hexdigest()


@contextmanager
def supress_stoplist_extraction_warning():
    with warnings.catch_warnings():
        warnings.filterwarnings(
            action="ignore",
            message=r"Extracting the C\+\+ stoplist will impact performance",
            category=UserWarning,
        )
        yield
