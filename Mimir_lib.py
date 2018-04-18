from PIL import Image, ImageDraw
import numpy
import nibabel
import pickle
from matplotlib import cm

class Fd_data:

    def __init__(self, path):
        self.img = nibabel.load(path)
        self.data = self.img.get_data()
        self.header = self.img.get_header()
        self.contrast_min = self.data.min()
        self.contrast_max = self.data.max()
        self.shape = self.data.shape
        self.points = []
        self.masks = []

    def _get_contrast_min(self):
        return self.contrast_min

    def _get_contrast_max(self):
        return self.contrast_max
    
    def _get_shape(self):
        return self.shape

    def get_slice(self, img_nb, plane_nb, slice_nb, contrast_min, contrast_max):
        # the slice(None) index will take an entire dimension, so using 2 of them and a number will reduce the
        # dimensions of the original array by one if the image is 3D
        slice_range = [slice(None)] * 3
        slice_range[plane_nb] = slice_nb
        slice_range = tuple(slice_range)

        # if the original image is 4D, we need to further reduce the number of dimensions by selecting a 3D image
        if len(self.shape) == 4: slice_range = slice_range + (img_nb,)
    
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
        image = self.__draw_points_masks(image, img_nb, plane_nb, slice_nb)
        return image, (pixdim[min(scales_indexes)], pixdim[max(scales_indexes)])
    
    def __draw_points_masks(self, image, img_nb, plane_nb, slice_nb):
        image_draw = ImageDraw.Draw(image)
        for mask in self.masks:
            image_draw.polygon([a[:plane_nb]+a[plane_nb+1:] for a in mask.points if a[plane_nb] == slice_nb], fill=128)
        image_draw.point([a[:plane_nb]+a[plane_nb+1:3] for a in self.points if a[3] == img_nb and a[plane_nb] == slice_nb], fill=32)
        return image

    def add_point(self, point):
        if len(point) == 4:
            self.points.append(point)
    
    def delete_point(self, index):
        if index < len(self.points) and index >= 0:
            del self.points[index]
    
    def add_point_to_mask(self, index, point):
        if index >= len(self.masks):
            self.masks[index] = Mask()
        self.masks[index].add_point(point)

    def delete_point_from_mask(self, index, pointIndex):
        self.masks[index].delete_point(pointIndex)

    def save_points_masks(self, save_path):
        with open(save_path, 'wb') as fp:
            pickle.dump((self.points, self.masks), fp)
    
    def load_points_masks(self, load_path):
        with open ('outfile', 'rb') as fp:
            l_points, l_masks = pickle.load(fp)
            self.points.extend(l_points)
            self.masks.extend(l_masks)

def colormap(image, color):
    cmap = cm.get_cmap(color)
    img = image.convert('L')
    img = numpy.array(img)
    img = cmap(img)
    img = numpy.uint8(img * 255)
    img = Image.fromarray(img)
    return img

def save_slice(image, save_path):
    # python-pillow can load any kind of image and save it in any common format
    image.save(save_path, 'PNG')

class Mask:
    def __init__(self):
        self.points = []
        self.index_freeze = -1
        self.value_freeze = -1
    
    def add_point(point):
        if len(point) == 3:
            if index_freeze != -1 and point[index_freeze] != value_freeze :
                return
            self.points.append(point)
            wc = [{}, {}, {}]
            t = []
            for b in a:
                for i, c in enumerate(b):
                    wc[i][c] = wc[i][c] + 1 if c in wc[i] else 1
            for k,v in enumerate(wc):
                for a in v:
                    if v[a] >= 2:
                        t.append((k, a))
            if len(t) == 0:
                del self.points[len(self.points)]
                return
            if len(t) == 1:
                self.index_freeze = t[0][0]
                self.value_freeze = t[0][1]           
    
    def delete_point(index):
        if index < len(self.points) and index >= 0:
            del self.points[index]