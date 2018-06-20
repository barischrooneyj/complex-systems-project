# Standard library imports.
from collections import defaultdict
from enum import Enum
import itertools
import random

# Third party imports.
import networkx as nx

# Custom imports.
import graph
import particle
import particle_dynamics
import routing_table


def init_graph(graph, f, max_particles=1):
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
               particle.Particle(node, 0, random.sample(graph.nodes(), 1)[0]))


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
         particle.Particle(to_node, timestep, random_start))


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


def all_particles(graph):
   """Collect all particles after a simulation."""
   return list(itertools.chain.from_iterable([
      node_data["old_particles"] + node_data["particles"]
      for _, node_data in graph.nodes(data=True)
   ]))
