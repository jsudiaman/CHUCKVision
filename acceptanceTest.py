"""
Generates a CSV file which compares the stateEstimation module to the given dataSet.json.
"""
import json

from stateEstimation import analyze


def error(exp, real):
    """
    Calculate percent error of an experimental value.

    :param exp: experimental value
    :param real: precise value
    :return: Percent error err such that 0 <= err <= 100.
    """
    return float(abs(exp - real)) / abs(real) * 100


if __name__ == '__main__':
    index = 0
    total_imgs = 197

    # Compare dataSet to stateEstimation
    with open('dataset/dataSet.json') as dataset_file, open("stateEstimation.csv", "w") as csv:
        dataset = json.load(dataset_file)
        print >> csv, "Reference,Value,Experimental,Actual,% Error"

        # Loop through data set
        while index <= total_imgs:
            _, exp = analyze("dataset/img/%04d.jpg" % index)

            # Board
            real = dataset[index]
            real_board = real['board']
            exp_board = exp['board']
            real_bx, real_by = real['board']['center']
            exp_bx, exp_by = exp['board']['center']
            real_bw, real_bh = real_board['size']['width'], real_board['size']['height']
            exp_bw, exp_bh = exp_board['size']['width'], exp_board['size']['height']
            print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Board X", exp_bx, real_bx, error(exp_bx, real_bx))
            print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Board Y", exp_by, real_by, error(exp_by, real_by))
            print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Board Width", exp_bw, real_bw, error(exp_bw, real_bw))
            print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Board Height", exp_bh, real_bh, error(exp_bh, real_bh))

            # Cornhole
            if 'hole' in real_board:
                real_ch = real_board['hole']
                exp_ch = exp_board['hole']
                (real_chx, real_chy), real_chr = real_ch['center'], real_ch['radius']
                (exp_chx, exp_chy), exp_chr = exp_ch['center'], exp_ch['radius']
                if exp_chr > 0:
                    print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Cornhole X", exp_chx, real_chx, error(exp_chx, real_chx))
                    print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Cornhole Y", exp_chy, real_chy, error(exp_chy, real_chy))
                    print >> csv, "%s,%s,%d,%d,%.1f" % ("%04d.jpg" % index, "Cornhole Radius", exp_chr, real_chr, error(exp_chr, real_chr))

            # TODO Beanbags
            index += 1
