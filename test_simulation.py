# Third party imports.
import matplotlib.pyplot as plt
import networkx as nx
import pytest

# Custom imports.
import network
import simulation


def test_init_traffic():
    """Test that traffic is correctly initialised in the network."""
    graph = network.new_network(1000, 500)
    f = 0.3
    max_node_particles = 10
    simulation.init_network(graph, f, max_particles=max_node_particles)
    for node, node_data in graph.nodes(data=True):
        assert isinstance(node_data["old_particles"], list)
        assert len(node_data["old_particles"]) == 0
    num_particles = sum(
        len(node_data["particles"])
        for _, node_data in graph.nodes(data=True))
    measured_f = num_particles / (len(graph.nodes()) * max_node_particles)
    assert measured_f > f * 0.9
    assert measured_f < f * 1.1


def test_run_simulation():
    """Test that all particles are updated the correct amount of times."""
    graph = network.new_network(100, 50)
    simulation.init_network(graph, 0.5)
    def update_particle(graph, node, timestep):
        if "updates" not in graph.node[node]:
            graph.node[node]["updates"] = -1
        graph.node[node]["updates"] += 1
        assert timestep == graph.node[node]["updates"]
    simulation.run_simulation(graph, update_particle, 10, print_=False)


def test_detour_at_obstacle():
    """Test that the DO particle update is applied correctly."""
    graph = nx.Graph()
    graph.add_nodes_from([1, 2, 3, 4, 5, 6])
    graph.add_edges_from(
        [(1, 5), (1, 2), (1, 3), (1, 4), (4, 3), (3, 2), (2, 6)])
    simulation.init_network(graph, f=0)
    graph.node[1]["particles"] = [simulation.Particle(1, 0, 6)]
    graph.node[2]["particles"] = [simulation.Particle(2, 0, 5)]
    graph.node[3]["particles"] = [simulation.Particle(3, 0, 5)]
    expected_id = graph.node[1]["particles"][0].id
    # Run the simulation on predictable order of nodes.
    simulation.run_simulation(graph, simulation.detour_at_obstacle, 1,
                              order=simulation.SimOrder.Increasing)
    # We expect the particle at either node 4 or 5.
    expected_at = list(map(
        lambda p: p[0].id if p else None,
        [graph.node[n]["particles"] for n in [4, 5]]
    ))
    assert expected_id in expected_at
