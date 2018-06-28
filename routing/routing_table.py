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
