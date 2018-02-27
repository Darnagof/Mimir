from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
import sys
import mimir_ui
import os
import POC_LIB
import nibabel
import numpy
from PIL import Image

class Mimir(QMainWindow, mimir_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)
        self.setupUi(self)
        self.actionOpen.triggered.connect(self.openFile)

        self.axial_save_slice.clicked.connect(self.saveSlice(self.axial_slice))
        self.sagittal_save_slice.clicked.connect(self.saveSlice(self.sagittal_slice))
        self.coronal_save_slice.clicked.connect(self.saveSlice(self.coronal_slice))

    def openFile(self):
        self.image_file = QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser('~'), filter='*.nii *.nii.gz')
        if not os.path.isfile(self.image_file[0]): return
        
        # Axial
        axial_data =  POC_LIB.nifty_parser(self.image_file[0], 0, 156)
        self.axial_slice = POC_LIB.format_image(*axial_data, 0)
        pixmap = self.axial_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.axial_graphic_view.setScene(self.scene)
        # Sagittal
        sagittal_data =  POC_LIB.nifty_parser(self.image_file[0], 1, 156)
        self.sagittal_slice = POC_LIB.format_image(*sagittal_data, 1)
        pixmap = self.sagittal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.sagittal_graphic_view.setScene(self.scene)
        # Coronal
        coronal_data =  POC_LIB.nifty_parser(self.image_file[0], 2, 12)
        self.coronal_slice = POC_LIB.format_image(*coronal_data, 2)
        pixmap = self.coronal_slice.toqpixmap()
        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        self.scene.addPixmap(pixmap)
        self.coronal_graphic_view.setScene(self.scene)

    def saveSlice(self, slice):
        file_info = QFileDialog.getSaveFileName(parent=self, directory=os.path.expanduser('~'), filter='*.png')
        if file_info[0] == '': return
        POC_LIB.save_slice(slice, file_info[0])

def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()