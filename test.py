from glob import glob
from utils import *
from config import *
import sys
sys.path.append(include_path)

BASE_PATH = '/Volumes/Weiyu/Datasets/shapenet/shapenet_render'

exr_imgs = glob(BASE_PATH + '/*/depth/*/*/*.exr')
for exr_img in exr_imgs:
    print(exr_img)
    exr_to_png(exr_img, True)