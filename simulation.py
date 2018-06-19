# Standard library imports.
from collections import defaultdict
from enum import Enum
import itertools
import random

# Third party imports.
import networkx as nx

# Custom imports.
import network


# Next available unique ID.
next_unique_id = 0

def get_unique_id():
   """Return a new unique ID."""
   global next_unique_id
   next_unique_id += 1
   return next_unique_id - 1


class Particle():
   """A particle that is kept track of through a simulation."""

   def __init__(self, start_node, start_timestep, target_node):
      self.start = start_node
      self.start_timestep = start_timestep
      self.target = target_node
      self.path = []  # An ordered list of (node, timestep).
      self.id = get_unique_id()

   def __repr__(self):
      """Useful representation of a Particle for debugging."""
      return "id: {}, (start, target): ({}, {}), path: {}".format(
         self.id, self.start, self.target, self.path)


def init_traffic(graph, f):
   """Set a fraction f of nodes as occupied with particles."""
   for node, node_data in graph.nodes(data=True):
      node_data["old_particles"] = []
      node_data["particle"] = (
         None if random.uniform(0, 1) >= f
         else Particle(node, 0, random.sample(graph.nodes(), 1)[0])
      )


def move_particle(graph, from_node, to_node, timestep):
   """Move a particle to a node, generating a new particle if target reached.

   This is a lower-level function intended to be used by higher-level models of
   particle dynamics e.g. random_walk.

   NOTE: This function assumes the move has been checked prior to be valid.

   """
   # Update the particle's path.
   particle = graph.node[from_node]["particle"]
   particle.path += [(to_node, timestep)]

   # Move particle from one node to another.
   graph.node[to_node]["particle"] = particle
   graph.node[from_node]["particle"] = None

   # If target reached then generate new particle and save old particle.
   if to_node == particle.target:
      graph.node[to_node]["old_particles"] += [particle]
      graph.node[to_node]["particle"] = Particle(
         to_node, timestep, random.sample(graph.nodes(), 1)[0])


class SimOrder(Enum):
   """The order that paricle updates are applied each timestep."""
   Increasing = 1
   Random = 2


def run_simulation(graph, particle_update, timesteps,
                   print_=True, order=SimOrder.Random):
   """Run the particle_update on all particles for N timesteps."""
   for timestep in range(timesteps):
      print("Timestep: {}".format(timestep)) if print_ else None

      # Determine the order that particle updates are applied.
      all_nodes = list(graph.nodes(data=True))
      if order == SimOrder.Random:
         random.shuffle(all_nodes)

      # For each node that has a particle apply the particle update.
      particles_updated = set()
      for node, node_data in graph.nodes(data=True):
         particle = graph.node[node]["particle"]
         if particle and particle.id not in particles_updated:
            particle_update(graph, node, timestep)
            particles_updated.add(particle.id)


def random_walk(graph, current_node, timestep):
   """Apply a particle update using RW dynamics."""
   for neighbor_node in graph.neighbors(current_node):
      # If a neighbor is free then apply update.
      if not graph.node[neighbor_node]["particle"]:
         move_particle(graph, current_node, neighbor_node, timestep)
         return


def detour_at_obstacle(network, current_node, timestep):
   """Apply a particle update using DO dynamics."""
   particle = network.node[current_node]["particle"]

   # Calculate length to target from each free neighbor.
   path_lengths = defaultdict(lambda: [])
   for neighbor_node in filter(
         lambda n: not network.node[n]["particle"],
         network.neighbors(current_node)):
      neighbor_length = len(nx.shortest_path(
         network, neighbor_node, particle.target))
      path_lengths[neighbor_length] += [neighbor_node]

   # There may be NO path available.
   if not path_lengths.keys(): return

   # Else choose one of the shortest paths.
   next_node = random.sample(path_lengths[min(path_lengths.keys())], 1)[0]
   move_particle(network, current_node, next_node, timestep)


def all_particles(graph):
   """Collect all particles after a simulation."""
   return list(itertools.chain.from_iterable([
      node_data["old_particles"]
      for _, node_data in graph.nodes(data=True)
   ]))


if __name__ == "__main__":
   graph = network.new_network(10, 8)
   init_traffic(graph, f=0.5)
   run_simulation(graph, detour_at_obstacle, timesteps=10)
   print(all_particles(graph))
