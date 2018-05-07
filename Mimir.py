from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene, QListView
from PyQt5.QtGui import QTransform, QStandardItemModel
from PyQt5.QtCore import QPointF, QStringListModel
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

## @brief GUI of Mímir
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
        self.maskMode = False
        self.currentMaskIndex = -1
        self.current_coords = [0, 0, 0]

        # Interface initialization
        self.setupUi(self)
        self.slice_viewers = [self.sagittal_slice_viewer, self.coronal_slice_viewer, self.axial_slice_viewer]
        self.slice_sliders = [self.sagittal_slice_slider, self.coronal_slice_slider, self.axial_slice_slider]
        self.points_list = self.findChild(QListView, 'pointsList')
        self.points_model = QStringListModel()
        self.points_list.setModel(self.points_model)
        self.masks_model = QStandardItemModel()
        self.masks_model.setHorizontalHeaderLabels(['#', 'Type'])
        self.masksList.setModel(self.masks_model)
        # --- Connection to functions
        self.axial_save_slice.clicked.connect(lambda: self.saveSlice(2))
        self.sagittal_save_slice.clicked.connect(lambda: self.saveSlice(0))
        self.coronal_save_slice.clicked.connect(lambda: self.saveSlice(1))
        self.actionClose.triggered.connect(self.closeFile)
        self.actionSave_points_masks.triggered.connect(self.savePointsMasks)
        self.actionLoad_points_masks.triggered.connect(self.loadPointsMasks)
        self.actionOpen.triggered.connect(self.openFile)
        for i in range(3):
            self.slice_sliders[i].valueChanged.connect(lambda value, i=i: self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value()))
        self.cycle_slider.valueChanged.connect(self.drawAllViewers)
        self.max_contrast_slider.valueChanged.connect(self.drawAllViewers)
        self.min_contrast_slider.valueChanged.connect(self.drawAllViewers)
        colormaps = pyplot.colormaps()
        colormaps.insert(0, "")
        self.comboBox.addItems(colormaps)
        self.comboBox.currentIndexChanged.connect(self.drawAllViewers)
        # --- Slice viewers
        for i, viewer in enumerate(self.slice_viewers):
            viewer.set_num(i)
            viewer.set_viewers(self.slice_viewers)
            viewer.set_sliders(self.slice_sliders)
            viewer.set_cycle_slider(self.cycle_slider)
        self.addPointBt.clicked.connect(lambda: self.add_point(self.current_coords, self.cycle))
        self.delPointBt.clicked.connect(lambda: self.delete_point())
        self.savePointsBt.clicked.connect(lambda: self.savePointsMasks())
        self.addMaskBt.clicked.connect(lambda: self.newMask())
        # Set most of UI to "not enabled"
        self.enableUi(False)

    ## @brief Enable or disable most of UI elements.
    # @details Enable or disable most of buttons or other elements for the user. It generaly depend if an image file is opended or not.
    # @param state If true, enable most of UI elements, otherwise disable them.
    def enableUi(self, state: bool):
        # --- Menu bar
        # ------ File
        self.actionClose.setEnabled(state)
        self.actionSave_points_masks.setEnabled(state)
        self.actionLoad_points_masks.setEnabled(state)
        # ------ Point
        self.menuPoint.setEnabled(state)
        # ------ Mask
        self.menuMask.setEnabled(state)
        # ------ Screenshot
        self.menuScreenshot.setEnabled(state)
        # --- Screenshot buttons
        self.axial_save_slice.setEnabled(state)
        self.sagittal_save_slice.setEnabled(state)
        self.coronal_save_slice.setEnabled(state)
        # --- Slice sliders
        self.axial_slice_slider.setEnabled(state)
        self.sagittal_slice_slider.setEnabled(state)
        self.coronal_slice_slider.setEnabled(state)
        # --- Cycle and contrast sliders
        self.cycle_slider.setEnabled(state)
        self.max_contrast_slider.setEnabled(state)
        self.min_contrast_slider.setEnabled(state)
        # --- Colormaps list
        self.comboBox.setEnabled(state)
        # --- Tabs (Main, Points and Masks)
        self.tabMenu.setEnabled(state)

    ## @brief Open image file.
    # @details Launche browser window to open an image file, then load the file in Mimir.
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
        # Enable UI functionnalities
        self.enableUi(True)
        # Try to load points
        if os.path.isfile(self.lastUsedPath + "/" + self.filename + ".mim"):
            self.image_file.load_points_masks(self.lastUsedPath + "/" + self.filename + ".mim")
            self.updatePointsList()
        # Set maximum to slice sliders
        for i in range(3):
            self.slice_sliders[i].setMaximum(self.image_file.shape[i] - 1)
        # First draw of images
        self.drawAllViewers()

    ## @brief Close image file.
    # @details Close image file then disable most of UI elements.
    def closeFile(self):
        del self.image_file
        self.enableUi(False)
        # self.clearViewers()

    ## @brief Save a slice as image file.
    # @details Save the current showed slice from a chosen view as image file (PNG)
    # @param num_type Select the view from where the slice is saved (0:sagittal, 1:coronal, 1:axial).
    def saveSlice(self, num_type: int):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(self.slices[num_type], save_path[0])

    ## @brief Draw all viewers
    # @details Draw all viewers according to the current coordinates
    def drawAllViewers(self):
        for i in range(3):
            self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value())

    ## @brief Draw one viewer
    # @details Draw one viewer according to the current coordinates
    # @param viewer
    # @param num_type
    # @param num_slice
    def drawViewer(self, viewer, num_type: int, num_slice: int):
        self.current_coords[num_type] = num_slice
        self.color_map = self.comboBox.currentText()
        self.contrast_min = self.min_contrast_slider.value()
        self.contrast_max = self.max_contrast_slider.value()
        self.cycle = self.cycle_slider.value()
        self.cycle_nb_label.setText(str(self.cycle) + "/" + str(self.cycle_slider.maximum()))
        contrast_min_percent = round((self.contrast_min-self.min_contrast_slider.minimum())/(self.min_contrast_slider.maximum()-self.min_contrast_slider.minimum())*100, 2)
        contrast_max_percent = round((self.contrast_max-self.max_contrast_slider.minimum())/(self.max_contrast_slider.maximum()-self.max_contrast_slider.minimum())*100, 2)
        self.contrast_nb_label.setText(str(contrast_min_percent) + "% | " + str(contrast_max_percent) + "%")
        self.slices[num_type], scale = self.image_file.get_slice(self.cycle, num_type, num_slice, self.contrast_min, self.contrast_max, self.color_map)
        pixmap = self.slices[num_type].toqpixmap()
        scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        scene.addPixmap(pixmap)
        viewer.setScene(scene)
        viewer.set_scale(scale)
        viewer.make_cursor()
        #viewer.show_cursor()

    ## @brief Clear all viewers
    def clearViewers(self):
        for viewer in self.slice_viewers:
            viewer.items.clear()

    ## @brief Update list of user-created points
    def updatePointsList(self):
        str_points = []
        for point in self.image_file.points:
            str_points.append(str(point))
        self.points_model.setStringList(str_points)

    ## @brief Add point into image file
    # @details Add a point, then update points list and viewers.
    # The point is not saved yet into the MIM file.
    # @param coords 3D-coordinates of the point
    # @param cycle
    def add_point(self, coords: list, cycle: int):
        self.image_file.add_point(coords + [cycle])
        print("Point added: " + str(coords + [cycle]))#DEBUG
        self.updatePointsList()
        self.drawAllViewers()

    ## @brief Delete point
    # @details Delete a point, then update points list and viewers.
    # The point deletion is not saved yet into the MIM file.
    def delete_point(self):
        for selection in self.points_list.selectedIndexes():
            self.image_file.delete_point(selection.row())
            print("Point deleted: " + str(selection.row()))#DEBUG
        self.updatePointsList()
        self.drawAllViewers()

    ## @brief Save points and masks
    # @details Save current points and masks into a MIM file. All deleted items are lost.
    def savePointsMasks(self):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.mim')
        self.image_file.save_points_masks(save_path[0])

    ## @brief Load points and masks from a MIM file
    # @details Load points and masks from a MIM file
    def loadPointsMasks(self):
        load_path = QFileDialog.getOpenFileName(parent=self, directory=self.lastUsedPath, filter='*.mim')
        self.image_file.load_points_masks(load_path[0])

    ## @brief Allow user to create a new mask
    def newMask(self):
        self.currentMaskIndex += 1
        self.toMaskMode(True)

    ## @brief Delete a point from a mask
    # @param index Index of the mask
    # @param pointIndex Index of the point
    def deletePointFromMask(self, index: int, pointIndex: int):
        self.image_file.delete_point_from_mask(index, pointIndex)

    ## @brief Update list of user-created masks
    def updateMasksList(self):
        print()

    ## @brief Switch to mask or point mode
    # @param state True = mask mode, False = point mode
    def toMaskMode(self, state: bool):
        self.maskMode = state
        if self.maskMode == True:
            print("Mask mode")
            self.enableUi(False)
        else:
            print("Point mode")
            self.enableUi(True)

    ## @brief Keyboard commands implementation
    # @param event Event containing the released key
    def keyReleaseEvent(self, event):
        # Space key : Add point to points or a mask
        if event.key() == QtCore.Qt.Key_Space:
            if(self.maskMode):
                self.image_file.add_point_to_mask([self.slice_sliders[0].value(), self.slice_sliders[1].value(), self.slice_sliders[2].value()], self.currentMaskIndex)
                print("Add point to mask ", self.currentMaskIndex, ": ", str([self.slice_sliders[0].value(), self.slice_sliders[1].value(), self.slice_sliders[2].value()]))
                self.drawAllViewers()
            else:
                self.add_point(self.current_coords, self.cycle)
        # Escape key : Quit mask mode
        if event.key() == QtCore.Qt.Key_Escape:
            self.toMaskMode(False)

def main():
    app = QApplication(sys.argv)
    form = Mimir()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()