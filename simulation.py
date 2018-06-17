import network


def run_simulation(graph, dynamics, timesteps):
   """Run a simulation of a network for N timesteps with given dynamics."""
   for timestep in range(timesteps):
      print("Timestep: {}".format(timestep))
      for node, node_data in graph.nodes(data=True):
         # Run the given dynamics on each node. Perhaps the dynamics should be a
         # function from (Network, NodeId) -> [(NodeId, Node)]. Which can be read
         # as given a network and a node on which to calculate particle dynamics,
         # then return the new states for any modified nodes.
         print("node {} node_data {}".format(node, node_data))
   return graph


if __name__ == "__main__":
   graph = network.new_network(3, 2)
   print(graph)
   final_graph = run_simulation(graph, None, 10)
   print(graph)
