def dispatcherclass(f):
    """
    Use this decorator to create a callable Dispatcher class from a pure function. Use this to conveniently turn a
    pure function mapping a stoplist and a request to an updated stoplist into a dispatcher usable with ridepy.

    In principle, using dispatcher objects allow for easy configuration of dispatcher behavior. After instantiation
    of an object ``dispatcher``, the original dispatcher function is available as ``dispatcher(...)``. Currently on
    initiating a dispatcher object, ``loc_type`` can be supplied for interface compatibility with Cython dispatchers.

    Use like

    .. code-block:: python

        @dispatcherclass
        def MyFancyDispatcher(
            request: TransportationRequest,
            stoplist: Stoplist,
            space: TransportSpace,
            seat_capacity: int,
        ) -> SingleVehicleSolution: ...

    """

    class DispatcherClass:
        __name__ = f.__name__
        __qualname__ = f.__qualname__
        __doc__ = f.__doc__
        __module__ = f.__module__

        def __init__(self, loc_type=None):
            self.loc_type = loc_type

        def __call__(self, *args, **kwargs):
            return f(*args, **kwargs)

    return DispatcherClass
