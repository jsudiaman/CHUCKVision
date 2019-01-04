"""
GUI for the stateEstimation module.

Usage: gui.py [--detailed] [--index INDEX]
"""
import argparse
import cv2

from stateEstimation import analyze, score

if __name__ == '__main__':
    # Initialization
    ap = argparse.ArgumentParser()
    ap.add_argument("-d", "--detailed",
                    action="store_true",
                    help="show the individual contours / Hough circles which form the boundaries")
    ap.add_argument("-i", "--index", default=0, help="image index to start with")
    args = ap.parse_args()
    index = int(args.index)
    total_imgs = 197

    # UI
    while index <= total_imgs:
        filename = "%04d.jpg" % index
        image, anns = analyze("dataset/img/" + filename, args.detailed)

        # Display filename.
        cv2.putText(image, filename, (0, 25), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        # Display score in the color of the scoring team.
        s = score(anns)
        if s > 0:
            s_color = (0, 0, 255)
        elif s < 0:
            s_color = (255, 0, 0)
        else:
            s_color = (255, 255, 255)
        cv2.putText(image, "Score: %d" % abs(s), (0, 715), cv2.FONT_HERSHEY_SIMPLEX, 1, s_color, 2, cv2.LINE_AA)

        # Show image.
        cv2.imshow("CHUCKVision", image)

        # J key = Go to previous image. L key = Go to next image. Escape key = Quit.
        key = cv2.waitKey(0)
        if key == 106:
            index = max(0, index - 1)
        elif key == 27:
            break
        elif key == 108:
            index += 1
