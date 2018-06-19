# Third party imports.
import pytest

# Custom imports.
import network
import simulation


def test_init_traffic():
    """Test that traffic is correctly initialised in the network."""
    graph = network.new_network(1000, 500)
    f = 0.5
    simulation.init_traffic(graph, f)
    for node, node_data in graph.nodes(data=True):
        assert isinstance(node_data["old_particles"], list)
        assert len(node_data["old_particles"]) == 0
    num_particles = sum(
        bool(node_data["particle"])
        for _, node_data in graph.nodes(data=True))
    measured_f = num_particles / len(graph.nodes())
    assert measured_f > f * 0.9
    assert measured_f < f * 1.1


def test_run_simulation():
    """Test that all particles are updated the correct amount of times."""
    graph = network.new_network(100, 50)
    simulation.init_traffic(graph, 0.5)
    def update_particle(graph, node, timestep):
        if "updates" not in graph.node[node]:
            graph.node[node]["updates"] = -1
        graph.node[node]["updates"] += 1
        assert timestep == graph.node[node]["updates"]
    simulation.run_simulation(graph, update_particle, 10, print_=False)
