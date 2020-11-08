from thesimulator.data_structures import Stop, StopAction


def stoplist_from_properties(stoplist_properties):
    return [
        Stop(
            location=loc,
            request=None,
            action=StopAction.internal,
            estimated_arrival_time=cpat,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]
