import routing_table
from simulation import move_particle


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
      # particles = graph.node[current_node]["particles"]
      # particles.append(particles.pop(0))

