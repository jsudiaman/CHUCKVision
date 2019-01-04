# CHUCKVision
Vision-based state estimation for [CHUCK](https://github.com/cornhole) (a Cornhole playing robot).

- [Project Summary](/misc/Summary%202017-04-11.pdf)

## Dependencies
- Python 2.7
- [Pipenv](https://pipenv.readthedocs.io)

## Setup
```Shell
pipenv install
pipenv shell
```

## GUI
Command: `python gui.py [--detailed]`

The GUI goes through the dataset, drawing boundaries around key objects and displaying the score. The
score is colored with respect to which team is scoring (i.e. red text if red team is scoring, blue text if
blue team is scoring). Use the LEFT and RIGHT arrow keys to navigate the dataset, and ESC to exit the
program. If run with the `--detailed` option, the GUI will display individual contours in addition to the
boundaries.

**Sample Run**

<img src="/misc/gui_sample_run.png" alt="gui_sample_run" width="441" height="480">

## Acceptance Test
Command: `python acceptanceTest.py`

The acceptance test will generate CSV files which compare estimations to the actual values from
[dataSet.json](/dataset/dataSet.json).

| File             | Description                                                     |
|------------------|-----------------------------------------------------------------|
| pointCompare.csv | Fine-grained comparison which uses exact points and dimensions. |
| scoreCompare.csv | High level comparison which uses the score.                     |

## Tools

### hsvRange.py
Command: `python hsvRange.py --image IMAGE [--tolerance TOLERANCE]`

This tool analyzes the given image and returns bounds on the HSV values of its pixels. Useful for scanning
cropped objects to determine their respective HSV boundaries in
[stateEstimation.py](/stateEstimation.py).

| Argument  | Description                                                                                                                                                                                                                   |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| image     | Path to the image                                                                                                                                                                                                             |
| tolerance | Error tolerance (between 0 and 50). Specifically, this argument controls the *percentiles* of HSV values to include in the range. For instance, a tolerance of 5 will return HSV values between the 5th and 95th percentiles. |

**Sample Run**
```
$ python hsvRange.py --image dataset/img/cropped/board.png --tolerance 30
bounds = ([30, 2, 235], [120, 5, 238])
```
