import sys
from PyQt6.QtWidgets import QApplication
from gui.views.main_window import MainWindow
from qfluentwidgets import FluentTranslator
from PyQt6.QtGui import QIcon


def main():
    # 创建应用程序实例
    app = QApplication(sys.argv)
    
    # 设置中文翻译
    translator = FluentTranslator()
    app.installTranslator(translator)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.setWindowIcon(QIcon("icon/图标智能客服.ico"))
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
