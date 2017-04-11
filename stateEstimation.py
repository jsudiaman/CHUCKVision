"""
Components for CHUCK state estimation.
"""
from math import sqrt
from os.path import basename

import cv2
import numpy as np

# HSV boundaries (Min, Max)
lower_red = ([0, 70, 50], [10, 255, 255])
upper_red = ([170, 70, 50], [180, 255, 255])
blue_beanbags = ([100, 120, 0], [140, 255, 255])
board = ([30, 2, 235], [120, 5, 238])

# Board values
board_u_margin = 0
board_r_margin = 50
board_d_margin = 0
board_l_margin = 0

# Beanbag values
min_beanbag_area = 100
max_beanbag_width = 109
max_beanbag_height = 109

# Cornhole values
min_ch_radius = 30
max_ch_radius = 50
dy_from_board = 85


def analyze(filename, detailed=False):
    """
    Scan the source image for beanbags, board, and cornhole. Detected objects are annotated using rectangles or circles.

    :param filename: location of the source file
    :param detailed: if true, show the individual contours / Hough circles which form the boundaries
    :return: (image, anns): the image and its annotations
    """
    # Load the image.
    image = cv2.imread(filename)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Find red beanbags.
    red1 = cv2.inRange(hsv, np.array(lower_red[0], dtype="uint8"), np.array(lower_red[1], dtype="uint8"))
    red2 = cv2.inRange(hsv, np.array(upper_red[0], dtype="uint8"), np.array(upper_red[1], dtype="uint8"))
    red_mask = cv2.bitwise_or(red1, red2)
    red_rects = _draw_beanbags(image, red_mask, (0, 0, 255), detailed)

    # Find blue beanbags.
    blue_mask = cv2.inRange(hsv, np.array(blue_beanbags[0], dtype="uint8"), np.array(blue_beanbags[1], dtype="uint8"))
    blue_rects = _draw_beanbags(image, blue_mask, (255, 0, 0), detailed)

    # Find the board.
    board_mask = cv2.inRange(hsv, np.array(board[0], dtype="uint8"), np.array(board[1], dtype="uint8"))
    board_rect = _draw_board(image, board_mask, detailed)

    # Find the cornhole.
    cornhole_circ = _draw_cornhole(image, detailed, board_rect)

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
            'location': _location(rect, board_rect, cornhole_circ)
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


def _draw_beanbags(image, mask, color, show_contours):
    """
    Draws bounding boxes around beanbags.

    :param image: image to annotate
    :param mask: mask used to find contours
    :param color: color of the bounding boxes (B,G,R)
    :param show_contours: if true, show the individual contours which form the bounding boxes
    :return: List of (x, y, w, h) tuples where (x, y) is the top-left corner, w is the width, and h is the height of each rectangle.
    """
    rects = []
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w * h >= min_beanbag_area:
            if show_contours:
                cv2.drawContours(image, c, -1, color, 4)

            # Beanbag is too big, split it
            # w ~ 95 h ~ 95
            # there are a few examples of a bean bag being larger than 106 (x2), along with two+ being smaller (x8)
            if w > max_beanbag_width:
                if h > w:
                    half_h = h / 2
                    cv2.rectangle(image, (x, y), (x + w, y + half_h), color, 2)
                    rects.append((x, y, w, half_h))
                    cv2.rectangle(image, (x, y), (x + w, y + half_h + half_h), color, 2)
                    rects.append((x, y + half_h, w, half_h))
                else:
                    half_w = w / 2
                    cv2.rectangle(image, (x, y), (x + half_w, y + h), color, 2)
                    rects.append((x, y, half_w, h))
                    cv2.rectangle(image, (x, y), (x + half_w + half_w, y + h), color, 2)
                    rects.append((x + half_w, y, half_w, h))
            elif h > max_beanbag_height:
                half_h = h / 2
                cv2.rectangle(image, (x, y), (x + w, y + half_h), color, 2)
                rects.append((x, y, w, half_h))
                cv2.rectangle(image, (x, y), (x + w, y + half_h + half_h), color, 2)
                rects.append((x, y + half_h, w, half_h))

            # Beanbag is not too big
            else:
                cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
                rects.append((x, y, w, h))
    return rects


def _draw_board(image, mask, show_contours):
    """
    Draws bounding box around the board.

    :param image: image to annotate
    :param mask: mask used to find contours
    :param show_contours: if true, show the individual contours which form the bounding box
    :return: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the rectangle.
    """
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Discard contours outside the margins
    board_cs = []
    height, width = image.shape[:2]
    for c in contours:
        M = cv2.moments(c)
        if M["m00"] > 0:
            x = int(M["m10"] / M["m00"])
            y = int(M["m01"] / M["m00"])
            if board_l_margin <= x <= width - board_r_margin and board_u_margin <= y <= height - board_d_margin:
                board_cs.append(c)
    contours = board_cs

    # Bounding box around the contours
    if len(contours) == 0:
        return None
    if show_contours:
        cv2.drawContours(image, contours, -1, (0, 255, 0), 4)
    x, y, w, h = cv2.boundingRect(np.concatenate(contours))
    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return x, y, w, h


def _draw_cornhole(image, show_all, board_rect=None):
    """
    Draws the cornhole using circular Hough transform.

    :param image: image to annotate
    :param show_all: if true, show all circles found by the transform. Extra circles will be drawn differently from the cornhole
    :param board_rect: rectangular boundaries of the board
    :return: (x, y, r) where (x, y) is the center and r is the radius of the circle, or (0, 0, 0) if none found.
    """
    # Do transformation
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.cv.CV_HOUGH_GRADIENT, 1.2, 100, None, 50, 30, min_ch_radius, max_ch_radius)
    ch = (0, 0, 0)
    if circles is None:
        return ch
    circles = np.round(circles[0, :]).astype("int")

    # Find circle with lowest distance from the expected position
    lo_dist = float('inf')
    for (x, y, r) in circles:
        if show_all:
            cv2.circle(image, (x, y), r, (0, 255, 255), 1)

        # If no board to reference, find the one closest to the top-middle of the entire image
        if board_rect is None:
            height, width = image.shape[:2]
            dist = sqrt((x - width / 2) ** 2 + (y - 0) ** 2)
        else:
            # Ensure that the hole is contained within the board
            bx, by, bw, bh = board_rect
            if not (bx <= x <= bx + bw and by <= y <= by + bh):
                continue

            # Find distance
            dist = sqrt((x - (bx + bw / 2)) ** 2 + ((y - (by + dy_from_board)) ** 2))
        if dist < lo_dist:
            lo_dist = dist
            ch = x, y, r

    # Return the cornhole
    x, y, r = ch
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


def _location(beanbag, board_rect, cornhole_circ):
    """
    Determine the location of a beanbag.
    
    :param beanbag: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the beanbag
    :param board_rect: (x, y, w, h) tuple where (x, y) is the top-left corner, w is the width, and h is the height of the board
    :param cornhole_circ: (x, y, r) where (x, y) is the center and r is the radius of the cornhole
    :return: "in" if the beanbag is in the cornhole (3 points), "on" if it is on the board (1 point), or "off" if it is 
    """
    # If missing board or cornhole, we can't determine the location.
    if board_rect is None:
        return None
    elif cornhole_circ is None:
        return None

    # Determine the location.
    mid_x, mid_y = _center(beanbag)
    bx, by, bw, bh = board_rect
    cx, cy, cr = cornhole_circ

    if bx < mid_x < bx + bw and by < mid_y < by + bh:
        if cx + cr > mid_x and cy + cr > mid_y and cx - cr < mid_x and cy - cr < mid_y:
            return "in"
        return "on"
    return "off"


def score(anns):
    """
    From a set of annotations (produced by stateEstimation or dataSet.json), get the score using cancellation scoring.

    :param anns: Annotations for a single image 
    :return: The score (> 0 if red is scoring, < 0 if blue is scoring, 0 if neither are scoring).
    """
    s = 0
    beanbags = anns['beanBags']
    for b in beanbags:
        color = b['color']
        location = b['location']
        if location == 'in':
            s += 3 if color == 'red' else -3
        elif location == 'on':
            s += 1 if color == 'red' else -1
    return s
