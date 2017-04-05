"""
Components for CHUCK state estimation.
"""
import math
from os.path import basename

import cv2
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
dy_from_board = 85


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
    red_rects = _draw_beanbags(image, red_mask, (0, 0, 255))

    # Find blue beanbags.
    blue_mask = cv2.inRange(hsv, np.array(blue_beanbags[0], dtype="uint8"), np.array(blue_beanbags[1], dtype="uint8"))
    blue_rects = _draw_beanbags(image, blue_mask, (255, 0, 0))

    # Find the board.
    board_mask = cv2.inRange(hsv, np.array(board[0], dtype="uint8"), np.array(board[1], dtype="uint8"))
    board_rect = _draw_board(image, board_mask)

    # Find the cornhole.
    circle_mask = cv2.inRange(hsv, np.array(cornhole[0], dtype="uint8"), np.array(cornhole[1], dtype="uint8"))
    cornhole_circ = _draw_cornhole(image, circle_mask, board_rect)

    # Prepare annotations, which should be one-to-one with dataSet.json.
    # Filename
    anns = {}
    anns['_reference'] = basename(filename)

    # Beanbags
    anns['beanBags'] = []
    for rect, color in [(r, 'red') for r in red_rects] + [(r, 'blue') for r in blue_rects]:
        _, _, w, h = rect
        beanbag = {
            'bounded_rectangle': {
                'center': _center(rect),
                'height': h,
                'width': w
            },
            'color': color,
            'location': None  # TODO
        }
        anns['beanBags'].append(beanbag)

    # Board
    cx, cy, cr = cornhole_circ
    _, _, bw, bh = board_rect
    anns['board'] = {
        'center': _center(board_rect),
        'hole': {
            'center': (cx, cy),
            'radius': cr
        },
        'size': {
            'height': bh,
            'width': bw
        }
    }

    # Return the image and its annotations.
    return image, anns


def _draw_beanbags(image, mask, color):
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


def _draw_board(image, mask):
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


def _draw_cornhole(image, mask, board_rect=None):
    """
    Draws the cornhole using color filtering.

    :param image: image to annotate
    :param mask: mask used to find contours
    :param board_rect: rectangular boundaries of the board
    :return: (x, y, r) where (x, y) is the center and r is the radius of the circle, or (0, 0, 0) if none found.
    """
    board_x, board_y, board_width, board_height = board_rect
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Discard contours outside the board
    if board_rect is not None:
        cs_in_board = []
        for c in contours:
            M = cv2.moments(c)
            if M["m00"] > 0:
                x = int(M["m10"] / M["m00"])
                y = int(M["m01"] / M["m00"])
                if board_x <= x <= board_x + board_width and board_y <= y <= board_y + board_height:
                    cs_in_board.append(c)
        contours = cs_in_board

    while len(contours) > 0:
        # Enclosing circle around the contours
        (x, y), r = cv2.minEnclosingCircle(np.concatenate(contours))
        x, y, r = int(x), int(y), int(r)

        # Ensure that circle is reasonably sized
        if not min_ch_radius <= r <= max_ch_radius:
            break

        # Circle looks good, so draw it
        cv2.circle(image, (x, y), r, (0, 255, 255), 4)
        return x, y, r

    # Fallback to Hough transform
    return _draw_cornhole2(image, board_rect)


def _draw_cornhole2(image, board_rect=None):
    """
    Draws the cornhole using circular Hough transform.

    :param image: image to annotate
    :param board_rect: rectangular boundaries of the board
    :return: (x, y, r) where (x, y) is the center and r is the radius of the circle, or (0, 0, 0) if none found.
    """
    # Do transformation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1.2, 100, param1=50, param2=30, minRadius=min_ch_radius, maxRadius=max_ch_radius)
    ch = (0, 0, 0)
    if circles is None:
        return ch
    circles = np.round(circles[0, :]).astype("int")

    # Find circle with lowest distance from the expected position
    lo_dist = float('inf')
    for (x, y, r) in circles:
        if board_rect is None:
            continue

        # Ensure that the hole is contained within the board
        bx, by, bw, bh = board_rect
        if not (bx <= x <= bx + bw and by <= y <= by + bh):
            continue

        # Find distance
        dist = math.sqrt((x - (bx + bw / 2)) ** 2 + ((y - (by + dy_from_board)) ** 2))
        if dist < lo_dist:
            lo_dist = dist
            ch = x, y, r

    # Return the cornhole
    x, y, r, = ch
    cv2.circle(image, (x, y), r, (0, 255, 255), 4)
    return ch


def _center(rect):
    """
    Calculate the center of a rectangle using the midpoint formula.

    :param rect: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the rectangle
    :return: (x, y) tuple where (x, y) is the center of the rectangle.
    """
    x, y, w, h = rect
    return (x + x + w) / 2, (y + y + h) / 2
