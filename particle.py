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
