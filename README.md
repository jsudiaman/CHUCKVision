Cornhole Vision Dataset
=======================

This directory contains a dataset of bean bags on a black board.
There are individual images and a single JSON file providing annotation information according to the following format:

- _reference:   xxxx.jpg
- beanBags:
  - bounded_rectangle:
    - center: [x,y]
    - height: #
    - width: #
    - Color: red/blue
    - Location: on/off/in
  - board:
    - center: [x,y]
    - hole:
      - center: [x,y]
      - radius: #
    - size:
      - height: #
      - width: #

The images are numbered 0-X and correspond to values in the "xxxx".jpg file
