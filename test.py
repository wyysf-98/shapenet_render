import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def sample_sphere(num_samples, scale=1, use_half=False):
    """ sample angles from the sphere
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


if __name__ == "__main__":
    pos_list = sample_sphere(1000, 1, False)

    print(len(pos_list))
    fig = plt.figure()
    ax = Axes3D(fig)
    ax.scatter(pos_list[:, 0], pos_list[:, 1], pos_list[:, 2])

    ax.set_zlabel('Z')
    ax.set_ylabel('Y')
    ax.set_xlabel('X')
    plt.show()
