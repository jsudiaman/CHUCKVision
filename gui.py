"""
GUI for the stateEstimation module.
"""
import cv2

from stateEstimation import analyze

if __name__ == '__main__':
    index = 0
    total_imgs = 197

    # UI
    while index <= total_imgs:
        image, anns = analyze("dataset/img/%04d.jpg" % index)
        cv2.imshow("State Estimator", image)

        # Left key = Go to previous image. Right key = Go to next image. Escape key = Quit.
        key = cv2.waitKey(0)
        if key == 63234 or key == 2424832:
            index = max(0, index - 1)
        elif key == 27:
            break
        elif key == 63235 or key == 2555904:
            index += 1
