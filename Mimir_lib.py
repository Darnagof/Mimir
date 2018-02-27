from PIL import Image
import numpy
import nibabel
from pprint import pprint

class Fd_data:

    def __init__(self, path):
        self.img = nibabel.load(path)
        self.data = self.img.get_data()
        self.header = self.img.get_header()
        self.contrast_min = self.data.min()
        self.contrast_max = self.data.max()

    def _get_contrast_min(self):
        return self.contrast_min

    def _get_contrast_max(self):
        return self.contrast_max

    def get_slice(self, plane_nb, slice_nb, contrast_min, contrast_max):
        # the slice(None) index will take an entire dimension, so using 2 of them and a number will reduce the
        # dimensions of the original array by one if the image is 3D
        slice_range = [slice(None)] * 3
        slice_range[plane_nb] = slice_nb
        slice_range = tuple(slice_range)
    
        # after the 2D plane has been extracted, the contrast must be changed according to the contrast sliders' values
        plane = numpy.copy(self.data[slice_range])
        plane[plane < contrast_min] = contrast_min
        plane[plane > contrast_max] = contrast_max

        converted = numpy.require(numpy.divide(numpy.subtract(plane, contrast_min), (contrast_max - contrast_min) / 255),
                                numpy.uint8, 'C')

        # the plane next needs to be scaled according to the scales in the NIfTI header
        scales_indexes = [((x + plane_nb) % 3) + 1 for x in [1, 2]]

        image = Image.fromarray(converted)

        image = image.rotate(90, expand=True)
        pixdim = self.header['pixdim']
        new_width = int(round(image.width*pixdim[min(scales_indexes)]))
        new_height = int(round(image.height*pixdim[max(scales_indexes)]))
        image = image.resize((new_width, new_height))

        return image

def save_slice(image, save_path):
    # python-pillow can load any kind of image and save it in any common format
    image.save(save_path, 'PNG')