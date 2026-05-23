import ttkbootstrap as ttkb
from .views.main_window import MainWindow
from .controllers.app_controller import AppController


def launch_app():
    root = ttkb.Window(themename="litera")

    # Создаем главное окно (оно внутри себя создаст все подвьюшки)
    view = MainWindow(root, None)

    # Создаем контроллер и передаем ему окно
    controller = AppController(view)

    # Привязываем контроллер обратно к окну
    view.controller = controller

    # теперь рисуем интерфейс
    # даем время на привязку контроллера
    root.after(100, controller._refresh_all_ui)

    # Перехватываем закрытие окна
    def on_closing():
        if controller.check_unsaved_changes():
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    launch_app()
