from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QAction, QGraphicsScene
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF
import sys
import design
import os
import POC_LIB
from PIL import Image, ImageOps


class ExampleApp(QMainWindow, design.Ui_MainWindow):
    def __init__(self, parent=None):
        super(ExampleApp, self).__init__(parent)
        self.setupUi(self)
        self.actionLoadFile.triggered.connect(self.browse_file)
        self.btnSave.clicked.connect(self.save_section)


    def browse_file(self):
        file_info = QFileDialog.getOpenFileName(parent=self, directory=os.path.expanduser('~'), filter='*.nii *.nii.gz')
        if not os.path.isfile(file_info[0]): return

        data, contrast_min, contrast_max, pixdim =  POC_LIB.nifty_parser(file_info[0])

        self.image = POC_LIB.format_image(data, contrast_min, contrast_max, pixdim)
        
        pixmap = self.image.toqpixmap()

        self.scene = QGraphicsScene(0, 0, pixmap.width(), pixmap.height())

        self.scene.addPixmap(pixmap)

        self.graphicsView.setScene(self.scene)

    def save_section(self):
        
        file_info = QFileDialog.getSaveFileName(parent=self, directory=os.path.expanduser('~'), filter='*.png')
        if file_info[0] == '': return
        POC_LIB.save_slice(self.image, file_info[0])

def main():
    app = QApplication(sys.argv)
    form = ExampleApp()
    form.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()