"""Components for CHUCK state estimation."""
import cv2
import json
import traceback
import numpy as np

# HSV boundaries (Min, Max)
lower_red = ([0, 70, 50], [10, 255, 255])
upper_red = ([170, 70, 50], [180, 255, 255])
blue_beanbags = ([100, 120, 0], [140, 255, 255])
board = ([103, 31, 120], [105, 47, 135])

# Beanbag values
min_beanbag_area = 100

# Cornhole values
min_ch_radius = 30
max_ch_radius = 50


def annotate(filename):
    """
    Annotate an image file using color detection algorithm.

    :param filename: location of the source file
    :return: (image, red_rects, blue_rects, board_rect, cornhole)
    """
    # Load the image.
    image = cv2.imread(filename)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Find red beanbags.
    red1 = cv2.inRange(hsv, np.array(lower_red[0], dtype="uint8"), np.array(lower_red[1], dtype="uint8"))
    red2 = cv2.inRange(hsv, np.array(upper_red[0], dtype="uint8"), np.array(upper_red[1], dtype="uint8"))
    red_mask = cv2.bitwise_or(red1, red2)
    red_rects = draw_beanbags(image, red_mask, (0, 0, 255))

    # Find blue beanbags.
    blue_mask = cv2.inRange(hsv, np.array(blue_beanbags[0], dtype="uint8"), np.array(blue_beanbags[1], dtype="uint8"))
    blue_rects = draw_beanbags(image, blue_mask, (255, 0, 0))

    # Find the board.
    board_mask = cv2.inRange(hsv, np.array(board[0], dtype="uint8"), np.array(board[1], dtype="uint8"))
    board_rect = draw_board(image, board_mask)

    # Find the cornhole.
    cornhole = draw_cornhole(image, board_rect)

    # Return the image and its annotations.
    return image, red_rects, blue_rects, board_rect, cornhole


def draw_beanbags(image, mask, color):
    """
    Draws bounding boxes onto an image from a mask.

    :param image: image to annotate
    :param mask: mask used to find contours
    :param color: color of the bounding boxes (B,G,R)
    :return: List of (x, y, w, h) tuples where (x, y) is the left corner, w is the width, and h is the height of the rectangle.
    """
    rects = []
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_beanbag_area:
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            rects.append((x, y, w, h))
    return rects


def draw_board(image, mask):
    """
    Draws bounding box onto an image from a mask.

    :param image: image to annotate
    :param mask: mask used to find contour
    :return: (x, y, w, h) tuple where (x, y) is the left corner, w is the width, and h is the height of the rectangle.
    """
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    x, y, w, h = cv2.boundingRect(np.concatenate(contours))
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return x, y, w, h


def draw_cornhole(image, board_rect=None):
    """
    Draws the cornhole.

    :param image: image to annotate
    :param board_rect: rectangular boundaries of the board
    :return: (x, y, r) where (x, y) is the center and r is the radius of the circle.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1.2, 100, param1=50, param2=30,
                               minRadius=min_ch_radius, maxRadius=max_ch_radius)

    # Draw circles
    # TODO If more than one hole found in the board, which one is the true cornhole?
    if circles is None:
        return None
    circles = np.round(circles[0, :]).astype("int")
    for (x, y, r) in circles:
        # Ensure that the hole is contained within the board
        if board_rect is not None:
            board_x, board_y, board_width, board_height = board_rect
            if not (board_x <= x <= board_x + board_width and board_y <= y <= board_y + board_height):
                continue
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        return x, y, r


if __name__ == '__main__':
    # Settings
    index = 0
    total_imgs = 197

    # Dataset
    with open('dataset/dataSet.json') as data_file:
        dataset = json.load(data_file)

    # UI
    while index <= total_imgs:
        image, red_rects, blue_rects, board_rect, cornhole = annotate("dataset/img/%04d.jpg" % index)
        cv2.imshow("State Estimator", image)

        try:
            # Compare to data set
            data = dataset[index]
            error = lambda exp, real: float(abs(exp - real)) / real * 100

            # Board
            ds_board = data['board']
            expWidth, expHeight = board_rect[2], board_rect[3]
            realWidth, realHeight = ds_board['size']['width'], ds_board['size']['height']
            print "File: %04d.jpg" % index
            print "==== BOARD ===="
            print "Width: %d (Error: %d%%)" % (expWidth, error(expWidth, realWidth))
            print "Height: %d (Error: %d%%)" % (expHeight, error(expHeight, realHeight))

            # Cornhole
            ds_hole = data['board']['hole']
            expX, expY, expRadius = cornhole
            realX, realY, realRadius = ds_hole['center'][0], ds_hole['center'][1], ds_hole['radius']
            print "=== CORNHOLE ==="
            print "x: %d (Error: %d%%)" % (expX, error(expX, realX))
            print "y: %d (Error: %d%%)" % (expY, error(expY, realY))
            print "radius: %d (Error: %d%%)" % (expRadius, error(expRadius, realRadius))
        except:
            print "==== EXCEPTION ===="
            traceback.print_exc()
        finally:
            print ""

        # Left key = Go to previous image. Right key = Go to next image. Escape key = Quit.
        key = cv2.waitKey(0)
        if key == 63234 or key == 2424832:
            index = max(0, index - 1)
        elif key == 27:
            break
        elif key == 63235 or key == 2555904:
            index += 1
