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

    def get_slice(self, img_nb, plane_nb, slice_nb, contrast_min, contrast_max, colormap):
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
        if colormap:
            image = set_colormap(image, colormap)
        image = self.__draw_points_masks(image, img_nb, plane_nb, slice_nb)
        image = image.rotate(90, expand=True)
        pixdim = self.header['pixdim']
        new_width = int(round(image.width*pixdim[min(scales_indexes)]))
        new_height = int(round(image.height*pixdim[max(scales_indexes)]))
        
        
        image = image.resize((new_width, new_height))
        return image, (pixdim[min(scales_indexes)], pixdim[max(scales_indexes)])

    def __draw_points_masks(self, image, img_nb, plane_nb, slice_nb):
        image = image.convert('RGBA')
        image_draw = ImageDraw.Draw(image)
        #image_draw.line((100,200, 150, 300), fill=128, width=3)
        
        for mask in self.masks:
            mask_points = []
            for a in mask.points:
                if a[plane_nb] == slice_nb:
                    temp_list = a[:plane_nb]+a[plane_nb+1:]
                    temp_list.reverse()
                    mask_points.extend(temp_list)
            if len(mask_points) >= 4:
                image_draw.polygon(tuple(mask_points), fill=(255,0,0,255))
        points_position = []
        for a in self.points:
            if a[3] == img_nb and a[plane_nb] == slice_nb:
                temp_list = a[:plane_nb]+a[plane_nb+1:3]
                temp_list.reverse()
                print(slice_nb,temp_list)
                image_draw.point(tuple(temp_list), fill=(255,0,0,255))
        return image

    def add_point(self, point):
        if len(point) == 4 and point not in self.points:
            self.points.append(point)
    
    def delete_point(self, index):
        if index < len(self.points) and index >= 0:
            del self.points[index]
    
    def add_point_to_mask(self, point, index):
        while index >= len(self.masks):
            self.masks.append(Mask())
        if len(point) == 3 and point not in self.masks[index].points:
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

def set_colormap(image, color):
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
    
    def add_point(self, point):
        if len(point) == 3:
            if self.index_freeze != -1 and point[self.index_freeze] != self.value_freeze :
                return
            print("point",point)
            print("self.points",self.points)
            self.points.append(point)
            print("self.points",self.points)
            if len(self.points) > 1:
                wc = [{}, {}, {}]
                t = []
                for b in self.points:
                    print("b",b)
                    for i, c in enumerate(b):
                        print("i, c",i,c)
                        wc[i][c] = wc[i][c] + 1 if c in wc[i] else 1
                for k,v in enumerate(wc):
                    print("k,v",k,v)
                    for a in v:
                        print("a, v[a]",a, v[a])
                        if v[a] >= 2:
                            t.append((k, a))
                print("t",t)
                if len(t) == 0:
                    print("del self.points",self.points)
                    del self.points[len(self.points)-1]
                    return
                if len(t) == 1:
                    self.index_freeze = t[0][0]
                    self.value_freeze = t[0][1]           
        print("self.points",self.points)

    def delete_point(self, index):
        if index < len(self.points) and index >= 0:
            del self.points[index]