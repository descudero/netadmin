from model.path import Path
import networkx as nx

data = [{'to_id': 1, 'to_ip': "1.1.1.2", 'from_id': 2, 'from_ip': "1.1.1.1"},
        {'to_id': 2, 'to_ip': "1.1.2.2", 'from_id': 3, 'from_ip': "1.1.2.1"},
        {'to_id': 3, 'to_ip': "1.1.3.2", 'from_id': 4, 'from_ip': "1.1.3.1"}
        ]

nodes = {edge['from_id'] for edge in data} | {edge['to_id'] for edge in data}

edges = [Path(**edge) for edge in data]

G = nx.Graph()
G.add_nodes_from(nodes)

for edge in data:
    G.add_edge(edge['to_id'], edge['from_id'])
    G.edges[edge['to_id'], edge['from_id']]['attr'] = {str(edge['to_id']) + 'ip': edge['to_ip'],
                                                       str(edge['from_id']) + 'ip': edge['from_ip']}

shortest = nx.shortest_path(G, source=1, target=4)
ip_go = []
ip_return = []
for index in range(len(shortest) - 1):
    ip_return.append(G.edges[shortest[index], shortest[index + 1]]['attr'][f'{shortest[index]}ip'])
    ip_go.append(G.edges[shortest[index], shortest[index + 1]]['attr'][f'{shortest[index + 1]}ip'])

print(list(reversed(ip_return)))
print(ip_go)
