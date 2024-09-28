import sys

import resources
import sqlite3

from PyQt5.QtGui import QPainter, QColor, QPixmap, QPen, QIcon
from PyQt5.QtWidgets import QWidget, QPushButton, QMainWindow, QFileDialog, QMessageBox, \
    QDialog, QApplication, QLabel, QColorDialog, QInputDialog
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import QtWidgets, uic
from PIL import Image, ImageQt


def fill_files(): #создаю файлы, в которых будут хранится данные о настоящем цвете размере и цветах в ячейках
    with open('colors.txt', 'w') as f:
        f.write("#F63E69,#41E917,#17E9E9,#FDFD06")
    with open('current.txt', 'w') as f:
        f.write("#000000,4,1")


def clean_all():
    con = sqlite3.connect('test.db')
    cur = con.cursor()
    cur.execute("""DELETE FROM images""")
    con.commit()
    cur.close()


def insert_result(cnt, imName):
    con = sqlite3.connect('test.db')
    cur = con.cursor()

    with open(imName, "rb") as f:
        img = f.read()
    binary = sqlite3.Binary(img)
    cur.execute(""" INSERT INTO images (name, image) VALUES (?, ?)""", (cnt, binary))
    con.commit()
    cur.close()


def delete_all_last(cnt): #удаляет все данные начиная с индекса cnt
    con = sqlite3.connect('test.db')
    cur = con.cursor()
    cur.execute("delete from images where name >= (?)", (str(cnt),))
    con.commit()


def get_result(cnt):
    con = sqlite3.connect('test.db')
    cur = con.cursor()
    cur.execute("SELECT image FROM images where name = (?)", (str(cnt),))
    img = cur.fetchone()[0]
    with open("out.png", "wb") as f:
        f.write(img)
    con.commit()


def max_cnt(): #возвращает размер таблицы
    con = sqlite3.connect('test.db')
    cur = con.cursor()
    a = cur.execute("Select max(name) from images").fetchone()[0]
    con.commit()
    return a


class MainPaint(QWidget):
    def __init__(self):
        self.fname = ''
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('icon.png'))
        # canvas
        self.setWindowTitle('Холст')
        self.desktop = QApplication.desktop()
        self.screenRect = self.desktop.screenGeometry()
        self.height = self.screenRect.height()
        self.width = self.screenRect.width()
        self.resize(self.width, self.height)
        self.setStyleSheet("background-color : #BA8EFD;")
        self.page = QLabel(self)
        self.page.resize(self.width - 20, self.height - 180)

        with open("fileName.txt", 'r') as f:
            fname = f.readline()

        self.image = Image.new('RGB',
                               (self.page.size().width(), self.page.size().height()),
                               color='#FFFFFF')  # Except write
        if fname != '': #форматирование картинки на случай если она больше холста
            im = Image.open(fname)
            w, h = im.size
            k = 1
            if (self.page.height() / h) < 1:
                k = self.page.height() / h
            if (self.page.width() / w) < 1:
                k = min(self.page.width() / w, k)
            w = round(w * k)
            h = round(h * k)
            new_image = im.resize((w, h))
            self.image.paste(new_image)

        self.page.move(10, 50)
        self.image.save('image.jpg')
        self.pixmap = QPixmap("image.jpg")
        self.page.setPixmap(self.pixmap)
        self.page.show()
        self.count_of_pictures = 0
        clean_all()
        insert_result(self.count_of_pictures, "image.jpg")

        self.firstPointX = -1
        self.firstPointY = -1
        self.lastPointX = -1
        self.lastPointY = -1
        self.cnt = 0
        self.currentSize = 4
        self.fileButton = QPushButton(self)
        self.fileButton.move(10, 10)
        self.fileButton.setStyleSheet("background-color : #FDACE2;")
        self.fileButton.setText('Сохранить')
        self.fileButton.clicked.connect(self.filesOpen)

        self.cleanButton = QPushButton(self)
        self.cleanButton.move(130, 10)
        self.cleanButton.setStyleSheet("background-color : #FDACE2;")
        self.cleanButton.setText('Чистый лист')
        self.cleanButton.clicked.connect(self.cleanPage)

        self.undoButton = QPushButton(self)
        self.undoButton.move(250, 10)
        self.undoButton.setStyleSheet("background-color : #808080;")
        self.undoButton.setText('Undo')
        self.undoButton.clicked.connect(self.returnLastImage)

        self.redoButton = QPushButton(self)
        self.redoButton.move(370, 10)
        self.redoButton.setStyleSheet("background-color : #808080;")
        self.redoButton.setText('Redo')
        self.redoButton.clicked.connect(self.redoLastImage)

        self.mainButton = QPushButton(self)
        self.mainButton.move(490, 10)
        self.mainButton.setStyleSheet("background-color : #FDACE2;")
        self.mainButton.setText('Главная')
        self.mainButton.clicked.connect(self.instrumentsOpen)


    def cleanPage(self): #удаляет все из базы, заполняет первую картинку белым цветом
        self.count_of_pictures = 1
        clean_all()
        image = Image.new('RGB', (self.page.size().width(), self.page.size().height()),
                          color='#FFFFFF')
        image.save('image.jpg')
        insert_result(0, 'image.jpg')
        self.returnLastImage()
        self.redoButton.setStyleSheet("background-color : #808080;")

    def filesOpen(self):
        image = Image.open('image.jpg')

        imName = QtWidgets.QFileDialog.getSaveFileName(self, 'Save Image', 'image',
                                                       'Images (*.jpg)')[0]
        if imName:
            image.save(imName)

    def redoLastImage(self):
        if self.count_of_pictures < max_cnt():
            self.count_of_pictures += 1
            get_result(self.count_of_pictures)
            self.page.setPixmap(QPixmap("out.png"))
            self.page.show()
            self.undoButton.setStyleSheet("background-color : #FDACE2;")
            if self.count_of_pictures < max_cnt():
                self.redoButton.setStyleSheet("background-color : #FDACE2;")
            else:
                self.redoButton.setStyleSheet("background-color : #808080;")

    def returnLastImage(self):
        if self.count_of_pictures > 0:
            self.count_of_pictures -= 1
            get_result(self.count_of_pictures)
            self.page.setPixmap(QPixmap("out.png"))
            self.page.show()
            self.redoButton.setStyleSheet("background-color : #FDACE2;")
            if self.count_of_pictures > 0:
                self.undoButton.setStyleSheet("background-color : #FDACE2;")
            elif self.count_of_pictures == 0:
                self.undoButton.setStyleSheet("background-color : #808080;")

    def mousePressEvent(self, event):
        self.firstPointX = event.x()
        self.firstPointY = event.y()
        if self.check(event.x(), event.y() - 30):
            self.cnt = 1
            self.update()
        else:
            self.cnt = 3

    def mouseMoveEvent(self, event):
        self.lastPointX, self.lastPointY = event.x(), event.y()
        if self.check(event.x(), event.y() - 30):
            self.cnt = 2
            self.update()

    def mouseReleaseEvent(self, event):
        if self.cnt != 3:
            self.cnt = 0
            im = ImageQt.fromqpixmap(self.page.pixmap())
            im.save('image.jpg')
            self.count_of_pictures += 1
            delete_all_last(self.count_of_pictures)
            insert_result(self.count_of_pictures, "image.jpg")

    def check(self, x, y): #проверка если нажимают в поле
        xm, ym = self.page.pos().x(), self.page.pos().y() - 30
        xs, ys = self.page.size().width(), self.page.size().height()
        if xm > x or ym > y:
            return False
        if xm + xs < x or ym + ys < y:
            return False
        return True

    def paintEvent(self, event):
        qp = QPainter(self.page.pixmap())
        qp.begin(self)
        with open('current.txt', 'r') as f:
            currentColor, currentSize, status = f.readline().split(',')
            currentSize = int(currentSize)
            status = int(status)
        qp.setBrush(QColor(currentColor))
        if status:
            qp.setPen(QPen(QColor(currentColor), currentSize, Qt.SolidLine))
        else:
            qp.setPen(QPen(QColor('#ffffff'), currentSize, Qt.SolidLine))
        if self.cnt == 2: #линия
            qp.drawLine(self.firstPointX - 10, self.firstPointY - 50,
                        self.lastPointX - 10, self.lastPointY - 50)
            self.firstPointX, self.firstPointY = self.lastPointX, self.lastPointY
            self.undoButton.setStyleSheet("background-color : #FDACE2;")
        elif self.cnt == 1: #точка
            qp.drawPoint(self.firstPointX - 10, self.firstPointY - 50)
            self.undoButton.setStyleSheet("background-color : #FDACE2;")
        qp.end()

    def instrumentsOpen(self):
        self.child_win = Instruments()
        self.child_win.exec()


class MyWindow(QMainWindow, MainPaint):
    def __init__(self):
        super().__init__()
        self.setFixedSize(608, 379)
        uic.loadUi('intro.ui', self)
        self.openPage.clicked.connect(self.clickOpenButton)
        self.newPage.clicked.connect(self.clickCreateButton)
        self.pushButton.clicked.connect(self.clickInfoButton)

    def clickInfoButton(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Автор: Ксюша Бальба")
        dialog.setText("Спасибо, что используешь мой пейнт!")
        dialog.exec()


    def run(self):
        self.window = MainPaint()
        self.window.show()
        self.close()
        with open("fileName.txt", 'w') as f:
            f.truncate()

    def clickCreateButton(self):
        self.run()

    def clickOpenButton(self):
        fname = \
            QFileDialog.getOpenFileName(self, 'Select', '', 'Images (*.png *.xpm *.jpg)')[
                0]
        if fname:
            with open("fileName.txt", 'w') as f:
                f.write(fname)
            self.run()


class Instruments(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowIcon(QIcon('icon.png'))
        self.setWindowTitle('Главная')
        self.setFixedSize(365, 200)
        self.move(500, 300)
        self.setStyleSheet("background-color : #BA8EFD;")

        # button changer color
        self.colorButton = QPushButton('поменять цвет', self)
        self.colorButton.setStyleSheet("background-color : #8CC8CE;")
        self.colorButton.resize(120, 40)
        self.colorButton.move(10, 10)
        self.colorButton.clicked.connect(self.colorChanger)
        self.colorSqares = []
        with open('colors.txt', 'r') as f:
            colors = f.readline().split(',')
        for i in range(4):
            a = QPushButton(self)
            a.resize(40, 40)
            a.move(i * 55 + 150, 10)
            a.setStyleSheet("border :2px solid ;"
                            "background-color : {};".format(colors[i]))
            self.colorSqares.append(a)
            a.clicked.connect(self.getcolor)
        # pen size changer
        self.sizeButton = QPushButton('поменять размер', self)
        self.sizeButton.setStyleSheet("background-color : #8CC8CE;")
        self.sizeButton.resize(140, 40)
        self.sizeButton.move(10, 70)
        self.sizeButton.clicked.connect(self.sizeChanger)
        self.sizeSquare = QLabel(self)
        self.sizeSquare.setStyleSheet("border :2px solid ;"
                                      "background-color : white;")
        self.sizeSquare.resize(40, 40)
        self.sizeSquare.setAlignment(Qt.AlignCenter)
        self.sizeSquare.setText(str(self.GetCurrent(1)))
        self.label = QLabel('размер ручки: ', self)
        self.label.setStyleSheet("font : 10pt;")
        self.label.move(170, 75)
        self.sizeSquare.move(315, 70)
        # eraser
        self.eraseButton = QPushButton('ластик', self)
        self.eraseButton.move(10, 130)
        self.eraseButton.resize(160, 40)

        self.drawButton = QPushButton('ручка', self)
        self.drawButton.move(190, 130)
        self.drawButton.resize(160, 40)
        with open('current.txt', 'r') as f:
            currentColor, currentSize, status = f.readline().split(',')
        if int(status):
            self.drawButton.setStyleSheet("background-color : #8CC8CE;")
            self.eraseButton.setStyleSheet("background-color : #c3c3c3;")
        else:
            self.drawButton.setStyleSheet("background-color : #c3c3c3;")
            self.eraseButton.setStyleSheet("background-color : #8CC8CE;")
        self.eraseButton.clicked.connect(self.eraserActivate)
        self.drawButton.clicked.connect(self.eraserDisActivate)

    def changeCurrent(self, indx, item):
        with open('current.txt', 'r') as f:
            a = f.readline().split(',')
        a[indx] = item
        with open('current.txt', 'w') as f:
            f.write(','.join(a))

    def GetCurrent(self, indx):
        with open('current.txt', 'r') as f:
            a = f.readline().split(',')
        return a[indx]

    def eraserActivate(self):
        self.changeCurrent(2, '0')
        self.drawButton.setStyleSheet("background-color : #c3c3c3;")
        self.eraseButton.setStyleSheet("background-color : #8CC8CE;")

    def eraserDisActivate(self):
        self.changeCurrent(2, '1')
        self.drawButton.setStyleSheet("background-color : #8CC8CE;")
        self.eraseButton.setStyleSheet("background-color : #c3c3c3;")

    def getcolor(self):
        with open('colors.txt', 'r') as f:
            colors = f.readline().split(',')
        k = self.colorSqares.index(self.sender())
        self.colorButton.setStyleSheet("background-color : {};".format(colors[k]))
        currentColor = colors[k]
        self.changeCurrent(0, currentColor)

    def colorChanger(self):
        with open('colors.txt', 'r') as f:
            colors = f.readline().split(',')
        color = QColorDialog.getColor()
        if color.isValid():
            currentColor = color.name()
            self.colorButton.setStyleSheet("background-color : {};".format(color.name()))
            for i in range(3):
                self.colorSqares[i].setStyleSheet("border :3px solid ;"
                                                  "background-color : {};".format(
                    colors[i + 1]))
                colors[i] = colors[i + 1]
            self.colorSqares[3].setStyleSheet("border :3px solid ;"
                                              "background-color : {};".format(
                color.name()))
            colors[3] = color.name()
            with open('colors.txt', 'w') as f:
                f.write(','.join(colors))
            self.changeCurrent(0, currentColor)

    def sizeChanger(self):
        currentSize = int(self.GetCurrent(1))
        sz, ok_pressed = QInputDialog.getInt(
            self, "Размер", "Введите желаемый размер",
            currentSize, 2, 30, 2)
        if ok_pressed:
            self.changeCurrent(1, str(sz))
            self.sizeSquare.setText(str(sz))


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


fill_files() # чистит бд

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec_())
