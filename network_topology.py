import random
import networkx as nx
from typing import List, Tuple


class NetworkTopologyGenerator:
    #Генератор топологии сети
    
    @staticmethod
    def create_topology(num_nodes: int, allow_bridges: bool = False) -> nx.Graph:
        """
        - Работа каждого из узлов реализуется в отдельном потоке;
        - Программа должна иметь возможность визуализации топологии сети и пошаговой визуализации RREQ и RREP запросов;
        - Количество узлов в сети до 50 шт.;
	    - Отсутствие мостов в графе топологии сети;
	    - Реберная связность графа не должна превышать (N-1)/2, где N число вершин в графе.
        - При allow_bridges=False граф не будет содержать мосты (будет пытаться убрать ;3)
        """
        graph = nx.Graph()
        
        # Создаем узлы
        for i in range(num_nodes):
            graph.add_node(i)
            
        # Максимальная реберная связность
        # не кол-во ребер
        max_edge_connectivity = int((num_nodes - 1) / 2)
        
        # Максимальное количество ребер
        max_total_edges = num_nodes * 2
        
        # создаем минимальное дерево
        nodes_list = list(range(num_nodes))
        random.shuffle(nodes_list)
        
        # Соединяем узлы в цепочку
        for i in range(1, num_nodes):
            # Соединяем с одним из предыдущих узлов
            prev = random.choice(nodes_list[:i])
            graph.add_edge(nodes_list[i], prev)
            
        # Добавляем дополнительные ребра для увеличения связности
        # но не превышая max_edges
        attempts = 0
        max_attempts = num_nodes * num_nodes * 2
        
        # Если мосты запрещены, сначала устраняем все мосты
        if not allow_bridges:
            while attempts < max_attempts and not NetworkTopologyGenerator.has_no_bridges(graph):
                attempts += 1
                
                # Проверяем не превысили ли лимит ребер
                if graph.number_of_edges() >= max_total_edges:
                    break
                
                # Выбираем случайную пару узлов
                u, v = random.sample(nodes_list, 2)
                
                if not graph.has_edge(u, v):
                    # Добавляем ребро для устранения мостов
                    graph.add_edge(u, v)
                    
        # Добавляем еще ребер, контролируя реберную связность
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            
            # Проверяем реберную связность и количество ребер
            try:
                current_connectivity = nx.edge_connectivity(graph)
                if current_connectivity >= max_edge_connectivity:
                    break
            except:
                pass
                
            if graph.number_of_edges() >= max_total_edges:
                break
                
            # Выбираем случайную пару узлов
            u, v = random.sample(nodes_list, 2)
            
            if not graph.has_edge(u, v):
                if allow_bridges:
                    # Просто добавляем ребро
                    graph.add_edge(u, v)
                else:
                    # Добавляем только если не создаст новых мостов
                    test_graph = graph.copy()
                    test_graph.add_edge(u, v)
                    
                    if NetworkTopologyGenerator.has_no_bridges(test_graph):
                        graph.add_edge(u, v)
                    
        return graph
    
    @staticmethod
    def has_no_bridges(graph: nx.Graph) -> bool: #Проверка отсутствия мостов в графе
        if graph.number_of_nodes() <= 2:
            return True
        try:
            bridges = list(nx.bridges(graph))
            return len(bridges) == 0
        except:
            return False
    
    @staticmethod
    def get_graph_info(graph: nx.Graph) -> dict:#выводим информацию о графе
        info = {
            'nodes': graph.number_of_nodes(),
            'edges': graph.number_of_edges(),
            'is_connected': nx.is_connected(graph),
            'avg_degree': sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
            'has_bridges': len(list(nx.bridges(graph))) > 0 if graph.number_of_nodes() > 2 else False
        }
        
        if graph.number_of_nodes() > 1:
        # Вычисляем реберную связность
            try:
                info['edge_connectivity'] = nx.edge_connectivity(graph)
            except:
                info['edge_connectivity'] = 0
        else:
            info['edge_connectivity'] = 0
            
        return info

