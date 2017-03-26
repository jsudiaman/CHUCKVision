"""
Use this to get HSV ranges for cropped images (e.g. a beanbag by itself)

Usage: python hsvRange.py --image image_file [--tolerance error_tolerance]
"""
import numpy as np
import argparse
import cv2

# Construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True, help="Path to the image")
ap.add_argument("-t", "--tolerance", default=5, help="Error tolerance [0, 50]")
args = vars(ap.parse_args())

# Print HSV bounds
image = cv2.imread(args['image'])
tol = int(args['tolerance'])
if not 0 <= tol <= 50:
    raise ValueError("Tolerance must be between 0 and 50.")
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
hue = [channels[0] for sublist in hsv for channels in sublist]
sat = [channels[1] for sublist in hsv for channels in sublist]
val = [channels[2] for sublist in hsv for channels in sublist]
lo_hue = np.percentile(hue, tol)
hi_hue = np.percentile(hue, 100 - tol)
lo_sat = np.percentile(sat, tol)
hi_sat = np.percentile(sat, 100 - tol)
lo_val = np.percentile(val, tol)
hi_val = np.percentile(val, 100 - tol)
print "bounds = ([%i, %i, %i], [%i, %i, %i])" % (lo_hue, lo_sat, lo_val, hi_hue, hi_sat, hi_val)
