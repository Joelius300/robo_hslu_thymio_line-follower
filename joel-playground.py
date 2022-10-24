import math
from typing import Literal

from thymio_utils import BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
    PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, ThymioObserver, print_thymio_functions_events, \
    SingleSerialThymioRunner, BUTTON_RIGHT, BUTTON_LEFT, GROUND_SENSOR_LEFT, GROUND_SENSOR_RIGHT
import numpy as np


class HandAvoider(ThymioObserver):

    def __init__(self):
        super().__init__()
        self.prox_prev = None

    def _update(self):
        prox = (self.th[PROXIMITY_FRONT_BACK][5] - self.th[PROXIMITY_FRONT_BACK][2]) // 10
        print(self.th[PROXIMITY_GROUND_AMBIENT])

        if prox != self.prox_prev:
            self.th[MOTOR_LEFT] = prox
            self.th[MOTOR_RIGHT] = prox
            print(prox)
            if prox > 5:
                self.th["leds.top"] = [0, 32, 0]
            elif prox < -5:
                self.th["leds.top"] = [32, 32, 0]
            elif abs(prox) < 3:
                self.th["leds.top"] = [0, 0, 32]
            self.prox_prev = prox
        if self.th[BUTTON_CENTER]:
            print("Center button pressed")
            self.stop()


class LineFollower(ThymioObserver):
    def __init__(self):
        super().__init__()
        self.left_speed = 200
        self.right_speed = 200
        self.speed_step = 20
        self.min_darkness = 50
        self.max_darkness = 700
        self.min_speed = 0
        self.max_speed = 500
        self.curve = self.speed_reduction_curve(type='pow', strength=2.5)
        print(self.curve)

    @staticmethod
    def speed_reduction_curve(type: Literal['exp', 'pow'], strength: float | Literal['e'], max_reduction=.75, steps=1000):
        x = np.linspace(0, 1, steps)
        if strength == 'e':
            strength = np.e
        if type == 'exp':
            y = (strength ** x) - 1
        else:
            y = x ** strength
        return (y / y.max()) * max_reduction

    def _update(self):
        self.follow_the_darkness()
        self.handle_buttons()

    def handle_buttons(self):
        if self.th[BUTTON_CENTER]:
            print("done")
            self.th[MOTOR_LEFT] = 0
            self.th[MOTOR_RIGHT] = 0
            self.stop()

    def map_steer_to_speed_reduction(self, steer: int) -> float:
        """
        Returns a value between 0 and 1 indicating the speed reduction percentage for the inner wheel (left if steer
        is negative, right if positive).
        """
        max_reflection_diff = self.max_darkness - self.min_darkness
        steer = min(abs(steer), max_reflection_diff)
        curve_index = math.floor(steer / max_reflection_diff * (len(self.curve) - 1))
        return self.curve.item(curve_index)

    def follow_the_darkness(self):
        # steer towards darkness (== less reflexion), so positive = right, negative = left
        steer = self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT] - \
                self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT]

        speed_reduction = self.map_steer_to_speed_reduction(steer)
        inner_speed, outer_speed = (self.left_speed, self.right_speed) if steer < 0 else (self.right_speed, self.left_speed)

        new_speed_inner = inner_speed * (1 - speed_reduction)  # slow inner
        overshot = max(0, self.min_speed - inner_speed)  # stores the speed the reduction overshot the min_speed by
        new_speed_inner = round(max(new_speed_inner, self.min_speed))  # clamp to min speed if overshot

        new_speed_outer = outer_speed * (1 + (speed_reduction / 2)) + (overshot / 2)  # speed up outer
        new_speed_outer = round(max(new_speed_outer, self.min_speed))  # clamp to max speed if overshot

        # LMAO this actually works pretty good but this never updates the left and right speed so it just always takes 200 and adjust those from there..
        if steer > 0:
            print(f"Left: {new_speed_inner}; Right: {new_speed_outer}")
            self.th[MOTOR_RIGHT] = new_speed_inner
            self.th[MOTOR_LEFT] = new_speed_outer
        else:
            print(f"Left: {new_speed_outer}; Right: {new_speed_inner}")
            self.th[MOTOR_RIGHT] = new_speed_outer
            self.th[MOTOR_LEFT] = new_speed_inner


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA},
                                      observer,
                                      1 / 15)
    runner.run()
