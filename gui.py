import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from typing import List, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import networkx as nx

from network import Network
from dsr_protocol import DSRPacket


class DSRSimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Симулятор протокола DSR")
        self.root.geometry("1280x720") # под ноут поменьше
        
        self.network = Network(self)
        self.pos = None  # позиций узлов для отрисовки
        
        self.setup_ui()
        
    def setup_ui(self): # Настройка пользовательского интерфейса
        # Верхняя панель управления
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Поле ввода количества узлов
        ttk.Label(control_frame, text="Количество узлов (2-50):").pack(side=tk.LEFT, padx=5)
        self.nodes_var = tk.StringVar(value="10")
        nodes_entry = ttk.Entry(control_frame, textvariable=self.nodes_var, width=10)
        nodes_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Создать топологию", 
            command=self.create_topology
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10) # полоска между кнопками
        
        # Поля для выбора узлов
        ttk.Label(control_frame, text="От узла:").pack(side=tk.LEFT, padx=5)
        self.source_var = tk.StringVar(value="0")
        source_entry = ttk.Entry(control_frame, textvariable=self.source_var, width=5)
        source_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="К узлу:").pack(side=tk.LEFT, padx=5)
        self.dest_var = tk.StringVar(value="5")
        dest_entry = ttk.Entry(control_frame, textvariable=self.dest_var, width=5)
        dest_entry.pack(side=tk.LEFT, padx=5)
        
        self.start_button = ttk.Button(
            control_frame, 
            text="Найти маршрут", 
            command=self.start_routing
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Разделитель
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Кнопка сброса
        ttk.Button(
            control_frame, 
            text="Сброс",
            command=self.reset
        ).pack(side=tk.LEFT, padx=5)
        
        # Задержка
        ttk.Label(control_frame, text="Задержка (сек):").pack(side=tk.LEFT, padx=5)
        self.delay_var = tk.StringVar(value="0.5")
        delay_entry = ttk.Entry(control_frame, textvariable=self.delay_var, width=5)
        delay_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame, 
            text="Применить", 
            command=self.update_delay
        ).pack(side=tk.LEFT, padx=5)
        
        # Основная область с отступами
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # визуализация графа в левой части
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ttk.Label(
            left_frame, 
            text="Топология сети", 
            font=('Arial', 12, 'bold')
        ).pack(pady=5)
        
        # Создаем поле для matplotlib
        self.fig = Figure(figsize=(8, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # лог событий
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        ttk.Label(
            right_frame, 
            text="Журнал событий", 
            font=('Arial', 12, 'bold')
        ).pack(pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame, 
            width=50, 
            height=30,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка очистки лога
        ttk.Button(
            right_frame, 
            text="Очистить лог", 
            command=self.clear_log
        ).pack(pady=5)
        
        # Инициализируем пустой граф
        self.visualize_graph()
        
    def create_topology(self): # Создать топологию сети
        try:
            num_nodes = int(self.nodes_var.get())
            
            if num_nodes < 2 or num_nodes > 50:
                messagebox.showerror(
                    "Ошибка", 
                    "Количество узлов должно быть от 2 до 50"
                )
                return
                
            self.network.stop_nodes() # при создании новой топологии останавливаем текущую сеть
            
            # Создаем новую топологию
            self.add_log("=" * 60)
            self.add_log(f"Создание новой топологии с узлами, колличество: {num_nodes}")
            
            self.network.create_topology(num_nodes)
            
            # Запускаем создание узлов
            self.network.start_nodes()
            
            # Визуализируем
            self.pos = None  # Сброс позиций для нового графа
            self.visualize_graph()
            
            self.add_log("Топология создана")
            self.add_log("Выберите узлы источника и назначения, затем нажмите 'Найти маршрут'")
            self.add_log("=" * 60)
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное число узлов")
            
    def visualize_graph(self, highlight_route=None, current_packet=None, current_node=None): # Визуализировать граф сети
        # очищаем поле для отрисовки
        self.ax.clear()
        
        if self.network.graph.number_of_nodes() == 0: # если нет узлов, то выводим сообщение
            self.ax.text(
                0.5, 0.5, 
                'Создайте топологию,\nчтобы здесь был граф', 
                ha='center', 
                va='center', 
                fontsize=20,
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5)
            )
            self.ax.axis('off')
            self.canvas.draw()
            return
            
        # Вычисляем позиции узлов
        if self.pos is None or len(self.pos) != self.network.graph.number_of_nodes():
            self.pos = nx.spring_layout(self.network.graph, k=2, iterations=50, seed=42)
            
        # Рисуем ребра
        nx.draw_networkx_edges(
            self.network.graph, 
            self.pos, 
            ax=self.ax,
            edge_color='gray',
            width=1.5,
            alpha=0.6
        )
        
        # Если есть найденный маршрут, подсвечиваем его
        if highlight_route and len(highlight_route) > 1:
            route_edges = [
                (highlight_route[i], highlight_route[i+1]) 
                for i in range(len(highlight_route)-1)
            ]
            nx.draw_networkx_edges(
                self.network.graph,
                self.pos,
                ax=self.ax,
                edgelist=route_edges,
                edge_color='green',
                width=4,
                alpha=0.9
            )
            
        # Определяем цвета узлов
        node_colors = []
        for node in self.network.graph.nodes():
            if current_node is not None and node == current_node:
                if current_packet and current_packet.type == 'RREQ':
                    node_colors.append('orange')  # Текущий узел обрабатывает RREQ
                elif current_packet and current_packet.type == 'RREP':
                    node_colors.append('lightgreen')  # Текущий узел обрабатывает RREP
                else:
                    node_colors.append('yellow')
            elif current_packet:
                if node == current_packet.source:
                    node_colors.append('blue')  # Источник
                elif node == current_packet.destination:
                    node_colors.append('red')  # Назначение
                elif node in current_packet.route:
                    node_colors.append('lightblue')  # Часть маршрута
                else:
                    node_colors.append('lightgray')
            else:
                node_colors.append('lightblue')
                
        # Рисуем узлы
        nx.draw_networkx_nodes(
            self.network.graph,
            self.pos,
            ax=self.ax,
            node_color=node_colors,
            node_size=500,
            edgecolors='black',
            linewidths=2
        )
        
        # Рисуем метки узлов
        nx.draw_networkx_labels(
            self.network.graph,
            self.pos,
            ax=self.ax,
            font_size=10,
            font_weight='bold'
        )
        
        # Добавляем информационную панель
        if current_packet:
            legend_text = f"Тип пакета: {current_packet.type}\n"
            legend_text += f"Маршрут: {current_packet.source} → {current_packet.destination}\n"
            legend_text += f"Путь: {' → '.join(map(str, current_packet.route))}"
            
            self.ax.text(
                0.05, 0.05, 
                legend_text,
                transform=self.ax.transAxes,
                fontsize=9,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9)
            )
        
        self.ax.set_title(
            f"Граф сети: {self.network.graph.number_of_nodes()} узлов, "
            f"{self.network.graph.number_of_edges()} связей",
            fontsize=11,
            fontweight='bold'
        )
        self.ax.axis('off')
        self.canvas.draw()
        
    def start_routing(self):#Запустить поиск маршрута
        try:
            source = int(self.source_var.get())
            dest = int(self.dest_var.get())
            
            if source not in self.network.nodes or dest not in self.network.nodes:
                messagebox.showerror(
                    "Ошибка", 
                    f"Узлы должны быть в диапазоне от 0 до {len(self.network.nodes)-1}"
                )
                return
                
            if source == dest:
                messagebox.showerror(
                    "Ошибка",
                    "Узел источника и узел назначения не могут совпадать"
                )
                return
                
            self.add_log("=" * 31)
            self.add_log(f"Начало поиска маршрута: {source} → {dest}")
            self.add_log("=" * 30)
            
            # Запускаем поиск в отдельном потоке
            #если не в отдельном потоке, то интерфейс перестанет отвечать на действия пользователя
            #нельзя будет прервать поиск и не будет визуализации пакетов
            threading.Thread(
                target=self.network.initiate_communication,
                args=(source, dest),
                daemon=True
            ).start()
            
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные номера узлов")
            
    def update_visualization(self, packet: DSRPacket, current_node: int): # Обновить визуализацию с текущим пакетом
        self.root.after(0, lambda: self.visualize_graph(None, packet, current_node))
        
    def show_found_route(self, route: List[int]): #Показать найденный маршрут
        self.root.after(0, lambda: self.visualize_graph(highlight_route=route))
        
    def add_log(self, message: str):# Добавить сообщение в лог
        timestamp = time.strftime("%H:%M:%S [log here]")
        
        def update():
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            
        self.root.after(0, update)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.add_log("Лог очищен")
        
    def reset(self):
        self.network.stop_nodes()
        self.network = Network(self)
        self.pos = None
        self.visualize_graph()
        self.add_log("=" * 60)
        self.add_log("Симуляция сброшена")
        self.add_log("=" * 60)
        
    def update_delay(self):
        try:
            delay = float(self.delay_var.get())
            self.network.set_delay(delay)
            self.add_log(f"Задержка установлена, {delay} секунд")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное значение задержки")
            
    def on_closing(self):
        self.network.stop_nodes()
        self.root.destroy()

