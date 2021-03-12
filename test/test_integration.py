from .simulate_script import simulate_on_r2


def test_simulate_script():
    simulate_on_r2(num_vehicles=10, rate=10, num_requests=1000, seat_capacities=4)
