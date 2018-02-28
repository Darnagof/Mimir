import argparse
import Mimir_lib
import os
import sys

parser = argparse.ArgumentParser(description='Process 2D, 3D or 4D images.')
parser.add_argument('path_in', help='Path of image to be processed')
parser.add_argument('-o', dest='path_out', help='Output file')
parser.add_argument('-t', dest='img_nb', type=int, default=0, help='In case of a 4D image, select the time of the image to process')
parser.add_argument('slice_type', choices=['SAG', '0', 'COR', '1', 'AXI', '2'], help='View of image to be processed')
parser.add_argument('slice_nb', type=int, help='Number of the slice to process')
parser.add_argument('-c', '--cmap', '--colormap', dest='cmap', help='Add a colormap too the processed image')
parser.add_argument('-x', '--contr-min', dest='contrast_min', default=0, type=float, help='Adjust the minimum contrast in %%')
parser.add_argument('-y', '--contr-max', dest='contrast_max', default=100, type=float, help='Adjust the maximum contrast in %%')
args = parser.parse_args()

if not os.path.isfile(args.path_in):
    print('Error: The file',args.path_in,'does not exist.')
    sys.exit()

fd_data = Mimir_lib.Fd_data(args.path_in)

plane_nb = 0 if args.slice_type == 'SAG' else 1 if args.slice_type == 'COR' else 2 if args.slice_type == 'AXI' else args.slice_type
contrast_min = round(fd_data.contrast_min+args.contrast_min*(fd_data.contrast_max-fd_data.contrast_min)/100)
contrast_max = round(fd_data.contrast_min+args.contrast_max*(fd_data.contrast_max-fd_data.contrast_min)/100)

img = fd_data.get_slice(args.img_nb, plane_nb, args.slice_nb, contrast_min, contrast_max)

if args.cmap:
    img = Mimir_lib.colormap(img, args.cmap)

path_out = args.path_out if args.path_out else './a.png'

Mimir_lib.save_slice(img, path_out)