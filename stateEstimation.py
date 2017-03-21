"""
Components for CHUCK state estimation.
"""
import numpy as np
import cv2


def color_and_contours(filename):
    """
    Detects colors and contours.

    :param filename: Source file
    :return: Matrix
    """
    # Define the boundaries (Min BGR, Max BGR).
    red_beanbags = ([23, 15, 74], [95, 72, 235])
    blue_beanbags = ([101, 58, 44], [204, 135, 95])
    boundaries_list = [
        red_beanbags,
        # blue_beanbags
    ]

    # Load the image.
    image = cv2.imread(filename)
    output = None

    for boundaries in boundaries_list:
        # Create NumPy arrays from the boundaries.
        lower, upper = boundaries
        lower = np.array(lower, dtype="uint8")
        upper = np.array(upper, dtype="uint8")

        # Find the colors within the specified boundaries and apply the mask.
        mask = cv2.inRange(image, lower, upper)
        result = cv2.bitwise_and(image, image, mask=mask)
        output = result if output is None else cv2.bitwise_or(output, result)

    # Find contours.
    imgray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(imgray, 235, 255, 0)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(image, contours, -1, (0, 255, 0), 3)

    # Return the matrix.
    return np.hstack([image, output])


if __name__ == '__main__':
    # Settings
    index = 0
    total_imgs = 197
    detect = color_and_contours

    # UI
    while index <= total_imgs:
        cv2.imshow("Dataset", detect("dataset/img/%04d.jpg" % index))

        # Left key = Go to previous image. Right key = Go to next image. Escape key = Quit.
        key = cv2.waitKey(0)
        if key == 63234:
            index = max(0, index - 1)
        elif key == 27:
            break
        elif key == 63235:
            index += 1
