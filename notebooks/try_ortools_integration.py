# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.11.2
#   kernelspec:
#     display_name: tmpsimulator
#     language: python
#     name: tmpsimulator
# ---

# + tags=[]
from ridepy.util.dispatchers_cython import optimize_stoplists
from ridepy.data_structures_cython import InternalRequest, TransportationRequest, StopAction, Stoplist, Stop, LocType
from ridepy.util.spaces_cython import Manhattan2D

# + tags=[]
from numpy import inf
inf=1000000

# + tags=[]
r1 = TransportationRequest(1, 0, (-100, 0), (-100, 20))
r2 = TransportationRequest(1, 0, (100, 10), (100, 40))
r3 = TransportationRequest(1, 0, (-100, 5), (-100, 60))

ir1 = InternalRequest(99, 0, (-100, 0))
ir2 = InternalRequest(99, 0, (100, 0))

# + tags=[]
sl1_orig = Stoplist([
    Stop(ir1.location, ir1, StopAction.internal, 0, 0, 0, inf),
    Stop(r1.origin, r1, StopAction.pickup, 0, 0, 0, inf),
    Stop(r2.origin, r2, StopAction.pickup, 0, 0, 0, inf),
    Stop(r1.destination, r1, StopAction.dropoff, 0, 0, 0, inf),
    Stop(r2.destination, r2, StopAction.dropoff, 0, 0, 0, inf),
    ], LocType.R2LOC)

sl2_orig = Stoplist([
    Stop(ir2.location, ir2, StopAction.internal, 0, 0, 0, inf),
    Stop(r3.origin, r3, StopAction.pickup, 0, 0, 0, inf),
    Stop(r3.destination, r3, StopAction.dropoff, 0, 0, 0, inf),
    ], LocType.R2LOC)

# + tags=[]
for sl in [sl1_orig, sl2_orig]:
    print("-"*10)
    for s in sl:
        print(s.location)

# + tags=[]
sls_new = optimize_stoplists([sl1_orig, sl2_orig], Manhattan2D(), [10,10])

for sl in sls_new:
    print("-"*20)
    for s in sl:
        print(s.location, s.action)
# -


