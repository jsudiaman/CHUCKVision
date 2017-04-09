"""
GUI for the stateEstimation module.

Usage: gui.py [--detailed]
"""
import argparse
import cv2

from stateEstimation import analyze

if __name__ == '__main__':
    # Initialization
    index = 0
    total_imgs = 197
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--detailed",
                    action="store_true",
                    help="show the individual contours / Hough circles which form the boundaries")
    args = ap.parse_args()

    # UI
    while index <= total_imgs:
        filename = "%04d.jpg" % index
        image, anns = analyze("dataset/img/" + filename, args.detailed)
        cv2.putText(image, filename, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.CV_AA)
        cv2.imshow("CHUCKVision", image)

        # Left key = Go to previous image. Right key = Go to next image. Escape key = Quit.
        key = cv2.waitKey(0)
        if key == 63234 or key == 2424832:
            index = max(0, index - 1)
        elif key == 27:
            break
        elif key == 63235 or key == 2555904:
            index += 1
