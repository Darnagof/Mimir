from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
import sys
import mimir_ui
import os
import Mimir_lib
import nibabel
import numpy
from PIL import Image

class Mimir(QMainWindow, mimir_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)

        self.axial_slice = None
        self.sagittal_slice = None
        self.coronal_slice = None

        # Interface initialization
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.openFile)
        self.axial_save_slice.clicked.connect(lambda: self.saveSlice(self.axial_slice))
        self.sagittal_save_slice.clicked.connect(lambda: self.saveSlice(self.sagittal_slice))
        self.coronal_save_slice.clicked.connect(lambda: self.saveSlice(self.coronal_slice))
        self.axial_save_slice.setEnabled(False)
        self.sagittal_save_slice.setEnabled(False)
        self.coronal_save_slice.setEnabled(False)

    def openFile(self):
        image_path = QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser('~'), filter='*.nii *.nii.gz')
        if not os.path.isfile(image_path[0]): return
        self.image_file = Mimir_lib.Fd_data(image_path[0])

        # Axial
        self.axial_slice = self.image_file.get_slice(0, 156, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.axial_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.axial_slice_viewer.setScene(self.scene)
        # Sagittal
        self.sagittal_slice = self.image_file.get_slice(1, 156, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.sagittal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.sagittal_slice_viewer.setScene(self.scene)
        # Coronal
        self.coronal_slice = self.image_file.get_slice(2, 12, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.coronal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.coronal_slice_viewer.setScene(self.scene)

        # Enable slice saving buttons
        self.axial_save_slice.setEnabled(True)
        self.sagittal_save_slice.setEnabled(True)
        self.coronal_save_slice.setEnabled(True)

    def saveSlice(self, slice):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=os.path.expanduser('~'), filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(slice, save_path[0])

def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()