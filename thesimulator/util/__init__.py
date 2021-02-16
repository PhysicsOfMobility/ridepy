import random
import string
import numpy as np
import pandas as pd


def short_uuid():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class smartVectorize:
    def __init__(self, base_fn, vectorized_fn=None, self_=None):
        self.base_fn = base_fn
        self.vectorized_fn = vectorized_fn
        self.self_ = self_

    def __get__(self, obj, objtype=None):
        return type(self)(
            base_fn=self.base_fn, vectorized_fn=self.vectorized_fn, self_=obj
        )

    def __call__(self, *args, **kwargs):
        shape = None

        if args:
            shape = np.shape(args[0])
            if not all(np.shape(arg) == shape for arg in args[1:]):
                raise ValueError("vector shapes must match")

        if kwargs:
            if shape is None:
                shape = np.shape(list(kwargs.values())[0])
            if not all(np.shape(v) == shape for v in kwargs.values()):
                raise ValueError("vector shapes must match")

        if len(shape) == self.self_.n_dim - 1:
            return self.base_fn(self.self_, *args, **kwargs)
        elif self.self_.n_dim - 1 < len(shape) <= self.self_.n_dim:
            if self.vectorized_fn is None:
                if args and not kwargs:
                    res = [self.base_fn(self.self_, *arg) for arg in zip(*args)]
                elif not args and kwargs:
                    res = [
                        self.base_fn(self.self_, **kwarg)
                        for kwarg in map(
                            dict,
                            zip(*[[(k, vv) for vv in v] for k, v in kwargs.items()]),
                        )
                    ]
                else:
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

                if args:
                    atype = type(args[0])
                elif kwargs:
                    atype = type(list(kwargs.values())[0])
                else:
                    atype = None

                if atype == pd.Series:
                    return pd.Series(res)
                else:
                    return np.array(res)

            else:
                return self.vectorized_fn(self.self_, *args, **kwargs)
        else:
            raise ValueError(
                f"Got {len(shape)+1}-dimensional object "
                f"instead of expected {self.ndim} dimensions"
            )

    def vectorized(self, vectorized_fn):
        return type(self)(
            base_fn=self.base_fn, vectorized_fn=vectorized_fn, self_=self.self_
        )
