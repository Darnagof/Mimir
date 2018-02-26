from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
import sys
import design
import os
import POC_LIB
import nibabel
import numpy
from PIL import Image


class ExampleApp(QMainWindow, design.Ui_MainWindow):
    def __init__(self, parent=None):
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.actionLoadFile.triggered.connect(self.browse_file)
        self.btnSave.clicked.connect(self.save_section)

    def browse_file(self):
        file_info = QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser('~'), filter='*.nii *.nii.gz')
        if not os.path.isfile(file_info[0]): return

        self.niba_img = nibabel.load(file_info[0])


        data = self.niba_img.get_data()
        header = self.niba_img.get_header()

        # we need a 2D array from a 3D or 4D array to display as an image

        # the slice(None) index will take an entire dimension, so using 2 of them and a number will reduce the
        # dimensions of the original array by one if the image is 3D
        slice_range = [slice(None)] * 3
        slice_range[1] = 156
        slice_range = tuple(slice_range)


        # after the 2D plane has been extracted, the contrast must be changed according to the contrast sliders' values
        plane = numpy.copy(data[slice_range])
        image_min = -1024
        image_max = 1969
        plane[plane < image_min] = image_min
        plane[plane > image_max] = image_max

        converted = numpy.require(numpy.divide(numpy.subtract(plane, image_min), (image_max - image_min) / 255),
                                  numpy.uint8, 'C')
        # the plane next needs to be scaled according to the scales in the NIfTI header
        transform = QTransform()
        scales_indexes = [((x + 1) % 3) + 1 for x in [1, 2]]
        scale = QPointF(header['pixdim'][min(scales_indexes)], header['pixdim'][max(scales_indexes)])

        # the plane needs to be rotated in order to be properly displayed
        transform.scale(scale.x(), scale.y())
        transform.rotate(-90)


        self.pixmap = Image.fromarray(converted).toqpixmap().transformed(transform)

        self.scene = QGraphicsScene(0, 0, self.pixmap.width(), self.pixmap.height())

        self.scene.addPixmap(self.pixmap)

        self.graphicsView.setScene(self.scene)

    def save_section(self):
        
        file_info = QFileDialog.getSaveFileName(parent=self, directory=os.path.expanduser('~'), filter='*.png')
        if not os.path.isfile(file_info[0]): return
        POC_LIB.save_slice(self.pixmap, file_info[0])

    """
    def closeEvent (self, eventQCloseEvent):
        self.scene.clear() # Clear QGraphicsPixmapItem
        eventQCloseEvent.accept() # Accept to close program
    """

def main():
    app = QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()