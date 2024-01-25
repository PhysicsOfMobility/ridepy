Glossary
========

.. glossary::
    :sorted:

    estimated arrival time
        Property of each stop. It is the time at which the vehicle was expected to reach the stop at the latest insertion of any stop (at which point the times are updated by the dispatcher).

        Legacy synonym: Cached Predicted Arrival Time (``CPAT``).

    time window min
        The earliest time at which a stop can be served.

        Legacy synonym: Earliest Allowed Service Time (``EAST``).

    time window max
        The maximum service time beyond which a stop may not be delayed.

        Legacy synonym: Latest Allowed Service Time (``LAST``).

    current position element
        ``CPE``, dummy stop. It must always be the first entry of each valid stoplist. It denotes the current position of the vehicle.

    vehicle
        A transporter. In reality, this could be a transit bus or a passenger car. The primary representation of a vehicle in the framework is a stoplist.

    fleet
        A set of transporters.

    dispatcher
        Algorithm that schedules the stops. In essence, the dispatcher is a mapping of an existing stoplist and a transportation request onto a modified stoplist and a cost of insertion/service.

    stoplist
        Ordered list of stops that define the route of a vehicle. The first element is the current position element (``CPE``), the other stops represent pick-up or drop-off of requests (passengers).

