import time
import threading
from typing import Dict, List, Optional
import networkx as nx

from dsr_protocol import Node, DSRPacket
from network_topology import NetworkTopologyGenerator


class Network:
    #Класс сети, управляющий всеми узлами
    #gui экземпляр класса DSRSimulatorGUI
    #nodes словарь узлов
    #graph граф сети
    #lock блокировка для синхронизации доступа к графу
    #delay задержка между шагами (секунды)
    #paused флаг паузы
    #found_route найденный маршрут
    
    def __init__(self, gui):
        self.gui = gui
        self.nodes: Dict[int, Node] = {}
        self.graph = nx.Graph()
        self.lock = threading.Lock()
        self.delay = 0.5  # Задержка между шагами (секунды)
        self.paused = False
        self.found_route: Optional[List[int]] = None
        
    def create_topology(self, num_nodes: int, allow_bridges: bool = False) -> bool:
        self.graph.clear()
        self.nodes.clear()
        self.found_route = None
        
        # Генерируем топологию
        self.graph = NetworkTopologyGenerator.create_topology(num_nodes, allow_bridges)
        
        # Создаем узлы
        for i in range(num_nodes):
            node = Node(i, self)
            self.nodes[i] = node
            
        # Настраиваем соседей
        for u, v in self.graph.edges():
            self.nodes[u].add_neighbor(v)
            self.nodes[v].add_neighbor(u)
            
        # Логируем информацию о топологии
        info = NetworkTopologyGenerator.get_graph_info(self.graph)
        self.log(f"Создана топология с {info['nodes']} узлами и {info['edges']} связями")
        self.log(f"Реберная связность: {info['edge_connectivity']}")
        self.log(f"Мосты в графе: {'Есть' if info['has_bridges'] else 'Отсутствуют'}")
        
        return True
        
    def start_nodes(self):
        #запускаем все узлы, которые не запущены
        for node in self.nodes.values():
            if not node.is_alive():
                node.start()
            
    def stop_nodes(self):
        #останавливаем все узлы
        for node in self.nodes.values():
            node.stop()
            
    def send_packet(self, from_node: int, to_node: int, packet: DSRPacket):
        #отправляем пакет от одного узла к другому
        if self.paused:
            return
            
        # Задержка для визуализации (в секундах)
        time.sleep(self.delay)
        
        if to_node in self.nodes:
            self.nodes[to_node].message_queue.put(packet)
            
    def initiate_communication(self, source: int, destination: int):
        #инициируем обмен данными между узлами
        if source not in self.nodes or destination not in self.nodes:
            self.log("Ошибка: неверные узлы источника или назначения")
            return
            
        if source == destination:
            self.log("Ошибка: источник и назначение совпадают")
            return
            
        self.found_route = None
        
        # Очищаем кэши узлов
        for node in self.nodes.values():
            node.clear_cache()
            
        # Запускаем поиск маршрута
        self.nodes[source].initiate_route_discovery(destination)
        
    def log(self, message: str):
        #добавляем сообщение в лог
        if self.gui:
            self.gui.add_log(message)
        
    def visualize_step(self, packet: DSRPacket, current_node: int):
        #визуализируем текущий шаг протокола
        if self.paused:
            return
        if self.gui:
            self.gui.update_visualization(packet, current_node)
        
    def route_found(self, route: List[int]):
        #вызывается когда маршрут найден
        self.found_route = route
        if self.gui:
            self.gui.show_found_route(route)
            
    def set_delay(self, delay: float):
        #устанавливаем задержку между шагами
        self.delay = max(0, delay)

