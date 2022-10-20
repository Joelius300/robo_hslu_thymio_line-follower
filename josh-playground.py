import math
from thymio_utils import BUTTON_CENTER, MOTOR_LEFT, MOTOR_RIGHT, PROXIMITY_GROUND_DELTA, PROXIMITY_GROUND_REFLECTED, \
    SingleSerialThymioRunner, ThymioObserver, BUTTON_RIGHT, BUTTON_LEFT, LEDS_TOP, GROUND_SENSOR_RIGHT, \
    GROUND_SENSOR_LEFT


class LineFollower(ThymioObserver):
    def __init__(self):
        super().__init__()
        self.step = 0
        self.speed = 100
        self.temp_speed = None
        self.slow_speed = 75
        self.speed_step = 10
        self.min_darkness = 50
        self.max_darkness = 700
        self.curve_steps = 30
        self.curve = self.exponential_curve(self.curve_steps, abs(self.speed * 1.2), 20)
        self.slow_steps_remaining = -1
        print(self.curve)

    def exponential_curve(self, steps: int, stop: float, log_base: float):
        base = math.log(steps, log_base)
        points = [math.floor(stop / math.pow(base, i)) for i in range(steps)]
        points.reverse()
        return points

    def _update(self):
        self.step = self.step + 1
        self.rainbow(self.step)
        self.follow_the_darkness()
        self.handle_buttons()

    def set_lights(self, r, g, b):
        self.th[LEDS_TOP] = [r, g, b]

    def rainbow(self, step):
        step = step % (6 * 32)
        i = step % 32
        if step < 1 * 32:
            self.set_lights(31, i, 0)
        elif step < 2 * 32:
            self.set_lights(31 - i, 31, 0)
        elif step < 3 * 32:
            self.set_lights(0, 31, i)
        elif step < 4 * 32:
            self.set_lights(0, 31 - i, 31)
        elif step < 5 * 32:
            self.set_lights(i, 0, 31)
        elif step < 6 * 32:
            self.set_lights(31, 0, 31 - i)

    def handle_buttons(self):
        if self.th[BUTTON_CENTER]:
            print("done")
            self.th[MOTOR_LEFT] = 0
            self.th[MOTOR_RIGHT] = 0
            self.stop()
        if self.th[BUTTON_RIGHT]:
            self.speed = self.speed + self.speed_step
            print(self.speed)
        if self.th[BUTTON_LEFT]:
            self.speed = self.speed - self.speed_step
            print(self.speed)

    # WIP
    # works as intended but intended badly
    # I think mapping the numbers in a logarithmic way (or exponential idk) would make sense. That wiggle should be minimized
    def map_steer_to_speed_reduction(self, steer):
        steer = abs(steer)
        if steer > self.max_darkness:
            steer = self.max_darkness
        ratio = (self.curve_steps - 1) / (self.max_darkness - self.min_darkness)
        curve_index = math.floor(abs((steer - self.min_darkness) * ratio))
        return self.curve[curve_index]

    # WIP
    # THIS IS LITERALLY BORKEN MONKA
    def adjust_speed(self, slow_speed):
        if not self.temp_speed:
            self.temp_speed = self.speed
            self.speed = slow_speed
        self.slow_steps_remaining = self.slow_steps_remaining - 1
        if self.slow_steps_remaining <= 0:
            self.speed = self.temp_speed
            self.temp_speed = None
        return

    def follow_the_darkness(self):
        # steer towards darkness (== less reflextion), so positive = right, negative = left
        steer = self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT] - \
                self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT]

        new_speed_inner = self.speed - self.map_steer_to_speed_reduction(steer)

        # This cheap formula works
        # new_speed_inner = self.speed - abs(steer // 10)

        if new_speed_inner <= 0:
            self.slow_steps_remaining = 10

        if self.slow_steps_remaining >= 0:
            self.adjust_speed(self.slow_speed)

        if steer > self.min_darkness:
            self.th[MOTOR_RIGHT] = new_speed_inner
            self.th[MOTOR_LEFT] = self.speed
        else:
            self.th[MOTOR_LEFT] = new_speed_inner
            self.th[MOTOR_RIGHT] = self.speed


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA},
                                      observer,
                                      0.1)
    runner.run()
