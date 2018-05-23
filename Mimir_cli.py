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

## @brief Check if a string is a int
# @param s String to check
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

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
parser.add_argument('-e','--edit_points', dest='edit', action='store_true', help='Edit points and masks in the specified slices (if no other options, all slices are accessible)')
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

#MASK AND POINTS EDITION MODE
if(args.edit):
    input_value = [""]
    path_out = args.path_out if args.path_out else "{}/{}.mim".format(os.path.dirname(args.path_in),os.path.splitext(args.path_in)[0])
    ensure_dir(path_out)
    edit_point = True
    last_index = len(image_file.masks) - 1
    actual_index = 0
    while(input_value[0] != "save" and input_value[0] != "exit"):
        input_value = input("{}> ".format("point" if edit_point else "mask {}".format(actual_index))).split()
        #SAVE
        if(input_value[0] == "save"):
            image_file.save_points_masks(path_out)
            print("Masks and points saved in {}".format(path_out))
        #CHANGE TO MASK MODE
        elif(input_value[0] == "mask" or input_value[0] == "m" or input_value[0] == "masks"):
            edit_point = False
            if len(input_value) == 1:
                last_index += 1
                actual_index = last_index
            elif(is_int(input_value[1])):
                actual_index = int(input_value[1])
        #CHANGE TO POINT MODE
        elif(input_value[0] == "point" or input_value[0] == "p" or input_value[0] == "points"):
            edit_point = True
        #DELETION
        elif(input_value[0] == "del" or input_value[0] == "d" or input_value == "delete"):
            if(is_int(input_value[1])):
                if(edit_point): #POINT MODE
                    image_file.delete_point(int(input_value[1]))
                else: #MASK MODE
                    image_file.get_mask(actual_index).delete_point(int(input_value[1]))
                print("Point {} deleted".format(input_value[1]))
            elif(input_value[1] == "mask" and is_int(input_value[2])):
                image_file.delete_mask(int(input_value[2]))
                print("Mask {} deleted".format(input_value[2]))
        #COLOR CHANGE
        elif(input_value[0] == "col" or input_value[0] == "c" or input_value[0] == "color"):
            if(edit_point and is_int(input_value[1])): #POINT MODE
                color = []
                if(len(input_value[2:]) == 4):
                    for v in input_value[2:]:
                        if(is_int(v) and int(v) < 256 and int(v) >= 0):
                            color.append(int(v))
                        else:
                            print("Color must be number in range (0-255).")
                    if(len(color) == 4):
                        image_file.set_color_point(input_value[1], input_value[2:])
                        print("Point {} set to color {}".format(input_value[1], input_value[2:]))
                    else:
                        print("Color must be number in range (0-255).")
                else:
                    print("Color must be R G B A.")
            else: #MASK MODE
                color = []
                if(len(input_value[1:]) == 4):
                    for v in input_value[1:]:
                        if(is_int(v)):
                            color.append(int(v))
                    if(len(color) == 4):
                        image_file.get_mask(actual_index).set_color(color)
                        print("Mask set to color {}".format(input_value[1:]))
        #DATA PRINT
        elif(input_value[0] == "data"):
            print("Points :")
            for i,point in enumerate(image_file.points):
                print("\t",i,point[:4],"color : ",point[4:])
            print("________\nMasks:")
            for i,mask in enumerate(image_file.masks):
                print("\t",i)
                for j,point in enumerate(mask.points):
                    print("\t\t",j,point)
        #HELP
        elif(input_value[0] == "help" or input_value[0] == "h" or input_value[0] == "?"):
            print("  save : \n\t\tSave the mim file to the output file provided or to the default output file ({}).".format("{}/{}.mim".format(os.path.dirname(args.path_in),os.path.splitext(args.path_in)[0])))
            print("  m|mask|masks [index] : \n\t\tEdit new mask or specific mask if index provided.")
            print("  p|point|points : \n\t\tEdit points.")
            print("  d|del|delete [mask] index : \n\t\tDelete point at index (from data if in point mode, from mask if in mask mode) or mask if specified \"mask\".")
            print("  c|col|color [index] R G B A : \n\t\tSet point at index to color (R,G,B,A) if in point mode, set mask to color if in mask mode.")
            print("  data : \n\t\tPrint all masks and points.")
            print("  ?|h|help : \n\t\tPrint this help.")
            print("  SAG COR AXI [T] [R G B A] : \n\t\tAdd point (4D) and color to data if in point mode, add point (3D) if in mask mode.")
            print("  exit : \n\t\tExit (Be careful, it won't save automatically)")
        #POINT ADDITION
        elif(input_value[0] != "exit"):
            if(edit_point): #POINT MODE
                point = []
                if(len(input_value) == 4 or len(input_value) == 8):
                    for v in input_value:
                        if(is_int(v)):
                            point.append(int(v))
                    if(len(point) == 4 or len(point) == 8):
                        image_file.add_point(point[:4], point[4:])
                        print("Point {} added".format(point[:4]), "with color {}".format(point[4:]) if point[4:] else "")
            else: #MASK MODE
                point = []
                if(len(input_value) == 3):
                    for v in input_value:
                        if(is_int(v)):
                            point.append(int(v))
                    if(len(point) == 3):
                        err = image_file.get_mask(actual_index).add_point(point)
                        if err:
                            print("Point {} not in mask's plan".format(point))
                        else:
                            print("Point {} added".format(point))
#SLICE RECUPERATION MODE
else:
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