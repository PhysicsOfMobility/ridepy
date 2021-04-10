from thesimulator.data_structures import Stop, StopAction
from thesimulator import data_structures_cython as cyds
from thesimulator import data_structures as pyds


def stoplist_from_properties(stoplist_properties, data_structure_module=pyds):
    return [
        data_structure_module.Stop(
            location=loc,
            request=data_structure_module.InternalRequest(
                request_id=-1, creation_timestamp=0, location=loc
            ),
            action=data_structure_module.StopAction.internal,
            estimated_arrival_time=cpat,
            occupancy_after_servicing=0,
            time_window_min=tw_min,
            time_window_max=tw_max,
        )
        for loc, cpat, tw_min, tw_max in stoplist_properties
    ]
