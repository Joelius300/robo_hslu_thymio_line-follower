import math
from typing import Literal

import numpy as np

from thymio_python.thymiodirect import ThymioObserver, SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_GROUND_REFLECTED, \
    PROXIMITY_GROUND_DELTA, GROUND_SENSOR_LEFT, GROUND_SENSOR_RIGHT, BUTTON_CENTER, MOTOR_LEFT, MOTOR_RIGHT


def clamp(num, min_value, max_value):
    num = max(min(num, max_value), min_value)
    return num


class LineFollower(ThymioObserver):
    """
    The idea was as follows:
    Store left and right speed in class. On each step, compare the darkness of the left and the right sensor.
    Use a power function on that difference to determine the ratio (hardness) of the turn that the robot should
    take (meaning small deltas give very small adjustments and only larger deltas yield big adjustments).
    The average of both current speeds is taken and multiplied by the turn ratio (hardness) yielding the absolute
    adjustment necessary. Half of this absolute adjustment is then subtracted from the inner wheel and
    half of it is added to the outer wheel speed (inner slows down, outer speeds up).
    If the difference in sensor darkness is below a certain threshold (percentage of max difference), then both sensors
    are sped up by a set percentage unless one of them is at max speed (to stay on the current curve).
    I also tried to implement a moving average to make it more resilient to outliers but because of negative and positive
    values that requires some more thinking.
    Unfortunately it still oversteers quite hard, leading me to question if the power function is the right tool for it.
    Even with a lot of playing around, I was not able to get consistent results with the approach as of this commit.

    Some ideas:
    - Use other function than power function for first transformation step
    - Know on what kind of curve you are currently (for.. something?)
    - Implement the rolling average again but make it sensible to the curve you're on -> figure out the +- issue
    """

    def __init__(self):
        super().__init__()
        self.left_speed = 200
        self.right_speed = 200
        self.min_darkness = 50
        self.max_darkness = 650
        self.min_speed = 10
        self.max_speed = 500
        moving_average_length = 3
        self.last_averaged_steer = 0
        self.last_steers = np.zeros(moving_average_length, dtype=int)
        weights = np.arange(moving_average_length + 1, 1, -1)
        self.last_steers_weights = weights / weights.sum()
        print(self.last_steers_weights)

        # self.curve = self.speed_reduction_curve(type='pow', strength=7, max_reduction=.4)
        self.curve = self.speed_reduction_curve(type='pow', strength=3, max_reduction=.1)
        # self.curve = self.speed_reduction_curve(type='exp', strength='e', max_reduction=.025)
        # self.curve = self.speed_reduction_curve(type='pow', strength=4, max_reduction=.50)
        print(self.curve)

    @staticmethod
    def speed_reduction_curve(type: Literal['exp', 'pow'], strength: float | Literal['e'], max_reduction,
                              steps=200):
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

        self.last_steers[1:] = self.last_steers[:-1]
        self.last_steers[0] = steer
        steer = np.average(self.last_steers, weights=self.last_steers_weights)
        print(f"Steers: {self.last_steers} -> steer: {steer}")

        # if steer is closer to 0 than self.last_averaged_steer: do nothing
        if abs(steer) <= abs(self.last_averaged_steer):
            print("More on track than before, don't adjust.")
            return

        self.last_averaged_steer = steer

        max_reflection_diff = self.max_darkness - self.min_darkness
        if abs(steer) <= max_reflection_diff * 0.1:
            if self.left_speed == self.max_speed or self.right_speed == self.max_speed:
                # retain ratio
                return

            print(f"Steer {steer} -> 1% speedup")
            self.left_speed = round(self.left_speed * 1.01)
            self.right_speed = round(self.right_speed * 1.01)
        else:
            speed_reduction_percent = self.map_steer_to_speed_reduction(steer)
            inner_speed, outer_speed = (self.left_speed, self.right_speed) if steer < 0 else (
                self.right_speed, self.left_speed)

            # curve_ratio = inner_speed / outer_speed  # smaller when the curve is harder -> decrease speed adjustment in hard curve

            # print(f"Steer {steer} -> {speed_reduction_percent:%} * {curve_ratio:%} (= {speed_reduction_percent * curve_ratio:%}) (-inner, +outer)")
            print(f"Steer {steer} -> {speed_reduction_percent:%} (-inner, +outer)")

            # avg_speed = (inner_speed + outer_speed) / 2
            # speed_reduction = math.floor(avg_speed * speed_reduction_percent / 2 * curve_ratio)
            # print(f"Steer {steer} -> {speed_reduction} (-inner, +outer)")
            #
            # inner_speed -= speed_reduction  # - int(speed_reduction / 2)  # slow inner
            # outer_speed += speed_reduction  # + int(speed_reduction / 2)  # speed up outer

            # inner_speed = round(inner_speed * (1 - speed_reduction_percent * curve_ratio))
            # outer_speed = round(outer_speed * (1 + speed_reduction_percent * curve_ratio))

            inner_speed = math.ceil(inner_speed * (1 - speed_reduction_percent))
            outer_speed = math.ceil(outer_speed * (1 + speed_reduction_percent))

            # overshot = max(0, self.min_speed - inner_speed)  # stores the speed the reduction overshot the min_speed by
            # if overshot > 0:
            #     print(f"Adding overshot {overshot} because inner too slow")
            #     outer_speed += overshot
            #
            # overshot = min(0, self.max_speed - outer_speed)  # stores the speed the increase overshot the max_speed by (negative)
            # if overshot < 0:
            #     print(f"Adding overshot {overshot} because outer too fast")
            #     inner_speed += overshot

            self.left_speed, self.right_speed = (inner_speed, outer_speed) if steer < 0 else (outer_speed, inner_speed)

        self.left_speed = clamp(self.left_speed, self.min_speed, self.max_speed)
        self.right_speed = clamp(self.right_speed, self.min_speed, self.max_speed)

        print(f"Left: {self.left_speed}; Right: {self.right_speed}")
        self.th[MOTOR_LEFT] = self.left_speed
        self.th[MOTOR_RIGHT] = self.right_speed


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA},
                                      observer,
                                      1 / 10)
    runner.run()
