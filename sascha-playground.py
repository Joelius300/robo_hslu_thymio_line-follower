# This file is part of thymiodirect.
# Copyright 2020 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,
# Miniature Mobile Robots group, Switzerland
# Author: Yves Piguet
#
# SPDX-License-Identifier: BSD-3-Clause

# Test of the communication with Thymio via serial port

from thymio_python.thymiodirect import Thymio
from thymio_python.thymiodirect.thymio_serial_ports import ThymioSerialPort
from thymio_utils import BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
    PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, ThymioObserver, print_thymio_functions_events, \
    SingleSerialThymioRunner
import sys
import os
import time

class LineFollower(ThymioObserver):

    def __init__(self):
        super().__init__()
        self.prox_prev = None

    def _update(self):

        reflection_difference = self.th[PROXIMITY_GROUND_REFLECTED][0] - self.th[PROXIMITY_GROUND_REFLECTED][1]

        if (reflection_difference > 0):
            right_speed = speed - (difference_reflection // 10)
            left_speed = speed
        else:
            right_speed = speed
            left_speed = speed + (difference_reflection // 10)


        if self.th[BUTTON_CENTER]:
            print("Center button pressed")
            self.stop()


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED,
                                       PROXIMITY_GROUND_DELTA, PROXIMITY_FRONT_BACK},
                                      observer)

    runner.run()