import argparse
import Mimir_lib
import os
import sys

## @brief Check if a path exist, create it if not
# @param file_path Path to check
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)


parser = argparse.ArgumentParser(description='Process 2D, 3D or 4D images.')
parser.add_argument('path_in', help='Path of image to be processed')
parser.add_argument('-o', dest='path_out', help='Output file')
parser.add_argument('-t', '--img_nb', dest='img_nb', type=int, help='In case of a 4D image, select the time of the image to process')
parser.add_argument('-p', '--plane', dest='plane', choices=['SAG', '0', 'COR', '1', 'AXI', '2'], help='View of image to be processed')
parser.add_argument('-s', '--slice_nb', dest='slice_nb', type=int, help='Number of the slice to process')
parser.add_argument('-c', '--cmap', '--colormap', dest='cmap', help='Add a colormap to the processed image')
parser.add_argument('-m', '--contrast-min', dest='contrast_min', default=0, type=float, help='Adjust the minimum contrast in %% (0-100)')
parser.add_argument('-M', '--contrast-max', dest='contrast_max', default=100, type=float, help='Adjust the maximum contrast in %% (0-100)')
parser.add_argument('--all', dest='all', action='store_true', help='Process every slice possible with the options given')
parser.add_argument('-l', '--link', dest='link', help='Link a .mim file to print points and masks stored in it')
args = parser.parse_args()

if not os.path.isfile(args.path_in):
    parser.error('The file',args.path_in,'does not exist.')

image_file = Mimir_lib.Fd_data(args.path_in)
if(args.link):
    image_file.load_points_masks(args.link)

if(args.plane):
    plane_nb = {'SAG':0, '0':0, 'COR':1, '1':1, 'AXI':2, '2':2}.get(args.plane)

if(args.contrast_min and (args.contrast_min < 0 or args.contrast_min > 100)):
    parser.error('argument -m/--contrast_min: invalid choice {} (choose in range 0-100)'.format(args.contrast_min))
if(args.contrast_max and (args.contrast_max < 0 or args.contrast_max > 100)):
    parser.error('argument -M/--contrast_max: invalid choice {} (choose in range 0-100)'.format(args.contrast_max))
if(args.img_nb and (args.img_nb < 0 or args.img_nb > image_file.shape[3])):
    parser.error('argument -t/--img_nb: invalid choice {} (choose in range 0-{})'.format(args.img_nb, image_file.shape[3]))

contrast_min = round(image_file.contrast_min+args.contrast_min*(image_file.contrast_max-image_file.contrast_min)/100)
contrast_max = round(image_file.contrast_min+args.contrast_max*(image_file.contrast_max-image_file.contrast_min)/100)

#Save every slices corresponding to the given options
if(args.all):
    for i in range(args.img_nb if args.img_nb else 0, args.img_nb + 1 if args.img_nb else image_file.shape[3]):
        for j in range(plane_nb if args.plane else 0, plane_nb + 1 if args.plane else 3):
            if(args.slice_nb and (args.slice_nb < 0 or args.slice_nb > image_file.shape[j])):
                parser.error('argument -s/--slice_nb: invalid choice {} (choose in range 0-{} for {} plane)'.format(args.slice_nb, image_file.shape[j], {0:'SAG', 1:'COR', 2:'AXI'}.get(j)))
            for k in range(args.slice_nb if args.slice_nb else 0, args.slice_nb + 1 if args.slice_nb else image_file.shape[j]):
                img, scale = image_file.get_slice(i, j, k, contrast_min, contrast_max, args.cmap)
                path_out = "{}/{}/{}/{}/{}.png".format((os.path.dirname(args.path_out) if args.path_out else os.path.dirname(args.path_in)),os.path.splitext(args.path_in)[0],i,{0:'SAG', 1:'COR', 2:'AXI'}.get(j),k)
                ensure_dir(path_out)
                Mimir_lib.save_slice(img, path_out)
else:
    if (args.plane and args.slice_nb):
        if(args.slice_nb and (args.slice_nb < 0 or args.slice_nb > image_file.shape[plane_nb])):
            parser.error('argument -s/--slice_nb: invalid choice {} (choose in range 0-{} for {} plane)'.format(args.slice_nb, image_file.shape[plane_nb], {0:'SAG', 1:'COR', 2:'AXI'}.get(plane_nb)))
        img, scale = image_file.get_slice(args.img_nb if args.img_nb else 0, plane_nb, args.slice_nb, contrast_min, contrast_max, args.cmap)
        path_out = args.path_out if args.path_out else "{}/{}.png".format(os.path.dirname(args.path_in),os.path.splitext(args.path_in)[0])
        
        ensure_dir(path_out)
        Mimir_lib.save_slice(img, path_out)
    else:
        parser.error('both plane and slice_nb arguments are obligatory if --all flag is not set.')