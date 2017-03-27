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
cornhole = ([21, 38, 96], [29, 58, 142])

# Beanbag values
min_beanbag_area = 100

# Cornhole values
min_ch_radius = 30
max_ch_radius = 50


def analyze(filename):
    """
    Scan the source image for beanbags, board, and cornhole. Detected objects are annotated using rectangles or circles.

    :param filename: location of the source file
    :return: (image, red_rects, blue_rects, board_rect, cornhole_circ)
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
    circle_mask = cv2.inRange(hsv, np.array(cornhole[0], dtype="uint8"), np.array(cornhole[1], dtype="uint8"))
    cornhole_circ = draw_cornhole2(image, board_rect)

    # Return the image and its annotations.
    # TODO Possibly return (image, jsonObject) instead
    return image, red_rects, blue_rects, board_rect, cornhole_circ


def draw_beanbags(image, mask, color):
    """
    Draws bounding boxes around beanbags.

    :param image: image to annotate
    :param mask: mask used to find contours
    :param color: color of the bounding boxes (B,G,R)
    :return: List of (x, y, w, h) tuples where (x, y) is the top-left corner, w is the width, and h is the height of each rectangle.
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
    Draws bounding box around the board.

    :param image: image to annotate
    :param mask: mask used to find contours
    :return: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the rectangle.
    """
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None
    x, y, w, h = cv2.boundingRect(np.concatenate(contours))
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return x, y, w, h


# def draw_cornhole(image, mask, board_rect=None):
#     """
#     Draws the cornhole using color filtering.
#
#     :param image: image to annotate
#     :param mask: mask used to find contours
#     :param board_rect: rectangular boundaries of the board
#     :return: (x, y, r) where (x, y) is the center and r is the radius of the circle.
#     """
#     board_x, board_y, board_width, board_height = board_rect
#     contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # Discard contours outside the board
#     if board_rect is not None:
#         cs_in_board = []
#         for c in contours:
#             M = cv2.moments(c)
#             if M["m00"] > 0:
#                 x = int(M["m10"] / M["m00"])
#                 y = int(M["m01"] / M["m00"])
#                 if board_x <= x <= board_x + board_width and board_y <= y <= board_y + board_height:
#                     cs_in_board.append(c)
#         contours = cs_in_board
#
#     while len(contours) > 0:
#         # Enclosing circle around the contours
#         (x, y), r = cv2.minEnclosingCircle(np.concatenate(contours))
#         x, y, r = int(x), int(y), int(r)
#
#         # Ensure that circle is reasonably sized
#         if not min_ch_radius <= r <= max_ch_radius:
#             break
#
#         # Circle looks good, so draw it
#         cv2.circle(image, (x, y), r, (0, 255, 255), 4)
#         return x, y, r
#
#     # Fallback to Hough transform
#     return draw_cornhole2(image, board_rect)


def draw_cornhole2(image, board_rect=None):
    """
    Draws the cornhole using circular Hough transform.

    :param image: image to annotate
    :param board_rect: rectangular boundaries of the board
    :return: (x, y, r) where (x, y) is the center and r is the radius of the circle.
    """
    # Do transformation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1.2, 100, param1=50, param2=30, minRadius=min_ch_radius,
                               maxRadius=max_ch_radius)
    if circles is None:
        return None
    circles = np.round(circles[0, :]).astype("int")

    # TODO If more than one hole is found in the board, which one is the true cornhole?
    # (Insert Highlander reference here)
    for (x, y, r) in circles:
        # Ensure that the hole is contained within the board
        if board_rect is not None:
            bx, by, bw, bh = board_rect
            if not (bx <= x <= bx + bw and by <= y <= by + bh):
                continue

        # Draw circle
        cv2.circle(image, (x, y), r, (0, 255, 255), 4)
    return 0, 0, 0  # TODO This is a placeholder


def center(rect):
    """
    Calculate the center of a rectangle using the midpoint formula.

    :param rect: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the rectangle
    :return: (x, y) tuple where (x, y) is the center of the rectangle.
    """
    x, y, w, h = rect
    return float(x + x + w) / 2, float(y + y + h) / 2


def error(exp, real):
    """
    Calculate percent error of an experimental value.

    :param exp: experimental value
    :param real: precise value
    :return: Percent error err such that 0 <= err <= 100.
    """
    return float(abs(exp - real)) / abs(real) * 100


if __name__ == '__main__':
    # Settings
    index = 0
    total_imgs = 197

    # Dataset
    with open('dataset/dataSet.json') as data_file:
        dataset = json.load(data_file)

    # UI
    while index <= total_imgs:
        image, red_rects, blue_rects, board_rect, cornhole_circ = analyze("dataset/img/%04d.jpg" % index)
        cv2.imshow("State Estimator", image)

        # Note: This is somewhat experimental
        try:
            # Compare to data set
            data = dataset[index]

            # Board
            ds_board = data['board']
            exp_board_x, exp_board_y = center(board_rect)
            real_board_x, real_board_y = ds_board['center']
            exp_board_width, exp_board_height = board_rect[2], board_rect[3]
            real_board_width, real_board_height = ds_board['size']['width'], ds_board['size']['height']
            print "File: %04d.jpg" % index
            print "==== BOARD ===="
            print "x: %d (Error: %d%%)" % (exp_board_x, error(exp_board_x, real_board_x))
            print "y: %d (Error: %d%%)" % (exp_board_x, error(exp_board_y, real_board_y))
            print "Width: %d (Error: %d%%)" % (exp_board_width, error(exp_board_width, real_board_width))
            print "Height: %d (Error: %d%%)" % (exp_board_height, error(exp_board_height, real_board_height))

            # Cornhole
            ds_hole = data['board']['hole']
            exp_ch_x, exp_ch_y, exp_radius = cornhole_circ
            real_ch_x, real_ch_y, real_radius = ds_hole['center'][0], ds_hole['center'][1], ds_hole['radius']
            print "=== CORNHOLE ==="
            print "x: %d (Error: %d%%)" % (exp_ch_x, error(exp_ch_x, real_ch_x))
            print "y: %d (Error: %d%%)" % (exp_ch_y, error(exp_ch_y, real_ch_y))
            print "radius: %d (Error: %d%%)" % (exp_radius, error(exp_radius, real_radius))
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
