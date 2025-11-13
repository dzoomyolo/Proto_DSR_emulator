import tkinter as tk
import sys
from gui import DSRSimulatorGUI

def main():
    # Создаем главное окно
    root = tk.Tk()
    
    # Создаем GUI приложения
    app = DSRSimulatorGUI(root)
    
    # Устанавливаем обработчик закрытия окна
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    app.add_log("=" * 30)
    app.add_log("Добро пожаловать в симулятор протокола DSR (Dynamic Source Routing)")
    app.add_log("Author: Menyashev R.R.")
    app.add_log("Group: 5141001/50301")
    app.add_log("Contact: https://github.com/dzoomyolo")
    app.add_log("=" * 30)
    
    # Запускаем главный цикл приложения
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\nОшибка: {e}")
        sys.exit(1)
