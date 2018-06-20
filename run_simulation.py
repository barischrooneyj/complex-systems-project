import graph
import particle_dynamics
import routing_table
import simulation


if __name__ == "__main__":
   graph = graph.new_network(10, 8)
   simulation.init_graph(graph, f=0.5)
   simulation.run_simulation(
      graph,
      particle_dynamics.send_from_routing_table,
      timesteps=10,
      send_router_update=routing_table.send_router_update)
   print(simulation.all_particles(graph))
