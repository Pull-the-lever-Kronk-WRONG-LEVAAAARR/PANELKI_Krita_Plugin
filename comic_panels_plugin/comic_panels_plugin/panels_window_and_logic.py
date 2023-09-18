from math import ceil
from krita import *
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QSpinBox,
    QGraphicsView,
    QGraphicsScene,
    QComboBox,
    QRadioButton,
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPen, QPixmap, QImage, QResizeEvent
from functools import partial


class PropertieWindow(QWidget):
    def __init__(self):
        super(PropertieWindow, self).__init__()
        self.setWindowTitle("Panel Properties")
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab1, "Размерность")
        self.tabs.addTab(self.tab2, "Настройки")
        # Размерность панелей, tab1
        descriptionPanels = QLabel("Задайте размерность раскадровки")
        rowsLabel = QLabel("Ряды")
        self.rowsInp = QSpinBox()
        self.rowsInp.setRange(1, 7)
        columnsLabel = QLabel("Колонки")
        self.columnsInp = QSpinBox()
        self.columnsInp.setRange(1, 7)
        descriptionGutter = QLabel("Задайте размер канавки")
        gutterLabel = QLabel("Канавка")
        self.gutterInp = QDoubleSpinBox()
        self.groupCheckbox = QCheckBox("Разбить на группы", self)
        # Табличная вёрстка
        gridTab1 = QGridLayout(self)
        gridTab1.addWidget(descriptionPanels, 0, 0, 1, 0)
        gridTab1.addWidget(rowsLabel, 1, 0)
        gridTab1.addWidget(self.rowsInp, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        gridTab1.addWidget(columnsLabel, 2, 0)
        gridTab1.addWidget(self.columnsInp, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        gridTab1.addWidget(descriptionGutter, 3, 0, 1, 0)
        gridTab1.addWidget(gutterLabel, 4, 0)
        gridTab1.addWidget(self.gutterInp, 4, 1, alignment=Qt.AlignmentFlag.AlignRight)
        gridTab1.addWidget(self.groupCheckbox, 5, 0)
        self.tab1.setLayout(gridTab1)
        # Настройки пропорций панелей, tab2
        descriptionPanels = QLabel(
            "Настройте пропорции панелей, изменяя положение канавок"
        )
        descriptionPanels.setWordWrap(True)
        self.xResultLabel = QLabel("x: 0 %", self)
        self.xSlider = QSlider(Qt.Orientation.Horizontal, self)
        self.xSlider.setRange(-100, 100)
        self.xSlider.setValue(0)
        self.xSlider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.xSlider.valueChanged.connect(self.updateX)

        self.yResultLabel = QLabel("y: 0 %", self)
        self.ySlider = QSlider(Qt.Orientation.Horizontal, self)
        self.ySlider.setRange(-100, 100)
        self.ySlider.setValue(0)
        self.ySlider.setTickPosition(QSlider.TickPosition.TicksAbove)
        self.ySlider.valueChanged.connect(self.updateY)

        gridTab2 = QGridLayout(self)
        gridTab2.addWidget(descriptionPanels, 0, 0, 1, 0)
        gridTab2.addWidget(self.xResultLabel, 1, 0)
        gridTab2.addWidget(self.xSlider, 2, 0)
        gridTab2.addWidget(self.yResultLabel, 3, 0)
        gridTab2.addWidget(self.ySlider, 4, 0)
        self.tab2.setLayout(gridTab2)

    def updateX(self, value):
        self.xResultLabel.setText(f"x: {value} %")

    def updateY(self, value):
        self.yResultLabel.setText(f"y: {value} %")


class Emitter(QObject):
    itemSelected = pyqtSignal(object)

class ManipItem(QGraphicsRectItem):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.setData(0, 0)  # x value
        self.setData(1, 0)  # y value
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.xValue = 0
        self.yValue = 0
        self.emitter = Emitter()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged and value == True:
            if self.scene() is None:
                return value
            self.xValue = self.data(0)
            self.yValue = self.data(1)
            self.emitter.itemSelected.emit([self.xValue, self.yValue])
            self.setOpacity(1)
        elif change == QGraphicsItem.ItemSelectedHasChanged and value == False:
            self.setOpacity(0.3)

        return QtWidgets.QGraphicsItem.itemChange(self, change, value)


class PluginWindow(QWidget):
    def __init__(self):
        self.MAX_PAGE = 1000000
        self.ACTIVE_DOC = Krita.instance().activeDocument()
        self.ACTIVE_NODE = self.ACTIVE_DOC.activeNode()
        self.NODE_WIDTH = self.ACTIVE_DOC.bounds().width()
        self.NODE_HEIGHT = self.ACTIVE_DOC.bounds().height()
        # вызов конструктора родительского класса
        super(PluginWindow, self).__init__()
        self.setWindowTitle("Панельки")
        # Разметка окна плагина представляет собой сетку из  4 колонок
        layout = QGridLayout(self)
        setupLayout = QVBoxLayout(self)
        applyButton = QPushButton("Применить")
        okButton = QPushButton("Готово")
        cancelButton = QPushButton("Отмена")
        # temp label
        # self.label = QLabel(self)
        # self.label.setText("scene size:")

        setupLayout.addWidget(self.units())
        setupLayout.addWidget(self.pageSetup())
        setupLayout.addWidget(self.safetyArea())
        setupLayout.addWidget(self.panelSetup())
        self.setLayout(layout)

        layout.addLayout(setupLayout, 1, 0)
        # layout.addWidget(self.label, 0, 1)
        layout.addWidget(self.preview(), 1, 1, 1, -1)
        layout.addWidget(applyButton, 2, 1)
        layout.addWidget(okButton, 2, 2)
        layout.addWidget(cancelButton, 2, 3)

        self.loadDocSize()
        # Инициализация границ
        self.canvasBorderPreview()
        self.bleedBorderPreview()
        self.safeBorderPreview()
        # Инициализация значений для перевода единиц измерения
        # Последнее поле хранит предыдущее состояние
        self.convertValues = {
            "pixelPerInch": self.ACTIVE_DOC.resolution(),
            "mmPerInch": 25.4,
            "pixelPerMm": self.ACTIVE_DOC.resolution() / 25.4,
            "prevState": self.comboBox.currentIndex(),
        }
        # Коллекция объектов-фреймов на сцене
        self.frameCollection = []
        # Коллекция графических объектов-манипуляторов
        self.manipCollection1 = []
        self.manipCollection2 = []
        self.manipMatrix = (
            []
        )  # 2D матрица, хранящая объекты сцены (панели, канавки, узлы)

        # СИГНАЛЫ
        # Если изменится одно из полей, то будет послан сигнал на изменение границ безопасной области
        self.widthInp.valueChanged.connect(self.boundsSafeSpace)
        self.heightInp.valueChanged.connect(self.boundsSafeSpace)
        # При изменении количества фреймов изменяется размер канавки
        self.panelProperties.rowsInp.valueChanged.connect(self.calcGutter)
        self.panelProperties.columnsInp.valueChanged.connect(self.calcGutter)
        # Перевод единиц измерения
        self.comboBox.currentTextChanged.connect(self.convertUnits)
        # Инициализация или удаление границ безопасной области
        self.safetygroupBox.toggled.connect(self.safeBorderPreview)
        # Обновление границ на предпросмотре
        applyButton.clicked.connect(self.updBorderPreview)
        okButton.clicked.connect(self.kritaGroup)
        cancelButton.clicked.connect(self.close)

        # ===========================================
        self.panelProperties.xSlider.valueChanged.connect(self.translateGutter)
        self.panelProperties.ySlider.valueChanged.connect(self.translateGutter)


    def updateSliders(self, i):
        self.panelProperties.xSlider.setValue(i[0])
        self.panelProperties.ySlider.setValue(i[1])


    def selectRC(self, r, c):
        for i in range(2 * self.panelProperties.rowsInp.value() - 1):
            self.horizontalTranslate(i, c)
            self.scaleHorizontal(i, c, i)

        for i in range(2 * self.panelProperties.columnsInp.value() - 1):
            self.verticalTranslate(r, i)
            self.scaleVertical(r, i, i)

        # self.scaleVertical(r, c, 2)

    def translateGutter(self):
        items = self.scene.selectedItems()
        for i in items:
            r = 0
            c = 0
            for row in self.manipMatrix:
                if i in row:
                    r = self.manipMatrix.index(row)
                    c = row.index(i)
                    if r % 2 != 0 and c % 2 != 0:
                        self.selectRC(r, c)
                    if c % 2 != 0:
                        self.horizontalTranslate(r, c)
                        self.scaleHorizontal(r, c, r)
                    elif r % 2 != 0:
                        self.verticalTranslate(r, c)
                        self.scaleVertical(r, c, c)
                    elif r % 2 != 0 and c % 2 != 0:
                        self.selectRC(r, c)            

    def horizontalTranslate(self, r, c):
        if c - 2 >= 0:
            x0 = (
                self.manipMatrix[r][c - 2].rect().right()
                + self.manipMatrix[r][c - 2].pos().x()
            )
        else:
            x0 = (
                self.manipMatrix[r][c - 1].rect().x()
                + self.manipMatrix[r][c - 1].pos().x()
            )
        # =================================================
        if c + 2 < self.panelProperties.columnsInp.value() * 2 - 1:
            xk = (
                self.manipMatrix[r][c + 2].rect().x()
                + self.manipMatrix[r][c + 2].pos().x()
                - self.manipMatrix[r][c].rect().width()
            )
        else:
            xk = (
                self.manipMatrix[r][c + 1].rect().right()
                + self.manipMatrix[r][c + 1].pos().x()
                - self.manipMatrix[r][c].rect().width()
            )
        # d = x0 - xk
        d = xk - x0

        xscale = self.panelProperties.xSlider.value()
        self.manipMatrix[r][c].setData(0, xscale)
        
        x = self.manipMatrix[r][c].rect().x()
        #if x < x0:
          #  k = x0 - x - (d / 2)
        #else:
          #  k = x0 - x + (d / 2)
        k = x0 + (d / 2) - x
        self.manipMatrix[r][c].setX((xscale * d / 200) + k)


    def verticalTranslate(self, r, c):
        if r - 2 >= 0:
            y0 = (
                self.manipMatrix[r - 2][c].rect().bottom()
                + self.manipMatrix[r - 2][c].pos().y()
            )
        else:
            y0 = (
                self.manipMatrix[r - 1][c].rect().y()
                + self.manipMatrix[r - 1][c].pos().y()
            )
        # =================================================
        if r + 2 < self.panelProperties.rowsInp.value() * 2 - 1:
            yk = (
                self.manipMatrix[r + 2][c].rect().y()
                + self.manipMatrix[r + 2][c].pos().y()
                - self.manipMatrix[r][c].rect().height()
            )
        else:
            yk = (
                self.manipMatrix[r + 1][c].rect().bottom()
                + self.manipMatrix[r + 1][c].pos().y()
                - self.manipMatrix[r][c].rect().height()
            )
        d = yk - y0
        yscale = self.panelProperties.ySlider.value()
        self.manipMatrix[r][c].setData(1, yscale)

        y = self.manipMatrix[r][c].rect().y()
        k = y0 + (d / 2) - y
        self.manipMatrix[r][c].setY((yscale * d / 200) + k)

    # def mousePressEvent(self, event):
    #     x = self.scenePos().x()
    #     y = self.event.scenePos().y()

    def scaleVertical(self, r, c, newC):
        self.manipMatrix[r - 1][newC].setRect(
            self.manipMatrix[r - 1][newC].rect().x(),
            self.manipMatrix[r - 1][newC].rect().y(),
            self.manipMatrix[r - 1][newC].rect().width(),
            self.manipMatrix[r][c].rect().y() + self.manipMatrix[r][c].pos().y() - self.manipMatrix[r - 1][newC].rect().y()
        )

        self.manipMatrix[r + 1][newC].setRect(
            self.manipMatrix[r + 1][newC].rect().x(),
            self.manipMatrix[r][c].rect().bottom() + self.manipMatrix[r][c].pos().y(),
            self.manipMatrix[r + 1][newC].rect().width(),
            self.manipMatrix[r + 1][newC].rect().bottom() - self.manipMatrix[r][c].rect().bottom() - self.manipMatrix[r][c].pos().y()
        )

    def scaleHorizontal(self, r, c, newR):
        self.manipMatrix[newR][c - 1].setRect(
            self.manipMatrix[newR][c - 1].rect().x(),
            self.manipMatrix[newR][c - 1].rect().y(),
            self.manipMatrix[r][c].rect().x() + self.manipMatrix[r][c].pos().x() - self.manipMatrix[newR][c - 1].rect().x(),
            self.manipMatrix[newR][c - 1].rect().height()
        )

        self.manipMatrix[newR][c + 1].setRect(
            self.manipMatrix[r][c].rect().right() + self.manipMatrix[r][c].pos().x(),
            self.manipMatrix[newR][c + 1].rect().y(),
            self.manipMatrix[newR][c + 1].rect().right() - self.manipMatrix[r][c].rect().right() - self.manipMatrix[r][c].pos().x(),
            self.manipMatrix[newR][c + 1].rect().height()
        )


    def units(self):
        # Меню для выбора единиц измерения
        unitsList = ["Дюймы (in)", "Миллиметры (mm)", "Пиксели (px)"]
        self.comboBox = QComboBox()
        self.comboBox.blockSignals(True)
        self.comboBox.addItems(unitsList)
        # По умолчанию выбраны px
        self.comboBox.setCurrentIndex(2)
        self.comboBox.blockSignals(False)
        return self.comboBox

    def pageSetup(self):
        # groupbox, в котором располагаются поля для настройки страницы
        # с учётом печатных требований
        # обрезной формат, т.е. размер итогового листа в готовом изделии
        # в качестве значений по умолчанию берутся параметры холста, если он был создан
        groupBox = QGroupBox("Настройки страницы")
        description = QLabel("Задайте обрезной формат")
        widthLabel = QLabel("Ширина")
        self.widthInp = QDoubleSpinBox()
        heightLabel = QLabel("Высота")
        self.heightInp = QDoubleSpinBox()
        bleedLabel = QLabel("Вылеты")
        self.bleedInp = QDoubleSpinBox()
        # Задание ограничений для полей  в п
        self.widthInp.setRange(1, self.MAX_PAGE)
        self.heightInp.setRange(1, self.MAX_PAGE)
        self.bleedInp.setRange(0, self.MAX_PAGE / 2)
        # Табличная вёрстка
        grid = QGridLayout(self)
        grid.addWidget(description, 0, 0, 1, 0)
        grid.addWidget(widthLabel, 1, 0)
        grid.addWidget(self.widthInp, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(heightLabel, 2, 0)
        grid.addWidget(self.heightInp, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(bleedLabel, 3, 0)
        grid.addWidget(self.bleedInp, 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
        groupBox.setLayout(grid)
        return groupBox

    def safetyArea(self):
        # groupbox, в котором располагаются поля для настройки безопасной области страницы
        # является необязательным — используется метод isCheckable
        self.safetygroupBox = QGroupBox("Безопасная область")
        self.safetygroupBox.setCheckable(True)
        description = QLabel("Задайте отступы")
        upperLabel = QLabel("Верхний")
        self.upperInp = QDoubleSpinBox()
        bottomLabel = QLabel("Нижний")
        self.bottomInp = QDoubleSpinBox()
        frontLabel = QLabel("Внешний")
        self.frontInp = QDoubleSpinBox()
        innerLabel = QLabel("Внутренний")
        self.innerInp = QDoubleSpinBox()
        # Задание первичных ограничений для полей
        self.upperInp.setRange(0, 500000)
        self.bottomInp.setRange(0, 500000)
        self.frontInp.setRange(0, 500000)
        self.innerInp.setRange(0, 500000)
        # Определение положения сгиба для правильного отображения внешнего и внутреннего отступов
        self.radioL = QRadioButton("Сгиб слева", self)
        self.radioR = QRadioButton("Сгиб справа", self)
        self.radioR.toggle()
        # Табличная вёрстка
        grid = QGridLayout(self)
        grid.addWidget(description, 0, 0, 1, 0)
        grid.addWidget(upperLabel, 1, 0)
        grid.addWidget(self.upperInp, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(bottomLabel, 2, 0)
        grid.addWidget(self.bottomInp, 2, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(frontLabel, 3, 0)
        grid.addWidget(self.frontInp, 3, 1, alignment=Qt.AlignmentFlag.AlignRight)
        grid.addWidget(innerLabel, 4, 0)
        grid.addWidget(self.innerInp, 4, 1, alignment=Qt.AlignmentFlag.AlignRight)

        grid.addWidget(self.radioL, 5, 0)
        grid.addWidget(self.radioR, 5, 1)
        self.safetygroupBox.setLayout(grid)
        return self.safetygroupBox

    def panelSetup(self):
        # groupbox, в котором располагаются поля для настройки панелей
        groupBox = QGroupBox("Панели")
        self.panelProperties = PropertieWindow()
        groupBoxLayout = QVBoxLayout()
        groupBoxLayout.addWidget(self.panelProperties.tabs)
        groupBox.setLayout(groupBoxLayout)

        return groupBox

    def preview(self):
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.show()
        self.loadActiveLayer()
        return self.view

    def closeEvent(self, event):
        event.accept()

    # =====================ФУНКЦИИ==========================
    def loadDocSize(self):
        # Если существует документ, то возвращаются значения ширины и высоты активного документа
        if self.ACTIVE_DOC:
            self.widthInp.setValue(self.NODE_WIDTH)
            self.heightInp.setValue(self.NODE_HEIGHT)

    def boundsSafeSpace(self):
        # расчёт и установка верхних границ для полей безопасной области
        self.upperInp.setRange(0, ceil(self.heightInp.value() / 2))
        self.bottomInp.setRange(0, ceil(self.heightInp.value() / 2))
        self.frontInp.setRange(0, ceil(self.widthInp.value() / 2))
        self.innerInp.setRange(0, ceil(self.widthInp.value() / 2))

    def calcGutter(self):
        # канавка занимает не более 1/3 фрейма при условии, они равны (1 / кол-во по ширине (высоте))
        # рассчитывается значение по высоте и по ширине,
        # выбирается минимальное
        print(self.panelProperties.rowsInp.value())
        gw = self.widthInp.value() / (self.panelProperties.rowsInp.value() * 4 - 1)
        gh = self.heightInp.value() / (self.panelProperties.columnsInp.value() * 4 - 1)
        minG = min(gw, gh)
        if self.comboBox.currentIndex() == 1 or self.comboBox.currentIndex() == 2:
            minG = round(minG, 2)
        else:
            minG = round(minG)
        self.panelProperties.gutterInp.setRange(0, minG)

    def loadActiveLayer(self):
        # Добавление активного слоя в качестве объекта QPixmap на сцену
        if self.ACTIVE_DOC and (self.ACTIVE_NODE is not None):
            byteArray = self.ACTIVE_NODE.pixelData(
                self.ACTIVE_DOC.bounds().left(),
                self.ACTIVE_DOC.bounds().top(),
                self.ACTIVE_DOC.bounds().width(),
                self.ACTIVE_DOC.bounds().height(),
            )
            if len(byteArray) > 0:
                img = QImage(
                    byteArray,
                    self.ACTIVE_DOC.bounds().width(),
                    self.ACTIVE_DOC.bounds().height(),
                    QImage.Format_RGBA8888,
                ).rgbSwapped()
                if img:
                    self.pixmapItem = self.scene.addPixmap(QPixmap(img))

    def updateScene(self):
        # Если после увеличения размеров объектов сцены и последующего увеличения сцены объекты были уменьшены,
        # то необходимо принудительно изменить границы сцены. Они на 2.5 пикселя больше объектов с каждой стороны
        # Наибольший размер всегда у границ вылетов или фонового изображения
        width = max(self.NODE_WIDTH, self.bleedBorder.rect().width())
        height = max(self.NODE_HEIGHT, self.bleedBorder.rect().height())
        x = min(0, self.bleedBorder.rect().x())
        y = min(0, self.bleedBorder.rect().y())
        if self.scene.width() > width + 5 or self.scene.height() > height + 5:
            self.scene.setSceneRect(x - 2.5, y - 2.5, width + 2.5, height + 2.5)

    def updateView(self):
        self.updateScene()
        sceneRect = self.scene.sceneRect()
        # print ('  rect %d %d %d %d' % (sceneRect.x(), sceneRect.y(), sceneRect.width(), sceneRect.height()))
        self.view.fitInView(sceneRect, Qt.KeepAspectRatio)

    def resizeEvent(self, event: QResizeEvent):
        self.updateView()

    def showEvent(self, event):
        # Масштабирование при программном вызове show()
        if not event.spontaneous():
            self.updateView()

    # def resizeEvent(self, event: QResizeEvent):
    #     if not self.pixmapItem.pixmap().isNull():
    #         self.view.fitInView(self.pixmapItem, Qt.KeepAspectRatio)

    def canvasBorderPreview(self):
        # Графическое обозначение границ фактического размера страницы
        # Индикация цветом -- синий
        self.canvasBorder = QGraphicsRectItem(
            0, 0, self.widthInp.value(), self.heightInp.value()
        )
        pen = QPen(Qt.cyan)
        pen.setWidth(5)
        self.canvasBorder.setPen(pen)
        self.scene.addItem(self.canvasBorder)

    def bleedBorderPreview(self):
        # Графическое обозначение границ вылетов
        # Начальная точка уменьшается на значение вылетов
        # Конечная точка увеличивается на значение вылетов
        # Индикация цветом -- красный
        self.bleedBorder = QGraphicsRectItem(
            -self.bleedInp.value(),
            -self.bleedInp.value(),
            self.widthInp.value() + self.bleedInp.value(),
            self.heightInp.value() + self.bleedInp.value(),
        )
        pen = QPen(Qt.red)
        pen.setWidth(5)
        self.bleedBorder.setPen(pen)
        self.scene.addItem(self.bleedBorder)

    def safeBorderPreview(self):
        # Графическое обозначение безопасной области, при её наличии
        # Индикация цветом -- зелёный
        width = self.toPixel(self.widthInp.value())
        height = self.toPixel(self.heightInp.value())
        upper = self.toPixel(self.upperInp.value())
        bottom = self.toPixel(self.bottomInp.value())
        inner = self.toPixel(self.innerInp.value())
        front = self.toPixel(self.frontInp.value())
        if self.safetygroupBox.isChecked():
            if self.radioL.isChecked():
                self.safeBorder = QGraphicsRectItem(
                    (self.NODE_WIDTH - width) / 2 + inner,
                    (self.NODE_HEIGHT - height) / 2 + upper,
                    width - inner - front,
                    height - upper - bottom,
                )
            elif self.radioR.isChecked():
                self.safeBorder = QGraphicsRectItem(
                    (self.NODE_WIDTH - width) / 2 + front,
                    (self.NODE_HEIGHT - height) / 2 + upper,
                    width - inner - front,
                    height - upper - bottom,
                )
            pen = QPen(Qt.green)
            pen.setWidth(5)
            self.safeBorder.setPen(pen)
            self.scene.addItem(self.safeBorder)
        else:
            self.scene.removeItem(self.safeBorder)

    # Перевод в пиксели из мм или дюймов
    def toPixel(self, value):
        if self.comboBox.currentIndex() == 0:
            return value * self.convertValues["pixelPerInch"]
        elif self.comboBox.currentIndex() == 1:
            return value * self.convertValues["pixelPerMm"]
        else:
            return value

    def updBorderPreview(self):
        # В случае если значения в полях были введены в мм или дюймах, они переводятся в пиксели
        width = self.toPixel(self.widthInp.value())
        height = self.toPixel(self.heightInp.value())
        bleed = self.toPixel(self.bleedInp.value())
        if self.safetygroupBox.isChecked():
            upper = self.toPixel(self.upperInp.value())
            bottom = self.toPixel(self.bottomInp.value())
            inner = self.toPixel(self.innerInp.value())
            front = self.toPixel(self.frontInp.value())
        self.canvasBorder.setRect(
            (self.NODE_WIDTH - width) / 2,
            (self.NODE_HEIGHT - height) / 2,
            width,
            height,
        )
        # bleed border
        self.bleedBorder.setRect(
            (self.NODE_WIDTH - width) / 2 - bleed,
            (self.NODE_HEIGHT - height) / 2 - bleed,
            width + 2 * bleed,
            height + 2 * bleed,
        )
        # safe area border
        if self.safetygroupBox.isChecked():
            if self.radioL.isChecked():
                self.safeBorder.setRect(
                    (self.NODE_WIDTH - width) / 2 + inner,
                    (self.NODE_HEIGHT - height) / 2 + upper,
                    width - inner - front,
                    height - upper - bottom,
                )
            elif self.radioR.isChecked():
                self.safeBorder.setRect(
                    (self.NODE_WIDTH - width) / 2 + front,
                    (self.NODE_HEIGHT - height) / 2 + upper,
                    width - inner - front,
                    height - upper - bottom,
                )

        # Очистка матрицы при наличии прошых значений и изменение размерности
        # ==========================================
        if self.manipMatrix:
            for i in self.manipMatrix:
                for j in i:
                    if isinstance(j, QGraphicsItem):
                        self.scene.removeItem(j)
            self.manipMatrix.clear()
        self.manipMatrix = [
            [0 for i in range(self.panelProperties.columnsInp.value() * 2 - 1)]
            for j in range(self.panelProperties.rowsInp.value() * 2 - 1)
        ]

        self.updateView()
        self.initFrames()

    def calcUnits(self, coefficient):
        self.widthInp.setValue(self.widthInp.value() * coefficient)
        self.heightInp.setValue(self.heightInp.value() * coefficient)
        self.bleedInp.setValue(self.bleedInp.value() * coefficient)
        if self.safetygroupBox.isChecked():
            self.frontInp.setValue(self.frontInp.value() * coefficient)
            self.innerInp.setValue(self.innerInp.value() * coefficient)
            self.upperInp.setValue(self.upperInp.value() * coefficient)
            self.bottomInp.setValue(self.bottomInp.value() * coefficient)
        self.panelProperties.gutterInp.setValue(
            self.panelProperties.gutterInp.value() * coefficient
        )

    def calcRange(self, coefficient):
        # Границы переводятся только в случает, если текущие единицы не являются пикселями
        self.widthInp.setMaximum(self.MAX_PAGE / coefficient)
        self.heightInp.setMaximum(self.MAX_PAGE / coefficient)
        self.bleedInp.setMaximum(self.MAX_PAGE / (2 * coefficient))

    def convertUnits(self):
        if self.convertValues["prevState"] == 0:
            if self.comboBox.currentIndex() == 1:
                self.calcUnits(self.convertValues["mmPerInch"])
                self.calcRange(self.convertValues["pixelPerMm"])
            elif self.comboBox.currentIndex() == 2:
                self.calcUnits(self.convertValues["pixelPerInch"])
                self.calcRange(1)
        elif self.convertValues["prevState"] == 1:
            if self.comboBox.currentIndex() == 0:
                self.calcUnits(1 / self.convertValues["mmPerInch"])
                self.calcRange(self.convertValues["pixelPerInch"])
            elif self.comboBox.currentIndex() == 2:
                self.calcUnits(self.convertValues["pixelPerMm"])
                self.calcRange(1)
        elif self.convertValues["prevState"] == 2:
            if self.comboBox.currentIndex() == 0:
                self.calcUnits(1 / self.convertValues["pixelPerInch"])
                self.calcRange(self.convertValues["pixelPerInch"])
            elif self.comboBox.currentIndex() == 1:
                self.calcUnits(1 / self.convertValues["pixelPerMm"])
                self.calcRange(self.convertValues["pixelPerMm"])
        self.convertValues["prevState"] = self.comboBox.currentIndex()

    # =====================ПАНЕЛИ==========================
    # Считываются значения рядов и столбцов, выводятся прямоугольники с равными пропорциями
    def initFrames(self):
        # очистка от прошлых объектов при перестройке
        if self.frameCollection:
            for i in self.frameCollection:
                self.scene.removeItem(i)
            self.frameCollection.clear()
        # если существует безопасная область, то границы берутся из неё, иначе из размера страницы
        # коллекция, содержащая все объекты-панели
        # объекты добавляются последовательно слева-направо сверху-вниз
        if not (self.safetygroupBox.isChecked()):
            x = self.canvasBorder.rect().x()
            y = self.canvasBorder.rect().y()
            width = self.canvasBorder.rect().width()
            height = self.canvasBorder.rect().height()
        else:
            x = self.safeBorder.rect().x()
            y = self.safeBorder.rect().y()
            width = self.safeBorder.rect().width()
            height = self.safeBorder.rect().height()
        panelWidth = (
            width
            - (self.panelProperties.columnsInp.value() - 1)
            * self.panelProperties.gutterInp.value()
        ) / self.panelProperties.columnsInp.value()
        panelHeight = (
            height
            - (self.panelProperties.rowsInp.value() - 1)
            * self.panelProperties.gutterInp.value()
        ) / self.panelProperties.rowsInp.value()
        offset = self.panelProperties.gutterInp.value()
        offsetx = x
        offsety = y
        pen = QPen(Qt.white)
        pen.setWidth(5)

        # панели располагаются на позициях self.manipMatrix, где (i, j / 2) = 0
        for r in range(0, self.panelProperties.rowsInp.value()):
            for c in range(0, self.panelProperties.columnsInp.value()):
                rect = QGraphicsRectItem(offsetx, offsety, panelWidth, panelHeight)
                rect.setPen(pen)
                self.frameCollection.append(rect)
                self.manipMatrix[r * 2][c * 2] = rect
                offsetx += panelWidth + offset
                self.scene.addItem(rect)
            offsetx = x
            offsety += panelHeight + offset

        self.initManips(x, y, panelWidth, panelHeight)

    def initManips(self, x, y, width, height):
        offset = self.panelProperties.gutterInp.value()
        offsetx = width + x
        offsety = y
        for r in range(0, 2 * self.panelProperties.rowsInp.value() - 1):
            if r % 2 == 0:
                offsetx = width + x
                for c in range(0, self.panelProperties.columnsInp.value() - 1):
                    # rect = QGraphicsRectItem(offsetx, offsety, offset, height)
                    rect = ManipItem(offsetx, offsety, offset, height)
                    rect.setBrush(Qt.white)
                    rect.setOpacity(0.3)
                    self.scene.addItem(rect)
                    self.manipMatrix[r][c * 2 + 1] = rect
                    offsetx += offset + width
                    rect.emitter.itemSelected.connect(self.updateSliders)
                offsety += height
            else:
                offsetx = x
                for c in range(0, 2 * self.panelProperties.columnsInp.value() - 1):
                    if c % 2 == 0:
                        # rect = QGraphicsRectItem(offsetx, offsety, width, offset)
                        rect = ManipItem(offsetx, offsety, width, offset)
                        offsetx += width
                        rect.setBrush(Qt.white)
                        rect.setOpacity(0.3)
                        self.manipMatrix[r][c] = rect
                        rect.emitter.itemSelected.connect(self.updateSliders)
                    else:
                        # rect = QGraphicsRectItem(offsetx, offsety, offset, offset)
                        rect = ManipItem(offsetx, offsety, offset, offset)
                        rect.setBrush(Qt.cyan)
                        rect.setZValue(1000)
                        rect.setOpacity(0.3)
                        offsetx += offset
                        self.manipMatrix[r][c] = rect
                        rect.emitter.itemSelected.connect(self.updateSliders)
                    self.scene.addItem(rect)

                offsety += offset

    def kritaGroup(self):
        canvasSize(
            self.ACTIVE_DOC,
            self.bleedBorder.rect().x(),
            self.bleedBorder.rect().y(),
            self.bleedBorder.rect().width(),
            self.bleedBorder.rect().height(),
        )
        if self.bleedInp.value() > 0:
            addGuides(
                self.ACTIVE_DOC,
                self.canvasBorder.rect().width(),
                self.canvasBorder.rect().height(),
                self.toPixel(self.bleedInp.value()),
            )
        if not self.panelProperties.groupCheckbox.isChecked():
            oneGroupSetup(
                self.ACTIVE_DOC,
                self.frameCollection,
                self.bleedBorder.rect().x(),
                self.bleedBorder.rect().y(),
                self.bleedBorder.rect().width(),
                self.bleedBorder.rect().height(),
            )
        else:
            multigroupSetup(
                self.ACTIVE_DOC,
                self.frameCollection,
                self.bleedBorder.rect().x(),
                self.bleedBorder.rect().y(),
                self.bleedBorder.rect().width(),
                self.bleedBorder.rect().height(),
            )
        self.close()


# =====================ВЫВОД В KRITA==========================
def canvasSize(doc, x, y, width, height):
    # Изменяет размеры холста на заданные
    # Содержимое не масштабируется
    doc.resizeImage(x, y, width, height)


def addGuides(doc, width, height, bleed):
    # Добавление разметки для обозначения вылетов
    doc.setGuidesLocked(True)
    doc.setGuidesVisible(True)
    doc.setHorizontalGuides({bleed, height + bleed})
    doc.setVerticalGuides({bleed, width + bleed})


# Создание панелей, не разбитых по группам
def oneGroupSetup(doc, frameCollection, x, y, width, height):
    # Добавление в документ папки, содержащей пустой растровый слой,
    # векторный слой с границами, слой, выполняющий функцию обтравочной маски
    group = doc.createNode("Page", "grouplayer")
    doc.rootNode().addChildNode(group, None)
    doc.setActiveNode(group)
    layer = doc.createVectorLayer("Mask")
    group.addChildNode(layer, None)
    svg = oneLayerPanel(frameCollection, x, y, width, height)
    layer.addShapesFromSvg(svg)
    sketch = doc.createNode("Sketch", "paintlayer")
    sketch.setInheritAlpha(True)
    group.addChildNode(sketch, None)
    doc.setActiveNode(sketch)
    panels = doc.createCloneLayer("Mask clone-outline", layer)
    panels.setBlendingMode("multiply")
    group.addChildNode(panels, None)
    doc.refreshProjection()


def panelRect(x, y, width, height):
    return f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="white" stroke="black" stroke-width="4"/>'


def oneLayerPanel(frameCollection, x, y, width, height):
    # Преобразование в svg объектов QRectItems
    # все панели в одном svg-объекте
    svgString = f'<svg width="{width}" height="{height}" viewBox="{x} {y} {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">'
    frames = ""
    for panel in frameCollection:
        frames += panelRect(
            panel.rect().x(),
            panel.rect().y(),
            panel.rect().width(),
            panel.rect().height(),
        )
    svgString += frames + "</svg>"
    return svgString


def multilayerPanel(panel, x, y, width, height):
    # Преобразование в svg объектов QRectItems
    # все панели в одном svg-объекте
    svgString = f'<svg width="{width}" height="{height}" viewBox="{x} {y} {width} {height}" fill="none" xmlns="http://www.w3.org/2000/svg">'
    frames = ""
    frames += panelRect(
        panel.rect().x(), panel.rect().y(), panel.rect().width(), panel.rect().height()
    )
    svgString += frames + "</svg>"
    return svgString


# Создание панелей, разбитых по группам
def multigroupSetup(doc, frameCollection, x, y, width, height):
    # Добавление в документ папки, содержащей пустой растровый слой,
    # векторный слой с границами, слой, выполняющий функцию обтравочной маски
    for panel in frameCollection:
        group = doc.createNode("Page", "grouplayer")
        doc.rootNode().addChildNode(group, None)
        doc.setActiveNode(group)
        layer = doc.createVectorLayer("Mask")
        group.addChildNode(layer, None)
        svg = multilayerPanel(panel, x, y, width, height)
        layer.addShapesFromSvg(svg)
        sketch = doc.createNode("Sketch", "paintlayer")
        sketch.setInheritAlpha(True)
        group.addChildNode(sketch, None)
        doc.setActiveNode(sketch)
        panels = doc.createCloneLayer("Mask clone-outline", layer)
        panels.setBlendingMode("multiply")
        group.addChildNode(panels, None)
        doc.refreshProjection()
