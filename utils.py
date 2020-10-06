import numpy as np


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
