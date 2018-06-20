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


def init_network(graph, f, max_particles=1):
   """Initialize necessary node attributes and potentially set a fraction f of
   queue space as occupied with particles.

   """
   for node, node_data in graph.nodes(data=True):
      # Particles that previously reached this target.
      node_data["old_particles"] = []

      # A queue of particles at the node (one processed per timestep).
      node_data["particles"] = []
      node_data["max_particles"] = max_particles

      # An empty routing table set at timestep -1.
      node_data["routing_tables"] = {-1: {node: (0, node)}}

      # Generate initial traffic/particles.
      for _ in range(max_particles):
         if random.uniform(0, 1) < f:
            node_data["particles"].append(
               Particle(node, 0, random.sample(graph.nodes(), 1)[0]))


def move_particle(graph, from_node, to_node, timestep):
   """Move a particle to a node, generating a new particle if target reached.

   This is a lower-level function intended to be used by higher-level models of
   particle dynamics e.g. random_walk.

   NOTE: This function assumes the move has been checked prior to be valid.

   """
   # Update the particle's path.
   graph.node[from_node]["particles"][0].path += [(to_node, timestep)]

   # Move particle from one node to another.
   graph.node[to_node]["particles"].append(
      graph.node[from_node]["particles"].pop(0))

   # If target reached then retire old particle and generate new particle.
   if to_node == graph.node[to_node]["particles"][-1].target:
      graph.node[to_node]["old_particles"] += [
         graph.node[to_node]["particles"].pop()]
      random_start = random.sample(graph.nodes(), 1)[0]
      graph.node[to_node]["particles"].append(
         Particle(to_node, timestep, random_start))


class SimOrder(Enum):
   """The order that particles updates are applied each timestep."""
   Increasing = 1
   Random = 2


def run_simulation(graph, particle_update, timesteps, print_=True,
                   order=SimOrder.Random, router_update_interval=5,
                   send_router_update=None):
   """Run the particle_update on each node, for N timesteps."""
   for timestep in range(timesteps):
      print("Timestep: {}".format(timestep)) if print_ else None

      # Update routing tables if it's time.
      if send_router_update and timestep % router_update_interval == 0:
         for node in graph.nodes():
            send_router_update(graph, node, timestep)

      # Determine the order that particle updates are applied.
      all_nodes = list(graph.nodes(data=True))
      if order == SimOrder.Random:
         random.shuffle(all_nodes)

      # For each node that has a waiting particle, apply the particle update.
      particles_updated = set()
      for node, node_data in all_nodes:
         particles = graph.node[node]["particles"]
         if particles:
            particle = particles[0]
            if particle.id not in particles_updated:
               particle_update(graph, node, timestep)
               particles_updated.add(particle.id)


def latest_routing_table(graph, node, timestep):
   """The most recently updated routing table for node."""
   routing_tables = graph.node[node]["routing_tables"]
   latest_timestep = max(filter(lambda x: x < timestep, routing_tables.keys()))
   return routing_tables[latest_timestep]


def send_router_update(graph, current_node, timestep):
   """Send routing table updates to all neighbors."""
   current_table = latest_routing_table(graph, current_node, timestep)
   for neighbor_node in graph.neighbors(current_node):
      neighbor_table = latest_routing_table(graph, neighbor_node, timestep)

      def routing_table_entry(node):
         if node not in neighbor_table:
            return current_table[node]
         if node not in current_table:
            result = neighbor_table[node]
            return (result[0] + 1, result[1])
         # Else we have both and choose minimum cost. Cost is found at index 0
         # and the node via which to travel at index 1.
         if current_table[node][0] < neighbor_table[node][0] + 1:
            return current_table[node]
         return (neighbor_table[node][0] + 1, neighbor_table[node][1])

      graph.node[neighbor_node]["routing_tables"][timestep + 1] = {
         node: routing_table_entry(node)
         for node in set(current_table).union(set(neighbor_table))
      }


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
   routing_table = latest_routing_table(graph, current_node, timestep)
   particle = graph.node[current_node]["particles"][0]
   if particle.target in routing_table:
      move_particle(graph, current_node, routing_table[particle.target][1], timestep)
   else:
      random_walk(graph, current_node, timestep)
      # particles = graph.node[current_node]["particles"]
      # particles.append(particles.pop(0))


def all_particles(graph):
   """Collect all particles after a simulation."""
   return list(itertools.chain.from_iterable([
      node_data["old_particles"] + node_data["particles"]
      for _, node_data in graph.nodes(data=True)
   ]))


if __name__ == "__main__":
   graph = network.new_network(10, 8)
   init_network(graph, f=0.5)
   run_simulation(graph, send_from_routing_table, timesteps=10,
                  send_router_update=send_router_update)
   print(all_particles(graph))
