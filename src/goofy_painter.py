from PyQt6.QtCore import QTimer, Qt, QSize
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QHBoxLayout, QMainWindow, QFileDialog, QMessageBox
from PIL import Image, ImageQt, ImageDraw
import numpy as np
import os
import math


class PaintWidget(QWidget):
    """
    Class that inherits from QWidget responsible for image
    display and painting
        -Loads image into numpy array
        -Implements drawing tools
        -Handles mouse events in painting

    """
    def __init__(self, picture_path):
        """
        Load the image and set up the painting canvas
        """
        super().__init__()
        img = Image.open(picture_path).convert('RGBA')
        self.arr = np.array(img)
        self.h, self.w, _ = self.arr.shape
        self.y, self.x = np.indices((self.h, self.w))

        self.label = QLabel()
        self.label.setFixedSize(self.w, self.h)
        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.label)

        self.painting = False # Flag to toggle painting on/off
        self.refresh()

    def refresh(self):
        """
        Takes the numpy array of the image and "redraws" into label
        """
        self.label.setPixmap(QPixmap.fromImage(
            ImageQt.ImageQt(
                Image.fromarray(self.arr))))

    def cycle_colors(self, mask):
        """
        Rotates R,G,B -> G,B,R for pixels where the mask is True

        Parameters
            mask: Numpy array of booleans indicating which pixels to modify
        """
        if not np.any(mask):
            return
        cols = self.arr[mask, :3].copy()
        self.arr[mask, 0] = cols[:, 1] # takes red make it green
        self.arr[mask, 1] = cols[:, 2] # takes green makes it blue
        self.arr[mask, 2] = cols[:, 0] # takes blue make it red
        if self.arr.shape[2] == 4:
            self.arr[mask, 3] = 255

    def draw_circle(self, x, y, r=30):
        """
        Uses color cycle to draw circle of radius r centered around point (x,y)

        Parameters
        x: x coordinate - center
        y: y coordinate - center
        r: radius of circle
        """
        mask = (self.x - x)**2 + (self.y - y)**2 <= r*r
        self.cycle_colors(mask)

    def draw_star(self, x, y, r=30, ratio=.27, pts=4):
        """
        Draw a cyan filled star centered around point (x,y)

        Parameters
            x: x coordinate
            y: y coordinate
            r: radius of star
            ratio: ratio of inner to outer radius i.e. spikyness of star
            pts: number of points of the star

        """
        vertices =[ (x + (r if i%2==0 else r*ratio) * math.cos(math.pi*i/pts - math.pi/2),
                  y + (r if i%2==0 else r*ratio) * math.sin(math.pi*i/pts - math.pi/2))
                 for i in range(pts*2)] #fancy math using polar coordinates -> Cartesian positions

        #creates a template to use for star
        tile =Image.new("L", (self.w, self.h),0)
        ImageDraw.Draw(tile).polygon(vertices, fill=255)
        mask = np.array(tile)>0

        #bakes in cyan for the star color
        self.arr[mask, 0] = 0
        self.arr[mask, 1] = 255
        self.arr[mask, 2] = 255
        if self.arr.shape[2] == 4:
            self.arr[mask, 3] = 255

    def mousePressEvent(self, event):
        """
        Start to paint when clicking left, draw star every right click
        """
        x,y = int(event.pos().x()), int(event.pos().y())
        if event.button() == Qt.MouseButton.LeftButton:
            self.painting = True
            self.draw_circle(x,y)
            self.refresh()
        elif event.button() == Qt.MouseButton.RightButton:
            self.draw_star(x,y)
            self.refresh()

    def mouseMoveEvent(self, event):
        """
        Continue to draw while dragging the mouse and pressing left button
        """
        if self.painting and event.buttons()&Qt.MouseButton.LeftButton:
            x,y = int(event.pos().x()), int(event.pos().y())
            self.draw_circle(x,y)
            self.refresh()


    def mouseReleaseEvent(self, event):
        """
        Stop painting when left button is released
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.painting = False

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Inherits from QMainWindow and opens current directory
        for user to import file from. Only allows for png,jpg, and jpeg extensions.
        Then uses the PaintWidget class to read and edit the image into MainWindow
        """
        super().__init__()
        self.setWindowTitle("HW10 : Goofy Colors and Shapes on Images")
        path_to_start = os.getcwd()
        path, _ = QFileDialog.getOpenFileName(self, "Open File", path_to_start, "Image Files (*.png *.jpg *.jpeg)")
        if not path:
            QMessageBox.information(self, "Error", "No File Selected. Program will now exit.Try again.")
            QTimer.singleShot(0, QApplication.instance().quit)
            return
        self.my_pic = PaintWidget(path)
        self.setCentralWidget(self.my_pic)

        #fixed window size to avoid issues with scaling/offset.
        w= self.my_pic.w
        h = self.my_pic.h
        self.setFixedSize(w, h)


app = QApplication([])
window = MainWindow()
window.show()
app.exec()
