# Standard library imports.
import random
import sys

# Third party imports.
import matplotlib.pyplot as plt
import numpy as np

# Custom imports.
import collect
import graph
import particle_dynamics
import routing_table
import simulation


class SimParam():
   """A set of parameters for one run of the simulation."""
   def __init__(self, network_size, avg_degree, gossip_k, max_node_particles,
                max_timesteps, state_update_f, expected_result_f, label):
      self.network_size = network_size
      self.avg_degree = avg_degree
      self.gossip_k = gossip_k
      self.max_node_particles = max_node_particles
      self.max_timesteps = max_timesteps
      self.state_update_f = state_update_f
      self.expected_result_f = expected_result_f
      self.label=label


def gossip_convergence(simParams):
   """Plot the convergence of gossip over different simulation parameters."""
   results = {}  # <nodes: (expected_result, result_per_timestep)>

   # For each given simulation parameters run the simulation.
   for simParam in simParams:

      # Setup the initial graph.
      G = graph.new_network(simParam.network_size, simParam.avg_degree)
      simulation.init_graph(G,
         max_node_particles=simParam.max_node_particles,
         initial_data_f=lambda: random.uniform(1, sys.maxsize)
      )

      # Calculate expected result from initial graph state.
      expected_result = simParam.expected_result_f([
         node_data["data"] for _, node_data in G.nodes(data=True)
      ])

      # Run the simulation and save collected data.
      collected_data = simulation.run_simulation(G,
         particle_update=lambda g, n, t: particle_dynamics.gossip(
            g, n, t, k_neighbors=simParam.gossip_k,
            state_update=simParam.state_update_f),
         timesteps=simParam.max_timesteps,
         collect=collect.avg_node_data
      )
      results[simParam.label] = (expected_result, collected_data)

   # Finally plot the results for each simulation parameter.
   for label, (expected_result, result_per_timestep) in results.items():
      error_at_timestep = np.abs(
         expected_result - list(result_per_timestep.values())) / expected_result
      plt.semilogy(error_at_timestep, label=label)
   plt.legend()
   plt.show()


if __name__ == "__main__":

   simParams = [
      SimParam(
         network_size=network_size,
         avg_degree=network_size - 1,
         gossip_k=int(network_size/10),
         max_node_particles=network_size-1,
         max_timesteps=100,
         state_update_f=min,
         expected_result_f=np.min,
         label="{} nodes".format(network_size)
      )
      for network_size in [10, 100, 1000]
   ]

   # gossip_convergence(simParams)

   simParams = [
      SimParam(
         network_size=100,
         avg_degree=100 - 1,
         gossip_k=gossip_k,
         max_node_particles=100,
         max_timesteps=100,
         state_update_f=min,
         expected_result_f=np.min,
         label="k = {}".format(gossip_k)
      )
      for gossip_k in [1, 5, 10, 20]
   ]

   gossip_convergence(simParams)
