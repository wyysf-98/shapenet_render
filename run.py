import os
import os.path as osp
import subprocess

from config import *

if __name__ == "__main__":
    # command = [blender_path, '--background', '--python', 'blender_render.py']
    command = [blender_path, '--python', 'blender_render.py']
    subprocess.run(command)