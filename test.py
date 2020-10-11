import cv2
import numpy as np

image = cv2.imread('./output_side_6_512x512/depth/02876657/dc0926ce09d6ce78eb8e919b102c6c08/0.exr', cv2.IMREAD_UNCHANGED)
print(np.min(image))
cv2.imwrite('save_cv2.img', image)