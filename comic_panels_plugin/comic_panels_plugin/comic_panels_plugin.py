from .panels_window_and_logic import *
class comicPanelsPlugin(Extension):

    def __init__(self, parent):
        super(comicPanelsPlugin, self).__init__(parent)

    # Krita.instance() exists, so do any setup work
    def setup(self):
        pass

    # called after setup(self)
    def createActions(self, window):
        action = window.createAction("", "Comic Panels")
        action.triggered.connect(self.showPlugin)

    def showPlugin(self):
        if Krita.instance().activeDocument() is not None:
            self.w = PluginWindow()
            self.w.show()
            self.w.activateWindow()
        else:
            QMessageBox.information(QWidget(), "Ошибка", "Документ не создан") 
            return