import numpy as np

def avg_node_data(graph):
    """The average data across all nodes."""
    return np.mean([
        node_data["data"]
        for _, node_data in graph.nodes(data=True)
    ])
