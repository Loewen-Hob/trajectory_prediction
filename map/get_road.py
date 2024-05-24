import pandas as pd
from numba import njit
import numpy as np
from PIL import Image

def load_park_layout_from_image(image_path, max_dimension=1024, threshold=128):
    with Image.open(image_path) as img:
        original_width, original_height = img.size
        scaling_factor = min(max_dimension / original_width, max_dimension / original_height)
        new_width = int(original_width * scaling_factor)
        new_height = int(original_height * scaling_factor)
        img_resized = img.resize((new_width, new_height))
        img_gray = img_resized.convert('L')
        image_array = np.array(img_gray)
        binary_image = (image_array > threshold).astype(int)
        park_layout = np.where(binary_image == 0, 0, -1)
        return park_layout, scaling_factor

image_path = 'wrzx_notree.png'
park, scaling_factor = load_park_layout_from_image(image_path, max_dimension=1024, threshold=128)
print(park)