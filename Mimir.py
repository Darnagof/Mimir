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
        self.lastUsedPath = os.path.dirname(os.path.abspath(__file__))
        self.slices = {0:self.sagittal_slice, 1:self.coronal_slice, 2:self.axial_slice}

        # Interface initialization
        self.setupUi(self)
        self.slice_viewers = {0:self.sagittal_slice_viewer, 1:self.coronal_slice_viewer, 2:self.axial_slice_viewer}
        self.slice_sliders = {0:self.sagittal_slice_slider, 1:self.coronal_slice_slider, 2:self.axial_slice_slider}
        self.actionOpen.triggered.connect(self.openFile)
        self.axial_save_slice.clicked.connect(lambda: self.saveSlice(2))
        self.sagittal_save_slice.clicked.connect(lambda: self.saveSlice(0))
        self.coronal_save_slice.clicked.connect(lambda: self.saveSlice(1))
        self.axial_save_slice.setEnabled(False)
        self.sagittal_save_slice.setEnabled(False)
        self.coronal_save_slice.setEnabled(False)
        for i in range(3):
            self.slice_sliders[i].valueChanged.connect(lambda value, i=i: self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value()))

    def openFile(self):
        image_path = QFileDialog.getOpenFileName(parent=self, directory=self.lastUsedPath, filter='*.nii *.nii.gz')
        if not os.path.isfile(image_path[0]): return
        self.image_file = Mimir_lib.Fd_data(image_path[0])
        self.lastUsedPath = os.path.dirname(image_path[0])
        self.filename = os.path.basename(image_path[0])
        self.filename = os.path.splitext(self.filename)[0]
        
        for i in range(3):
            self.drawViewer(self.slice_viewers[i], i, 0)
            self.slice_sliders[i].setMaximum(self.image_file._get_shape()[i] - 1)

        # Enable slice saving buttons
        self.axial_save_slice.setEnabled(True)
        self.sagittal_save_slice.setEnabled(True)
        self.coronal_save_slice.setEnabled(True)

    def saveSlice(self, num_type):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(self.slices[num_type], save_path[0])

    def drawViewer(self, viewer, num_type, num_slice):
        self.slices[num_type] = self.image_file.get_slice(0, num_type, num_slice, self.image_file.contrast_min, self.image_file.contrast_max)
        pixmap = self.slices[num_type].toqpixmap()
        scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        scene.addPixmap(pixmap)
        viewer.setScene(scene)


def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()