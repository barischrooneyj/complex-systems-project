# Standard library imports.
import random

# Custom imports.
import routing_table
from simulation import move_particle, send_new_particle


def random_walk(graph, current_node, timestep):
   """Apply a particle update using RW dynamics."""
   for neighbor_node in graph.neighbors(current_node):
      # If a neighbor is free then apply update.
      if (len(graph.node[neighbor_node]["particles"])
          < graph.node[neighbor_node]["max_particles"]):
         move_particle(graph, current_node, neighbor_node, timestep)
         return


def detour_at_obstacle(network, current_node, timestep):
   """Apply a particle update using DO dynamics."""
   particle = network.node[current_node]["particles"][0]

   # Calculate length to target from each free neighbor.
   path_lengths = defaultdict(lambda: [])
   for neighbor_node in network.neighbors(current_node):
      node_data = network.node[neighbor_node]
      if len(node_data["particles"]) < node_data["max_particles"]:
         neighbor_length = len(nx.shortest_path(
            network, neighbor_node, particle.target))
         path_lengths[neighbor_length] += [neighbor_node]

   # There may be NO path available.
   if not path_lengths.keys(): return

   # Else choose one of the shortest paths.
   next_node = random.sample(path_lengths[min(path_lengths.keys())], 1)[0]
   move_particle(network, current_node, next_node, timestep)


def send_from_routing_table(graph, current_node, timestep):
   """Send the particle if in routing table, else re-queue the particle."""
   table = routing_table.latest_routing_table(graph, current_node, timestep)
   particle = graph.node[current_node]["particles"][0]
   if particle.target in table:
      move_particle(graph, current_node, table[particle.target][1], timestep)
   else:
      random_walk(graph, current_node, timestep)


def gossip(graph, current_node, timestep, k_neighbors=None, state_update=None):
   """Update gossip state, and send gossip info to k random neighbors."""

   # First process any previously received particles (gossip messages).
   while graph.node[current_node]["particles"]:
      particle = graph.node[current_node]["particles"].pop(0)
      graph.node[current_node]["data"] = state_update(
         graph.node[current_node]["data"], particle.data)

   def set_gossip_info(particle):
      """Assign the node's gossip info to the particle."""
      particle.data = graph.node[current_node]["data"]
      return particle

   # Send updated gossip state to a maximum k neighbors.
   all_neighbors = list(graph.neighbors(current_node))
   k_neighbors = random.sample(all_neighbors, k=min(len(all_neighbors), k_neighbors))
   for neighbor_node in k_neighbors:
      send_new_particle(graph, current_node, neighbor_node, timestep, set_gossip_info)
