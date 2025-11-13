import threading
import time
import queue
import random
from typing import List, Dict, Set, Tuple, Optional


class DSRPacket:
    #Класс для работы с пакетами DSR
    
    def __init__(self, packet_type: str, source: int, destination: int, 
                 route: List[int] = None, packet_id: int = 0):
        self.type = packet_type  # RREQ или RREP
        self.source = source
        self.destination = destination
        self.route = route if route else [source]
        self.packet_id = packet_id
        self.timestamp = time.time()


class Node(threading.Thread):
    #Класс узла сети, работающий в отдельном потоке
    
    def __init__(self, node_id: int, network): #инициализируем узел
        super().__init__(daemon=True)
        self.node_id = node_id
        self.network = network
        self.neighbors: Set[int] = set()
        self.route_cache: Dict[int, List[int]] = {}  # словарь для хранения маршрутов
        self.message_queue = queue.Queue()
        self.running = False
        self.processed_rreq: Set[Tuple[int, int]] = set()  # source, packet_id
        
    def add_neighbor(self, neighbor_id: int):
        self.neighbors.add(neighbor_id)
        
    def run(self):
        #основной цикл работы узла
        self.running = True
        while self.running:
            try:
                # Получаем сообщение из очереди
                packet = self.message_queue.get(timeout=0.1)
                self.process_packet(packet)
            except queue.Empty: #если очередь пуста, то продолжаем цикл
                continue
            except Exception as e:
                self.network.log(f"Ошибка в узле {self.node_id}: {e}")
                
    def process_packet(self, packet: DSRPacket):
        #обработка входящего пакета
        if packet.type == 'RREQ':
            self.process_rreq(packet)
        elif packet.type == 'RREP':
            self.process_rrep(packet)
            
    def process_rreq(self, packet: DSRPacket):
        #обработка запроса маршрута (Route Request)
        packet_key = (packet.source, packet.packet_id)
        
        # Проверяем, не обрабатывали ли мы уже этот RREQ
        if packet_key in self.processed_rreq:
            return
            
        self.processed_rreq.add(packet_key)
        
        # Логируем получение RREQ
        self.network.log(
            f"Узел {self.node_id} получил RREQ от {packet.source} "
            f"к {packet.destination}, маршрут: {packet.route}"
        )
        self.network.visualize_step(packet, self.node_id)
        
        # Если мы узел назначения
        if self.node_id == packet.destination:
            # Отправляем RREP обратно
            self.send_rrep(packet)
            return
            
        # Проверяем, что нас еще нет в маршруте (избегаем циклов)
        if self.node_id in packet.route:
            return
            
        # Добавляем себя к маршруту и пересылаем соседям
        new_route = packet.route + [self.node_id]
        for neighbor in self.neighbors:
            if neighbor not in new_route:
                new_packet = DSRPacket(
                    'RREQ', 
                    packet.source, 
                    packet.destination,
                    new_route.copy(),
                    packet.packet_id
                )
                self.network.send_packet(self.node_id, neighbor, new_packet)
                
    def send_rrep(self, rreq_packet: DSRPacket):
        #отправка ответа на запрос маршрута (Route Reply)
        # полный маршрут от источника до назначения
        full_route = rreq_packet.route + [self.node_id]
        
        self.network.log(
            f"Узел {self.node_id} отправляет RREP к {rreq_packet.source}, "
            f"маршрут: {full_route}"
        )
        
        # Создаем RREP пакет
        rrep = DSRPacket(
            'RREP',
            rreq_packet.destination,  # Теперь мы источник
            rreq_packet.source,        # Первоначальный источник это назначение
            full_route,
            rreq_packet.packet_id
        )
        
        # Отправляем RREP обратно по обратному маршруту
        reverse_route = list(reversed(full_route))
        if len(reverse_route) > 1:
            next_hop = reverse_route[1]
            self.network.send_packet(self.node_id, next_hop, rrep)
            
    def process_rrep(self, packet: DSRPacket):
        """Route Reply обработка"""
        self.network.log(
            f"Узел {self.node_id} получил RREP от {packet.source} "
            f"к {packet.destination}, маршрут: {packet.route}"
        )
        self.network.visualize_step(packet, self.node_id)
        
        # Сохраняем маршрут в кэше
        self.route_cache[packet.source] = packet.route
        
        # Если мы узел назначения RREP (источник RREQ)
        if self.node_id == packet.destination:
            self.network.log(
                f"Маршрут найден! От {self.node_id} до {packet.source}: "
                f"{packet.route}"
            )
            self.network.route_found(packet.route)
            return
            
        # Пересылаем RREP дальше по маршруту
        reverse_route = list(reversed(packet.route))
        current_idx = reverse_route.index(self.node_id)
        
        if current_idx < len(reverse_route) - 1:
            next_hop = reverse_route[current_idx + 1]
            self.network.send_packet(self.node_id, next_hop, packet)
            
    def initiate_route_discovery(self, destination: int): # Инициировать поиск маршрута к узлу назначения
        # Проверяем кэш маршрутов
        #if destination in self.route_cache:
         #   self.network.log(
          #      f"Узел {self.node_id} использует кэшированный маршрут к {destination}"
           # )
            #return
        self.route_cache.clear() #очищаем кэш маршрутов

        # Создаем новый RREQ
        packet_id = random.randint(1, 10000)
        rreq = DSRPacket('RREQ', self.node_id, destination, [self.node_id], packet_id)
        
        self.network.log(
            f"Узел {self.node_id} инициирует поиск маршрута к {destination}"
        )
        self.network.visualize_step(rreq, self.node_id)
        
        # Отмечаем, что мы обработали этот RREQ
        self.processed_rreq.add((self.node_id, packet_id))
        
        # Отправляем RREQ всем соседям
        for neighbor in self.neighbors:
            self.network.send_packet(self.node_id, neighbor, rreq)
            
    def stop(self): # Остановить узел
        self.running = False
    
    def clear_cache(self):#Очистить кэш маршрутов и обработанных RREQ
        self.processed_rreq.clear()
        self.route_cache.clear()

