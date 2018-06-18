from collections import defaultdict
import networkx as nx
import random

import network

next_unique_id = 0
def get_unique_id():
   """"""
   global next_unique_id
   next_unique_id += 1
   return next_unique_id - 1


class Particle():
   """A particle kept track of through a simulation."""
   def __init__(self, start_node, start_timestep, target_node):
      self.start = start_node
      self.start_timestep = start_timestep
      self.target = target_node
      self.path = []  # An ordered list of (node, timestep).
      self.id = get_unique_id()


def init_network(network, f):
   """Set a fraction f of nodes as occupied with particles."""
   for node, node_data in graph.nodes(data=True):
      node_data["old_particles"] = []
      node_data["particle"] = (
         None if random.uniform(0, 1) >= f
         else Particle(node, 0, random.sample(graph.nodes(), 1)[0])
      )


def move_particle(graph, from_node, to_node, timestep):
   """Move a particle from one node to another, reset if target reached."""
   # Update the particle's path.
   particle = graph.node[from_node]["particle"]
   particle.path += [(to_node, timestep)]
   # Move particle from one node to another.
   graph.node[to_node]["particle"] = particle
   graph.node[from_node]["particle"] = None
   # Generate new particle, and save old, if target reached.
   if to_node == particle.target:
      graph.node[to_node]["old_particles"] += [particle]
      graph.node[to_node]["particle"] = Particle(
         to_node, timestep, random.sample(graph.nodes(), 1)[0])


def run_simulation(graph, particle_update, timesteps):
   """Run the particle_update on all particles for N timesteps."""
   for timestep in range(timesteps):
      print("Timestep: {}".format(timestep))
      # For each node that has a particle apply the particle update.
      particles_updated = set()
      for node, node_data in graph.nodes(data=True):
         particle = graph.node[node]["particle"]
         if particle and particle.id not in particles_updated:
            particle_update(graph, node, timestep)
            particles_updated.add(particle.id)
   return graph


def random_walk(graph, current_node):
   """Apply network updates using RW dynamics."""
   for neighbor_node in graph.neighbors(current_node):
      # If a neighbor is free then apply update.
      if not graph.node[neighbor]["particle"]:
         move_particle(graph, current_node, neighbor_node)
         return


def detour_at_obstacle(network, current_node, timestep):
   """Apply network updates using RW dynamics."""
   particle = network.node[current_node]["particle"]

   # Calculate length to target from each free neighbor.
   path_lengths = defaultdict(lambda: [])
   for neighbor_node in filter(
         lambda n: not network.node[n]["particle"],
         network.neighbors(current_node)):
      neighbour_length = len(nx.shortest_path(
         network, neighbor_node, particle.target))
      path_lengths[neighbour_length] += [neighbor_node]

   # There may be NO path available.
   if not path_lengths.keys(): return

   # Else choose one of the shortest paths.
   next_node = random.sample(path_lengths[min(path_lengths.keys())], 1)[0]
   move_particle(network, current_node, next_node, timestep)


if __name__ == "__main__":
   graph = network.new_network(10, 8)
   init_network(graph, f=0.5)
   graph = run_simulation(graph, detour_at_obstacle, timesteps=10)
   for node, node_data in graph.nodes(data=True):
      for particle in node_data["old_particles"]:
         print(particle.path)
