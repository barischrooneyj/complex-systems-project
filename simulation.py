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


def init_graph(graph, particle_density=0, max_node_particles=1,
               particle_f=particle.random_target, gossip_initiators=0,
               initial_data_f=None):
   """Initialize each node's attributes based on the given parameters."""
   for node, node_data in graph.nodes(data=True):
      # Incoming queue of particles.
      node_data["particles"] = []

      # The maximum capacity of particles at this node.
      node_data["max_particles"] = max_node_particles

      # Particles that arrived to a node at full capacity.
      node_data["overflow_particles"] = []

      # Particles that reached their target.
      node_data["old_particles"] = []
      
      # An empty routing table, tagged at time-step -1 (pre-simulation).
      node_data["routing_tables"] = {-1: {node: (0, node)}}

      # The initial data that this node may have.
      node_data["data"] = initial_data_f() if initial_data_f else None

      # Generate initial particles based on 'particle_density'.
      for _ in range(max_node_particles):
         if random.uniform(0, 1) < particle_density:
            node_data["particles"].append(particle_f(graph, node))


def send_new_particle(graph, start_node, target_node, timestep,
                      particle_f=None):
   """Create and send a new particle from one node to another."""
   node_particle = particle.Particle(start_node, timestep, target_node)
   if particle_f:
      node_particle = particle_f(node_particle)
   graph.node[start_node]["particles"] = (
      [node_particle] + graph.node[start_node]["particles"])
   move_particle(graph, start_node, target_node, timestep, regen=False)


def move_particle(graph, from_node, to_node, timestep, regen=True):
   """Attempt to move a particle across a link.

   This is a lower-level function intended to be used by higher-level models of
   particle dynamics e.g. random_walk.

   If the target node is at capacity the particle will be added to the target
   node's list of overflowed particles.

   """
   # Check if particle already moved this time-step.
   particle = graph.node[from_node]["particles"][0]
   if particle.path and particle.path[-1][1] == timestep:
      raise ValueError("Particle {} already moved in time-step {}".format(
         particle.id, timestep))

   # Update the particle's path.
   particle = graph.node[from_node]["particles"].pop(0)
   particle.path += [(to_node, timestep)]

   # If target node is at capacity then overflow particle.
   if (len(graph.node[to_node]["particles"])
       >= graph.node[to_node]["max_particles"]):
      graph.node[to_node]["overflow_particles"].append(particle)

   # Else move particle across link.
   else:
      graph.node[to_node]["particles"].append(particle)


class SimOrder(Enum):
   """The order updates are applied to nodes each time-step."""
   Increasing = 1
   Random = 2


def run_simulation(graph, update_f, order=SimOrder.Random, timesteps=10,
                   additional_update_fs=[], collect=None):
   """Run the update function on each node at each time-step.

   Additional update functions can also be passed, each to be run every N
   time-steps. These additional functions f need to be passed as a list
   additional_update_fs=[(f, N)].

   """

   # Setup data collection and run once before simulation.
   collected_data = {}
   if collect:
      collected_data[-1] = collect(graph)

   # Apply update dynamics and data collection at each time-step.
   for timestep in range(timesteps):
      print("Timestep: {}".format(timestep))

      # Determine the order that particle updates are applied.
      all_nodes = list(graph.nodes(data=True))
      if order == SimOrder.Random:
         random.shuffle(all_nodes)

      # For each node apply the update function.
      for node, node_data in all_nodes:
         update_f(graph, node, timestep)

      # Run any additional update functions if given.
      for (additional_update_f, update_interval) in additional_update_fs:
         if timestep % update_interval == 0:
            for node in graph.nodes():
               additional_update_f(graph, node, timestep)

      # Run data collection if requested.
      if collect:
         collected_data[timestep] = collect(graph)

   return collected_data


def all_particles(graph):
   """Collect all particles after a simulation."""
   return list(itertools.chain.from_iterable([
      node_data["old_particles"] + node_data["particles"] +
      node_data["overflow_particles"]
      for _, node_data in graph.nodes(data=True)
   ]))
