from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
import sys
import mimir_ui
import os
import POC_LIB
import Mimir_lib
import nibabel
import numpy
from PIL import Image

class Mimir(QMainWindow, mimir_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.openFile)

        #self.axial_save_slice.clicked.connect(self.saveSlice(self.axial_slice))
        #self.sagittal_save_slice.clicked.connect(self.saveSlice(self.sagittal_slice))
        #self.coronal_save_slice.clicked.connect(self.saveSlice(self.coronal_slice))

    def openFile(self):
        image_path = QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser('~'), filter='*.nii *.nii.gz')
        if not os.path.isfile(image_path[0]): return
        
        self.image_file = Mimir_lib.Fd_data(image_path[0])

        # Axial
        self.axial_slice = self.image_file.get_slice(0, 156, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.axial_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.axial_graphic_view.setScene(self.scene)
        # Sagittal
        self.sagittal_slice = self.image_file.get_slice(1, 156, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.sagittal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.sagittal_graphic_view.setScene(self.scene)
        # Coronal
        self.coronal_slice = self.image_file.get_slice(2, 156, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.coronal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.coronal_graphic_view.setScene(self.scene)

def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()