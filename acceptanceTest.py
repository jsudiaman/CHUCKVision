"""
Generates CSV files which compare the stateEstimation module to the given dataSet.json.

pointCompare.csv: Fine-grained comparison which uses exact points and dimensions.
"""
import json

import math

from stateEstimation import analyze


def error(exp, real):
    """
    Calculate percent error of an experimental value.

    :param exp: experimental value
    :param real: precise value
    :return: Percent error err such that 0 <= err <= 100.
    """
    return float(abs(exp - real)) / abs(real) * 100


def closest_rect(rect, rects):
    """
    From a list of rectangles, get the rectangle closest to the one that is given.
    
    Rectangles are tuples in (centerX, centerY, width, height) format.

    :param rect: Single rectangle
    :param rects: List of rectangles
    :return: The closest rectangle to rect in rects
    """
    # Initialize.
    x1, y1, _, _ = rect
    min_dist = float('inf')
    closest = None

    # Find closest rectangle.
    for r in rects:
        x2, y2, _, _ = r
        dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest = r
    return closest


if __name__ == '__main__':
    total_imgs = 197

    # Compare dataSet to stateEstimation
    with open('dataset/dataSet.json') as dataset_file, open("pointCompare.csv", "w") as point:
        dataset = json.load(dataset_file)
        point_format = "%s,%s,%d,%d,%.1f"
        print >> point, "Reference,Value,Experimental,Actual,% Error"

        # Loop through data set
        for i in xrange(0, total_imgs + 1):
            ref = "%04d.jpg" % i
            _, exp = analyze("dataset/img/" + ref)
            real = dataset[i]

            # Beanbags
            real_beanbags = real['beanBags']
            exp_beanbags = exp['beanBags']
            for beanbag in exp_beanbags:
                # Get beanbag color
                color = beanbag['color']

                # Convert to rects
                real_rects = [b['bounded_rectangle'] for b in real_beanbags if b['color'] == color]
                real_rects = [(r['center'][0], r['center'][1], r['width'], r['height']) for r in real_rects]
                exp_rect = beanbag['bounded_rectangle']
                exp_rect = exp_rect['center'][0], exp_rect['center'][1], exp_rect['width'], exp_rect['height']

                # Make comparisons
                real_bbx, real_bby, real_bbw, real_bbh = closest_rect(exp_rect, real_rects)
                exp_bbx, exp_bby, exp_bbw, exp_bbh = exp_rect
                print >> point, point_format % (ref, "%s Beanbag X" % color.capitalize(), exp_bbx, real_bbx, error(exp_bbx, real_bbx))
                print >> point, point_format % (ref, "%s Beanbag Y" % color.capitalize(), exp_bby, real_bby, error(exp_bby, real_bby))
                print >> point, point_format % (ref, "%s Beanbag Height" % color.capitalize(), exp_bbh, real_bbh, error(exp_bbh, real_bbh))
                print >> point, point_format % (ref, "%s Beanbag Width" % color.capitalize(), exp_bbw, real_bbw, error(exp_bbw, real_bbw))

            # Board
            real_board = real['board']
            exp_board = exp['board']
            real_bx, real_by = real['board']['center']
            exp_bx, exp_by = exp['board']['center']
            real_bw, real_bh = real_board['size']['width'], real_board['size']['height']
            exp_bw, exp_bh = exp_board['size']['width'], exp_board['size']['height']
            print >> point, point_format % (ref, "Board X", exp_bx, real_bx, error(exp_bx, real_bx))
            print >> point, point_format % (ref, "Board Y", exp_by, real_by, error(exp_by, real_by))
            print >> point, point_format % (ref, "Board Height", exp_bh, real_bh, error(exp_bh, real_bh))
            print >> point, point_format % (ref, "Board Width", exp_bw, real_bw, error(exp_bw, real_bw))

            # Cornhole
            if 'hole' in real_board:
                real_ch = real_board['hole']
                exp_ch = exp_board['hole']
                (real_chx, real_chy), real_chr = real_ch['center'], real_ch['radius']
                (exp_chx, exp_chy), exp_chr = exp_ch['center'], exp_ch['radius']
                if exp_chr > 0:
                    print >> point, point_format % (ref, "Cornhole X", exp_chx, real_chx, error(exp_chx, real_chx))
                    print >> point, point_format % (ref, "Cornhole Y", exp_chy, real_chy, error(exp_chy, real_chy))
                    print >> point, point_format % (ref, "Cornhole Radius", exp_chr, real_chr, error(exp_chr, real_chr))
