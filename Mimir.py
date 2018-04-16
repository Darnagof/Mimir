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
from matplotlib import pyplot


class Mimir(QMainWindow, mimir_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)

        self.axial_slice = None
        self.sagittal_slice = None
        self.coronal_slice = None
        self.color_map = None
        self.contrast_min = None
        self.contrast_max = None
        self.cycle = 0
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
        self.axial_slice_slider.setEnabled(False)
        self.sagittal_slice_slider.setEnabled(False)
        self.coronal_slice_slider.setEnabled(False)
        self.cycle_slider.setEnabled(False)
        self.cycle_slider.valueChanged.connect(self.drawAllViewers)
        self.max_contrast_slider.setEnabled(False)
        self.max_contrast_slider.valueChanged.connect(self.drawAllViewers)
        self.min_contrast_slider.setEnabled(False)
        self.min_contrast_slider.valueChanged.connect(self.drawAllViewers)
        colormaps = pyplot.colormaps()
        colormaps.insert(0, "")
        self.comboBox.setEnabled(False)
        self.comboBox.addItems(colormaps)
        self.comboBox.currentIndexChanged.connect(self.drawAllViewers)
        for i in range(3):
            self.slice_sliders[i].valueChanged.connect(lambda value, i=i: self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value()))

    def openFile(self):
        image_path = QFileDialog.getOpenFileName(parent=self, directory=self.lastUsedPath, filter='*.nii *.nii.gz')
        if not os.path.isfile(image_path[0]): return
        self.image_file = Mimir_lib.Fd_data(image_path[0])
        self.lastUsedPath = os.path.dirname(image_path[0])
        self.filename = os.path.basename(image_path[0])
        self.filename = os.path.splitext(self.filename)[0]
        
        self.max_contrast_slider.setMaximum(self.image_file.contrast_max)
        self.max_contrast_slider.setMinimum(self.image_file.contrast_min)
        self.max_contrast_slider.setValue(self.image_file.contrast_max)
        self.min_contrast_slider.setMaximum(self.image_file.contrast_max)
        self.min_contrast_slider.setMinimum(self.image_file.contrast_min)
        self.min_contrast_slider.setValue(self.image_file.contrast_min)

        if len(self.image_file.shape) == 4:
            self.cycle_slider.setMaximum(self.image_file.shape[3] - 1)
            self.cycle_slider.setEnabled(True)

        for i in range(3):
            self.slice_sliders[i].setMaximum(self.image_file.shape[i] - 1)
        self.drawAllViewers()
        # Enable slice saving buttons
        self.axial_save_slice.setEnabled(True)
        self.sagittal_save_slice.setEnabled(True)
        self.coronal_save_slice.setEnabled(True)
        self.comboBox.setEnabled(True)
        self.axial_slice_slider.setEnabled(True)
        self.sagittal_slice_slider.setEnabled(True)
        self.coronal_slice_slider.setEnabled(True)
        self.max_contrast_slider.setEnabled(True)
        self.min_contrast_slider.setEnabled(True)

    def saveSlice(self, num_type):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(self.slices[num_type], save_path[0])

    def drawAllViewers(self):
        self.color_map = self.comboBox.currentText()
        self.contrast_min = self.min_contrast_slider.value()
        self.contrast_max = self.max_contrast_slider.value()
        self.cycle = self.cycle_slider.value()
        self.cycle_nb_label.setText(str(self.cycle) + "/" + str(self.cycle_slider.maximum()))
        self.contrast_nb_label.setText(str(self.contrast_min) + "|" + str(self.contrast_max))
        for i in range(3):
            self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value())

    def drawViewer(self, viewer, num_type, num_slice):
        self.slices[num_type] = self.image_file.get_slice(self.cycle, num_type, num_slice, self.contrast_min, self.contrast_max)
        if self.color_map:
            self.slices[num_type] = Mimir_lib.colormap(self.slices[num_type], self.color_map)
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