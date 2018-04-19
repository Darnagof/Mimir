from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
from PyQt5 import QtCore
import sys
import mimir_ui
import os
import Mimir_lib
import nibabel
import numpy
from PIL import Image
from matplotlib import pyplot
from CursorGraphicsView import CursorGraphicsView


class Mimir(QMainWindow, mimir_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)

        self.axial_slice = None
        self.sagittal_slice = None
        self.coronal_slice = None
        self.color_map = None
        self.contrast_min = None
        self.contrast_max = None
        self.one_percent_contrast = 0.0
        self.cycle = 0
        self.lastUsedPath = os.path.dirname(os.path.abspath(__file__))
        self.slices = {0:self.sagittal_slice, 1:self.coronal_slice, 2:self.axial_slice}
        self.clickedCoords = [0, 0, 0]

        # Interface initialization
        self.setupUi(self)
        self.slice_viewers = [self.sagittal_slice_viewer, self.coronal_slice_viewer, self.axial_slice_viewer]
        self.slice_sliders = [self.sagittal_slice_slider, self.coronal_slice_slider, self.axial_slice_slider]
        self.actionOpen.triggered.connect(self.openFile)
        # --- Screenshot buttons
        self.axial_save_slice.clicked.connect(lambda: self.saveSlice(2))
        self.sagittal_save_slice.clicked.connect(lambda: self.saveSlice(0))
        self.coronal_save_slice.clicked.connect(lambda: self.saveSlice(1))
        self.axial_save_slice.setEnabled(False)
        self.sagittal_save_slice.setEnabled(False)
        self.coronal_save_slice.setEnabled(False)
        # --- Slice sliders
        self.axial_slice_slider.setEnabled(False)
        self.sagittal_slice_slider.setEnabled(False)
        self.coronal_slice_slider.setEnabled(False)
        for i in range(3):
            self.slice_sliders[i].valueChanged.connect(lambda value, i=i: self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value()))
        # --- Cycle and contrast sliders
        self.cycle_slider.setEnabled(False)
        self.cycle_slider.valueChanged.connect(self.drawAllViewers)
        self.max_contrast_slider.setEnabled(False)
        self.max_contrast_slider.valueChanged.connect(self.drawAllViewers)
        self.min_contrast_slider.setEnabled(False)
        self.min_contrast_slider.valueChanged.connect(self.drawAllViewers)
        # --- Colormaps list
        colormaps = pyplot.colormaps()
        colormaps.insert(0, "")
        self.comboBox.setEnabled(False)
        self.comboBox.addItems(colormaps)
        self.comboBox.currentIndexChanged.connect(self.drawAllViewers)
        # --- Mode radiobuttons
        self.mode_buttons = [self.marker_mode_button, self.mask_mode_button]
        self.marker_mode_button.setChecked(True)
        # --- Slice viewers
        for i, viewer in enumerate(self.slice_viewers):
            viewer.set_num(i)
            viewer.set_viewers(self.slice_viewers)
            viewer.set_sliders(self.slice_sliders)
            viewer.set_mode_buttons(self.mode_buttons)
            viewer.set_cycle_slider(self.cycle_slider)
            viewer.set_coords(self.clickedCoords)

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
        self.one_percent_contrast = 1/(self.image_file.contrast_max - self.image_file.contrast_min)*100

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
        # --- Slice viewers
        for i, viewer in enumerate(self.slice_viewers):
            viewer.set_fd_data(self.image_file)

    def saveSlice(self, num_type):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(self.slices[num_type], save_path[0])

    def drawAllViewers(self):
        for i in range(3):
            self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value())

    def drawViewer(self, viewer, num_type, num_slice):
        self.color_map = self.comboBox.currentText()
        self.contrast_min = self.min_contrast_slider.value()
        self.contrast_max = self.max_contrast_slider.value()
        self.cycle = self.cycle_slider.value()
        self.cycle_nb_label.setText(str(self.cycle) + "/" + str(self.cycle_slider.maximum()))
        contrast_min_percent = round((self.contrast_min-self.min_contrast_slider.minimum())/(self.min_contrast_slider.maximum()-self.min_contrast_slider.minimum())*100, 2)
        contrast_max_percent = round((self.contrast_max-self.max_contrast_slider.minimum())/(self.max_contrast_slider.maximum()-self.max_contrast_slider.minimum())*100, 2)
        self.contrast_nb_label.setText(str(contrast_min_percent) + "% | " + str(contrast_max_percent) + "%")
        self.slices[num_type], scale = self.image_file.get_slice(self.cycle, num_type, num_slice, self.contrast_min, self.contrast_max)
        if self.color_map:
            self.slices[num_type] = Mimir_lib.colormap(self.slices[num_type], self.color_map)
        pixmap = self.slices[num_type].toqpixmap()
        scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        scene.addPixmap(pixmap)
        viewer.setScene(scene)
        viewer.set_scale(scale)
        viewer.make_cursor()

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.image_file.add_point([self.slice_sliders[0].value(), self.slice_sliders[1].value(), self.slice_sliders[2].value(), self.cycle])
            print("Add point: " + str([self.slice_sliders[0].value(), self.slice_sliders[1].value(), self.slice_sliders[2].value(), self.cycle]))

def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()