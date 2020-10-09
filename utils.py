import os
import math
import numpy as np
import OpenEXR
import Imath
from PIL import Image 
from glob import glob
from mathutils import Matrix
from mathutils import Vector

# Blender utils


def convert_obj2glb(src_dir, dst_dir):
    os.system("obj2gltf -i %s -o %s" % (src_dir, dst_dir))

# Render utils


def sample_sphere(num_samples, scale=1, use_half=False):
    """ sample x,y,z location from the sphere
    reference: https://zhuanlan.zhihu.com/p/25988652?group_id=828963677192491008
    """
    phi = (np.sqrt(5) - 1.0) / 2.
    pos_list = []
    for n in range(1, num_samples+1):
        z = (2. * n - 1) / num_samples - 1.
        x = np.cos(2*np.pi*n*phi)*np.sqrt(1-z*z)
        y = np.sin(2*np.pi*n*phi)*np.sqrt(1-z*z)
        if use_half and z < 0:
            continue
        pos_list.append((x*scale, y*scale, z*scale))

    return np.array(pos_list)


def sample_side(scale=2):
    """ sample x,y,z location from six sides
    """
    pos_list = [
        (1*scale, 0, 0),
        (-1*scale, 0, 0),
        (0, 2*scale, 0),
        (0, -2*scale, 0),
        (0, 0, 2*scale),
        (0, 0, -2*scale),
    ]

    return pos_list


def obj_location(dist, azi, ele):
    ele = math.radians(ele)
    azi = math.radians(azi)
    x = dist * math.cos(azi) * math.cos(ele)
    y = dist * math.sin(azi) * math.cos(ele)
    z = dist * math.sin(ele)
    return x, y, z

# Output utils
## Prefix output filename. eg(1_001.png to 1.png)
def prefix_name(out_paths):
    for out_path in out_paths:  
        end_str = '.png'
        if os.path.exists(out_path+'0001'+'.exr'):
            end_str = '.exr'
        outRenderFileNamePadded = out_path+'0001'+end_str
        outRenderFileName = out_path+end_str
        if os.path.exists(outRenderFileName):
            os.remove(outRenderFileName)
        os.rename(outRenderFileNamePadded, outRenderFileName)
        if end_str == '.exr':
            exr_to_png(outRenderFileName)

def exr_to_png(exr_path):
    depth_path = exr_path.replace('.exr', '.png')
    exr_image = OpenEXR.InputFile(exr_path)
    dw = exr_image.header()['dataWindow']
    (width, height) = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)

    def read_exr(s, width, height):
        mat = np.fromstring(s, dtype=np.float32)
        mat = mat.reshape(height, width)
        return mat

    dmap, _, _ = [read_exr(s, width, height) for s in exr_image.channels('BGR', Imath.PixelType(Imath.PixelType.FLOAT))]
    dmap = Image.fromarray((dmap != 1).astype(np.int32))
    dmap.save(depth_path)
    exr_image.close()
    # os.system('rm {}'.format(exr_path))
