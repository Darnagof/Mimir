from PIL import Image
from PyQt5.QtGui import QTransform
from PyQt5.QtCore import QPointF

def save_slice(imageToSave, savePath):
        # python-pillow can load any kind of image and save it in any common format
        image = Image.fromqpixmap(imageToSave)
        image.save(savePath, 'PNG')