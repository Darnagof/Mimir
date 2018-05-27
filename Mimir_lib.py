from PIL import Image, ImageDraw
import numpy
import nibabel
import pickle
from matplotlib import cm
from matplotlib.path import Path

## @brief Data of the loaded image
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
        self.default_color = [255,0,0,255]
    
    ## @brief Get minimum contrast of the data
    def get_contrast_min(self):
        return self.contrast_min

    ## @brief Get maximum contrast of the data
    def get_contrast_max(self):
        return self.contrast_max

    ## @brief Get shape of the data
    # @details Number of slices in each dimension
    def get_shape(self):
        return self.shape

    ## @brief Get an image of a specific slice
    # @details Return an image of the chosen slice
    # @param img_nb Number of the cycle (temporal) of the chosen slice
    # @param plane_nb Number of the plane (0:sagittal, 1:coronal, 1:axial) of the chosen slice
    # @param slice_nb Number of the slice in the plane
    # @param contrast_min Minimum value wanted for the image
    # @param contrast_max Maximum value wanted for the image
    # @param colormap Name of the colormap to apply on the image
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

        converted = numpy.require(numpy.divide(numpy.subtract(plane, contrast_min), (contrast_max - contrast_min) / 255 if contrast_max != contrast_min else 1),
                                numpy.uint8, 'C')

        # the plane next needs to be scaled according to the scales in the NIfTI header
        scales_indexes = [((x + plane_nb) % 3) + 1 for x in [1, 2]]

        image = Image.fromarray(converted)
        if colormap:
            image = set_colormap(image, colormap)
        image = self._draw_points_masks(image, img_nb, plane_nb, slice_nb)
        image = image.rotate(90, expand=True)
        pixdim = self.header['pixdim']
        new_width = int(round(image.width*pixdim[min(scales_indexes)]))
        new_height = int(round(image.height*pixdim[max(scales_indexes)]))
        image = image.resize((new_width, new_height))

        return image, (pixdim[min(scales_indexes)], pixdim[max(scales_indexes)])

    ## @brief Draw the points and masks on the image
    # @details Return an image of the image with the points and the masks
    # @param image Image to modify
    # @param img_nb Number of the cycle (temporal) of the chosen slice
    # @param plane_nb Number of the plane (0:sagittal, 1:coronal, 1:axial) of the chosen slice
    # @param slice_nb Number of the slice in the plane
    def _draw_points_masks(self, image, img_nb, plane_nb, slice_nb):
        image = image.convert('RGB')
        image_draw = ImageDraw.Draw(image, 'RGBA')
        
        #Draw masks
        for mask in self.masks:
            mask_points = []
            for a in mask.points:
                if a[plane_nb] == slice_nb:
                    temp_list = a[:plane_nb]+a[plane_nb+1:]
                    temp_list.reverse()
                    mask_points.extend(temp_list)
            if len(mask_points) >= 4:
                color = mask.get_color() if mask.get_color() else self.default_color
                image_draw.polygon(tuple(mask_points), fill=tuple(color))

        #Draw points
        for a in self.points:
            if a[3] == img_nb and a[plane_nb] == slice_nb:
                color = a[4:] if a[4:] else self.default_color
                temp_list = a[:plane_nb]+a[plane_nb+1:3]
                temp_list.reverse()
                image_draw.ellipse([temp_list[0]-1, temp_list[1]-1, temp_list[0]+1, temp_list[1]+1], fill=tuple(color))
        return image

    ## @brief Add a point to the data
    # @param details Add a point to the list of points
    # @param point 4D coordinates of the point
    # @param color (R,G,B,A) color of the point
    def add_point(self, point, color=None):
        if len(point) == 4 and point not in self.points:
            color_point = color if color and len(color) == 4 else self.default_color
            self.points.append(point+color_point)
    
    ## @brief Change color of a point
    # @param index Index of the point in the list
    # @param color (R,G,B,A) color of the point
    def set_color_point(self, index, color):
        if index < len(self.points) and index >= 0 and len(color) == 4:
            self.points[index] = self.points[index][:4]+color

    ## @brief Delete a point
    # @param index Index of the point in the list
    def delete_point(self, index):
        if index < len(self.points) and index >= 0:
            del self.points[index]
    
    ## @brief Return a mask
    # @param index Index of the mask in the list
    def get_mask(self, index):
        while index >= len(self.masks):
            self.masks.append(Mask(self.shape[:3], self.header['pixdim']))
        return self.masks[index]

    ## @brief Delete a mask
    # @param index Index of the mask in the list
    def delete_mask(self, index):
        if index < len(self.masks) and index >=0:
            del self.masks[index]

    ## @brief Save masks and points in a file
    # @param save_path Path of the output file
    def save_points_masks(self, save_path):
        with open(save_path, 'wb') as fp:
            pickle.dump((self.points, self.masks), fp)
    
    ## @brief Load masks and points from a file
    # @param load_path Path of the input file
    def load_points_masks(self, load_path):
        del self.points[:]
        del self.masks[:]
        with open (load_path, 'rb') as fp:
            l_points, l_masks = pickle.load(fp)
            self.points.extend(l_points)
            self.masks.extend(l_masks)
                
## @brief Add a colormap to an image
# @param color Name of the colormap 
def set_colormap(image, color):
    cmap = cm.get_cmap(color)
    img = image.convert('L')
    img = numpy.array(img)
    img = cmap(img)
    img = numpy.uint8(img * 255)
    img = Image.fromarray(img)
    return img

## @brief Save an image as a PNG
# @param image Image to save
# @param save_path Path of the output file 
def save_slice(image, save_path):
    # python-pillow can load any kind of image and save it in any common format
    image.save(save_path, 'PNG')

## @brief Data of a mask
class Mask:
    def __init__(self, shape, pixdim):
        self.points = []
        self.index_freeze = -1
        self.value_freeze = -1
        self.color = None
        self.shape = shape
        self.pixdim = pixdim

    ## @brief Change the color of the mask
    # @param color (R,G,B,A) color of the mask
    def set_color(self, color):
        if len(color) == 4:
            self.color = color

    ## @brief Return color of the mask
    def get_color(self):
        return self.color

    ## @brief Add a point to the mask
    # @param point 3D coordinates of the point
    def add_point(self, point):
        if len(point) == 3 and point not in self.points:
            if self.index_freeze != -1 and point[self.index_freeze] != self.value_freeze :
                return 1
            self.points.append(point)
            #Check if the point is in the same plane as the mask
            if len(self.points) > 1:
                wc = [{}, {}, {}]
                t = []
                for b in self.points:
                    for i, c in enumerate(b):
                        wc[i][c] = wc[i][c] + 1 if c in wc[i] else 1
                for k,v in enumerate(wc):
                    for a in v:
                        if v[a] >= 2:
                            t.append((k, a))
                if len(t) == 0:
                    del self.points[len(self.points)-1]
                    return 1
                if len(t) == 1:
                    self.index_freeze = t[0][0]
                    self.value_freeze = t[0][1]           
            return 0
    ## @brief Delete a point
    # @param index Index of the point in the list
    def delete_point(self, index):
        if index < len(self.points) and index >= 0:
            del self.points[index]
    
    ## @brief Save a mask in a nifti file
    # @param save_path Path of the output file
    def save_mask_to_nifti(self, save_path):
        if self.index_freeze != -1:
            new_array = numpy.zeros(self.shape, dtype=numpy.float)
            
            nx, ny = (x for i,x in enumerate(self.shape) if i != self.index_freeze)
            poly_verts = [tuple(x for i,x in enumerate(point) if i != self.index_freeze) for point in self.points]


            x, y = numpy.meshgrid(numpy.arange(nx), numpy.arange(ny))
            x, y = x.flatten(), y.flatten()

            new_points = numpy.vstack((x,y)).T

            path = Path(poly_verts)
            grid = path.contains_points(new_points)
            grid = grid.reshape((ny,nx))
            for k,v in enumerate(new_array):
                for k2,v2 in enumerate(v):
                    for k3,v3 in enumerate(v2):
                        if self.index_freeze == 0 and self.value_freeze == k and grid[k3][k2] \
                        or self.index_freeze == 1 and self.value_freeze == k2 and grid[k3][k] \
                        or self.index_freeze == 2 and self.value_freeze == k3 and grid[k2][k]:
                            new_array[k][k2][k3] = 1.
        
            new_nifti = nibabel.Nifti1Image(new_array, affine=numpy.eye(4))
            hdr = new_nifti.get_header()
            hdr['pixdim'] = self.pixdim
            new_nifti.to_filename(save_path)