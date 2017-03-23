"""
Use this to get HSV ranges for cropped images (e.g. a beanbag by itself)

Usage: python hsvRange.py --image image_file [--alpha error_tolerance]
"""
import numpy as np
import argparse
import cv2

# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="Path to the image")
ap.add_argument("-a", "--alpha", default=5, help="Error tolerance [0, 50]")
args = vars(ap.parse_args())

# Print HSV bounds
image = cv2.imread(args['image'])
alpha = int(args['alpha'])
if not 0 <= alpha <= 50:
    raise ValueError("Alpha must be between 0 and 50.")
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
hue = [channels[0] for sublist in hsv for channels in sublist]
sat = [channels[1] for sublist in hsv for channels in sublist]
val = [channels[2] for sublist in hsv for channels in sublist]
lo_hue = np.percentile(hue, alpha)
hi_hue = np.percentile(hue, 100 - alpha)
lo_sat = np.percentile(sat, alpha)
hi_sat = np.percentile(sat, 100 - alpha)
lo_val = np.percentile(val, alpha)
hi_val = np.percentile(val, 100 - alpha)
print "bounds = ([%i, %i, %i], [%i, %i, %i])" % (lo_hue, lo_sat, lo_val, hi_hue, hi_sat, hi_val)
