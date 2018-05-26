from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene, QListView, QTreeWidget, QTreeWidgetItem, QColorDialog, QMessageBox, QToolButton
from PyQt5.QtGui import QTransform, QStandardItemModel, QStandardItem, QColor
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

    ## @brief Initiate Qt interface and variables
    def __init__(self, parent=None):
        super(Mimir, self).__init__(parent)

        self.image_file = None
        self.axial_slice = None
        self.sagittal_slice = None
        self.coronal_slice = None
        self.color_map = None
        self.contrast_min = None
        self.contrast_max = None
        self.cycle = 0
        self.lastUsedPath = os.path.dirname(os.path.abspath(__file__))
        self.slices = {0:self.sagittal_slice, 1:self.coronal_slice, 2:self.axial_slice}
        self.maskMode = False
        self.currentMaskIndex = -1
        self.current_coords = [0, 0, 0]

        # Interface initialization
        self.setupUi(self)
        self.showMaximized()
        self.slice_viewers = [self.sagittal_slice_viewer, self.coronal_slice_viewer, self.axial_slice_viewer]
        self.slice_sliders = [self.sagittal_slice_slider, self.coronal_slice_slider, self.axial_slice_slider]
        self.slice_labels = [self.sagittal_slice_label, self.coronal_slice_label, self.axial_slice_label]
        # Points list
        self.points_list = self.findChild(QListView, 'pointsList')
        self.points_model = QStringListModel()
        self.points_list.setModel(self.points_model)
        # Masks list
        self.masks_list = self.findChild(QTreeWidget, 'masksList')
        # --- Connection to functions
        # ------ Save slice buttons
        self.axial_save_slice.clicked.connect(lambda: self.saveSlice(2))
        self.sagittal_save_slice.clicked.connect(lambda: self.saveSlice(0))
        self.coronal_save_slice.clicked.connect(lambda: self.saveSlice(1))
        # ------ File menu
        self.actionClose.triggered.connect(self.closeFile)
        self.actionOpen.triggered.connect(self.openFile)
        self.actionSave_points_masks.triggered.connect(self.savePointsMasks)
        self.actionLoad_points_masks.triggered.connect(self.loadPointsMasks)
        # ------ Point menu
        self.actionNew_point.triggered.connect(lambda: self.add_point(self.current_coords, self.cycle))
        self.actionDelete_point.triggered.connect(lambda: self.delete_point())
        # ------ Mask menu
        self.actionNew_mask.triggered.connect(lambda: self.newMask())
        self.actionDelete_mask.triggered.connect(lambda: self.delete_mask())
        self.actionSet_color.triggered.connect(lambda: self.setMaskColor())
        self.actionSave_to_NifTI.triggered.connect(lambda: self.saveMaskToNifti())
        self.actionSave_all_to_NifTI.triggered.connect(lambda: self.saveAllMasksToNifti())
        # ------ Screenshot menu
        self.actionSave_current_axial_slice.triggered.connect(lambda: self.saveSlice(2))
        self.actionSave_current_sagittal_slice.triggered.connect(lambda: self.saveSlice(0))
        self.actionSave_current_coronal_slice.triggered.connect(lambda: self.saveSlice(1))
        # ------ Sliders
        for i in range(3):
            self.slice_sliders[i].valueChanged.connect(lambda value, i=i: self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value()))
        self.cycle_slider.valueChanged.connect(self.drawAllViewers)
        self.max_contrast_slider.valueChanged.connect(self.drawAllViewers)
        self.min_contrast_slider.valueChanged.connect(self.drawAllViewers)
        # ------ Colormap list
        colormaps = pyplot.colormaps()
        colormaps.insert(0, "")
        self.comboBox.addItems(colormaps)
        self.comboBox.currentIndexChanged.connect(self.drawAllViewers)
        # ------ Points tab
        self.addPointBt.clicked.connect(lambda: self.add_point(self.current_coords, self.cycle))
        self.delPointBt.clicked.connect(lambda: self.delete_point())
        self.savePointsBt.clicked.connect(lambda: self.savePointsMasks())
        # ------ Masks tab
        self.addMaskBt.clicked.connect(lambda: self.newMask())
        self.delMaskBt.clicked.connect(lambda: self.delete_mask())
        self.saveMasksBt.clicked.connect(lambda: self.savePointsMasks())
        self.saveMaskNiftiBt.clicked.connect(lambda: self.saveMaskToNifti())
        self.saveAllMasksNiftiBt.clicked.connect(lambda: self.saveAllMasksToNifti())
        self.masks_list.itemDoubleClicked.connect(lambda: self.goToMask())
        # --- Slice viewers
        for i, viewer in enumerate(self.slice_viewers):
            viewer.set_num(i)
            viewer.set_viewers(self.slice_viewers)
            viewer.set_sliders(self.slice_sliders)
            viewer.set_cycle_slider(self.cycle_slider)
        # Set most of UI to "not enabled"
        self.enableUi(False)
        self.enableViewers(False)

    ## @brief Enable or disable most of UI elements
    # @details Enable or disable most of buttons or other elements for the user. It generaly depend if an image file is opened or not.
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

    def enableViewers(self, state: bool):
        # --- Viewers
        for viewer in self.slice_viewers:
            viewer.setEnabled(state)

    ## @brief Open image file
    # @details Launch browser window to open an image file, then load the file in Mimir.
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
        else:
            self.cycle_slider.setMaximum(0)
        # Enable UI functionnalities
        self.enableUi(True)
        self.enableViewers(True)
        # Try to load points and masks
        if os.path.isfile(self.lastUsedPath + "/" + self.filename + ".mim"):
            self.image_file.load_points_masks(self.lastUsedPath + "/" + self.filename + ".mim")
            self.currentMaskIndex = self.getLastMaskIndex()
        # Set maximum to slice sliders and reset cursors position
        for i in range(3):
            self.slice_sliders[i].setMaximum(self.image_file.shape[i] - 1)
        # First draw of images
        self.drawAllViewers()
        # Update masks and points lists
        self.updatePointsList()
        self.updateMasksList()

    ## @brief Close image file
    # @details Close image file then disable most of UI elements and clear viewers.
    def closeFile(self):
        self.image_file = None
        self.enableUi(False)
        self.enableViewers(False)
        self.clearViewers()
        # Clear points list
        self.points_model.removeRows(0, self.points_model.rowCount())
        # Clear masks list
        self.masks_list.clear()

    ## @brief Save a slice as image file.
    # @details Save the current showed slice from a chosen view as image file (PNG).
    # @param num_type Select the view from where the slice is saved (0:sagittal, 1:coronal, 1:axial).
    def saveSlice(self, num_type: int):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.png')
        if save_path[0] == '': return
        Mimir_lib.save_slice(self.slices[num_type], save_path[0])

    ## @brief Draw all viewers
    # @details Draw all viewers according to the current coordinates.
    def drawAllViewers(self):
        for i in range(3):
            self.drawViewer(self.slice_viewers[i], i, self.slice_sliders[i].value())

    ## @brief Draw one viewer
    # @details Draw one viewer according to the current coordinates.
    # @param viewer Viewer object to draw with
    # @param num_type 0:sagittal view, 1: coronal view, 2: axial view
    # @param num_slice Index of slice to draw.
    def drawViewer(self, viewer, num_type: int, num_slice: int):
        self.current_coords[num_type] = num_slice
        self.slice_labels[num_type].setText(str(num_slice))
        self.color_map = self.comboBox.currentText()
        self.contrast_min = self.min_contrast_slider.value()
        self.contrast_max = self.max_contrast_slider.value()
        self.cycle = self.cycle_slider.value()
        self.cycle_nb_label.setText(str(self.cycle) + "/" + str(self.cycle_slider.maximum()))
        if self.min_contrast_slider.minimum() != self.min_contrast_slider.maximum():
            contrast_min_percent = round((self.contrast_min-self.min_contrast_slider.minimum())/(self.min_contrast_slider.maximum()-self.min_contrast_slider.minimum())*100, 2)
        else:
            contrast_min_percent = 0
        if self.max_contrast_slider.minimum() != self.max_contrast_slider.maximum():
            contrast_max_percent = round((self.contrast_max-self.max_contrast_slider.minimum())/(self.max_contrast_slider.maximum()-self.max_contrast_slider.minimum())*100, 2)
        else:
            contrast_max_percent = 0
        self.contrast_nb_label.setText(str(contrast_min_percent) + "% | " + str(contrast_max_percent) + "%")
        self.slices[num_type], scale = self.image_file.get_slice(self.cycle, num_type, num_slice, self.contrast_min, self.contrast_max, self.color_map)
        pixmap = self.slices[num_type].toqpixmap()
        scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())
        scene.addPixmap(pixmap)
        viewer.setScene(scene)
        viewer.set_scale(scale)
        viewer.make_cursor()
        #viewer.show_cursor()

    ## @brief Clear all viewers.
    def clearViewers(self):
        for viewer in self.slice_viewers:
            viewer.scene().clear()

    ## @brief Update list of user-created points.
    def updatePointsList(self):
        str_points = []
        for point in self.image_file.points:
            str_points.append(str(point[:4]))
        self.points_model.setStringList(str_points)

    ## @brief Add point into image file
    # @details Add a point, then update points list and viewers.
    # The point is not saved yet into the MIM file.
    # @param coords 3D-coordinates of the point
    # @param cycle Cycle index
    def add_point(self, coords: list, cycle: int):
        self.image_file.add_point(coords + [cycle])
        print("Point added: " + str(coords + [cycle]))#DEBUG
        self.updatePointsList()
        self.drawAllViewers()

    ## @brief Delete selected point
    # @details Delete the selected point, then update points list and viewers.
    # The point deletion is not saved yet into the MIM file.
    def delete_point(self):
        for selection in self.points_list.selectedIndexes():
            self.image_file.delete_point(selection.row())
            print("Point deleted: " + str(selection.row()))#DEBUG
        self.updatePointsList()
        self.drawAllViewers()

    ## @brief Update list of user-created masks
    def updateMasksList(self):
        self.masks_list.clear()
        root = self.masks_list.invisibleRootItem()
        for i, mask in enumerate(self.image_file.masks):
            child = QTreeWidgetItem([str(i)])
            root.addChild(child)
            colorButton = QToolButton(self)
            maskColor = mask.get_color() or [255, 0, 0, 0]
            maskColorHex = QColor(maskColor[0], maskColor[1], maskColor[2], maskColor[3]).name()
            colorButton.setStyleSheet("background-color:" + maskColorHex + ";")
            colorButton.setFixedWidth(colorButton.height())
            colorButton.clicked.connect(lambda value, i=i: self.setMaskColor(i))
            self.masks_list.setItemWidget(child, 1, colorButton)
            for point in mask.points:
                root.child(i).addChild(QTreeWidgetItem([str(point)]))
            self.masks_list.setColumnWidth(0, 200)

    ## @brief Delete selected mask or point from mask
    # @details Delete the selected mask or point from a mask , then update masks list and viewers.
    # The mask/point deletion is not saved yet into the MIM file.
    def delete_mask(self):
        if self.masks_list.currentItem():
            # If point selected
            if self.masks_list.indexOfTopLevelItem(self.masks_list.currentItem())==-1:
                self.image_file.get_mask(self.masks_list.currentIndex().parent().row()).delete_point(self.masks_list.currentItem().parent().indexOfChild(self.masks_list.currentItem()))
                print("Delete from mask #" + str(self.masks_list.currentIndex().parent().row()) + " point n°" + str(self.masks_list.currentItem().parent().indexOfChild(self.masks_list.currentItem())))
            # Else mask selected
            else:
                self.image_file.delete_mask(self.masks_list.currentIndex().row())
                print("Delete mask #"+str(self.masks_list.currentIndex().row()))
            self.updateMasksList()
            self.drawAllViewers()
            self.currentMaskIndex = self.getLastMaskIndex()

    ## @brief Save points and masks
    # @details Save current points and masks into a MIM file. All deleted items are lost.
    def savePointsMasks(self):
        save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/'+self.filename, filter='*.mim')
        self.image_file.save_points_masks(save_path[0])

    ## @brief Load points and masks from a MIM file
    # @details Open a file explorer to load points and masks from a MIM file.
    def loadPointsMasks(self):
        load_path = QFileDialog.getOpenFileName(parent=self, directory=self.lastUsedPath, filter='*.mim')
        if not os.path.isfile(load_path[0]): return
        self.image_file.load_points_masks(load_path[0])
        self.currentMaskIndex = self.getLastMaskIndex()
        self.updatePointsList()
        self.updateMasksList()
        self.drawAllViewers()

    ## @brief Save selected mask to a NifTI file
    def saveMaskToNifti(self):
        # A mask must be selected
        if self.masks_list.currentItem():
            if self.masks_list.indexOfTopLevelItem(self.masks_list.currentItem())!=-1:
                save_path = QFileDialog.getSaveFileName(parent=self, directory=self.lastUsedPath+'/', filter='*.nii')
                self.image_file.get_mask(self.masks_list.currentIndex().row()).save_mask_to_nifti(save_path[0])

    ## @brief Save all masks to NifTI files
    def saveAllMasksToNifti(self):
        save_directory = QFileDialog.getExistingDirectory(self, "Select folder to save all masks", self.lastUsedPath+'/', QFileDialog.ShowDirsOnly)
        print(save_directory)
        if not os.path.isdir(save_directory): return
        for i in range(len(self.image_file.masks)):
            self.image_file.get_mask(i).save_mask_to_nifti(save_directory + "/" + self.filename + "_mask" + str(i))

    ## @brief Allow user to create a new mask
    def newMask(self):
        self.currentMaskIndex += 1
        self.toMaskMode(True)

    ## @brief Get last index of masks from the image file
    def getLastMaskIndex(self):
        return len(self.image_file.masks) - 1

    ## @brief Go to mask or point of mask coordinates
    def goToMask(self):
        # If point selected
        if self.masks_list.indexOfTopLevelItem(self.masks_list.currentItem())==-1:
            goto = self.image_file.get_mask(self.masks_list.currentIndex().parent().row()).points[0]
        # Else mask selected
        else:
            goto = self.image_file.get_mask(self.masks_list.currentIndex().row()).points[0]
        for i, slider in enumerate(self.slice_sliders): slider.setValue(goto[i])
    
    ## @brief Open color window to change mask color
    # @details Open menu to change the color of a mask.
    # @param index Index of the mask to change the color. If None, it will be the index of the selected mask in list.
    def setMaskColor(self, index = None):
        print("Index: " + str(index))
        # If mask selected in masks list
        if index == None: 
            if self.masks_list.currentItem() and self.masks_list.indexOfTopLevelItem(self.masks_list.currentItem())!=-1:
                index = self.masks_list.currentIndex().row()
            else:
                print("No mask selected")
                return
        # Verify if there is a mask with the chosen index
        if index <= self.getLastMaskIndex():
            mask = self.image_file.get_mask(index)
            maskColor = mask.get_color() or [255, 0, 0, 255]
            newColor = QColorDialog.getColor(QColor(maskColor[0], maskColor[1], maskColor[2], maskColor[3]), self, "Mask color", QColorDialog.ShowAlphaChannel)
            if newColor.isValid():
                mask.set_color(newColor.getRgb())
                self.drawAllViewers()
                self.updateMasksList()
            else: print("Invalid color")
        else:
            print("Invalid mask index")

    ## @brief Switch to mask or point mode
    # @param state True = mask mode, False = point mode
    def toMaskMode(self, state: bool):
        if self.maskMode != state:
            self.maskMode = state
            if self.maskMode == True:
                print("Mask mode")
                self.enableUi(False)
            else:
                print("Point mode")
                self.enableUi(True)
                self.updateMasksList()
                self.currentMaskIndex = self.getLastMaskIndex()

    ## @brief Keyboard commands implementation
    # @param event Event containing the released key
    def keyReleaseEvent(self, event):
        if self.image_file:
            # Space key : Add point to points or a mask
            if event.key() == QtCore.Qt.Key_Space:
                if(self.maskMode):
                    self.image_file.get_mask(self.currentMaskIndex).add_point([self.slice_sliders[0].value(), self.slice_sliders[1].value(), self.slice_sliders[2].value()])
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