import math

from thymio_python.thymiodirect import SingleSerialThymioRunner, ThymioObserver
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
    GROUND_SENSOR_LEFT, \
    GROUND_SENSOR_RIGHT, BUTTON_CENTER, BUTTON_FRONT, BUTTON_BACK, MOTOR_LEFT, MOTOR_RIGHT, \
    LEDS_TOP


class LineFollower(ThymioObserver):
    def __init__(self):
        super().__init__()
        self.step = 0
        self.original_speed = 250
        self.speed = None
        self.slow_speed = 150
        self.speed_step = 10
        self.min_darkness = 80
        self.max_darkness = 400
        self.curve_steps = 30
        self.original_curve = self.exponential_curve(self.curve_steps, abs(self.original_speed * 1.1), 20)
        print(self.original_curve)
        self.curve = self.original_curve
        self.slow_steps_to_make = 10
        self.slow_steps_remaining = -1
        self.set_speed(self.original_speed)
        self.steer_history = [0] * 5
        self.weights = [25, 15, 5, 5, 2]

    def exponential_curve(self, steps: int, stop: float, log_base: float):
        base = math.log(steps, log_base)
        points = [math.floor(stop / math.pow(base, i)) for i in range(steps)]
        points.reverse()
        return points

    def set_speed(self, new_speed):
        ratio = new_speed / self.original_speed
        self.speed = math.floor(new_speed)
        self.curve = [math.floor(x * ratio) for x in self.original_curve]
        return

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
        if self.th[BUTTON_FRONT]:
            self.original_speed = self.original_speed + self.speed_step
            self.set_speed(self.original_speed)
        if self.th[BUTTON_BACK]:
            self.original_speed = self.original_speed - self.speed_step
            self.set_speed(self.original_speed)

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

    def add_steer_to_history(self, steer):
        for i in range(len(self.steer_history) - 1, 0, -1):
            self.steer_history[i] = self.steer_history[i - 1]
        self.steer_history[0] = steer
    
    def get_weighted_steer_average(self):
        total = 0
        for i in range(len(self.weights)):
            total = total + self.steer_history[i] * self.weights[i]
        avg = total / sum(self.weights)
        # print(self.steer_history)
        # print('total', total)
        # print('avg  ', avg)
        # print()
        return avg

    def follow_the_darkness(self):
        # steer towards darkness (== less reflextion), so positive = right, negative = left
        steer = self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT] - \
                self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT]

        # if steer > self.min_darkness or steer < -self.min_darkness:
        #     self.add_steer_to_history(steer)
        # else:
        #     print(self.step)
        #     self.add_steer_to_history(self.get_weighted_steer_average())
        # new_speed_inner = self.speed - self.map_steer_to_speed_reduction(self.get_weighted_steer_average())
            
        new_speed_inner = self.speed - self.map_steer_to_speed_reduction(steer)

        if new_speed_inner <= 0:
        # if abs(steer) >= self.max_darkness:
            self.slow_steps_remaining = self.slow_steps_to_make
            # self.slow_steps_remaining = self.slow_steps_to_make + 3

        if self.slow_steps_remaining >= 0:
            # if self.slow_steps_remaining > self.slow_steps_to_make:
            #     fraction = (self.slow_steps_remaining - self.slow_steps_to_make) / 4
            # else:
            fraction = (self.slow_steps_to_make - self.slow_steps_remaining) / self.slow_steps_to_make

            difference = (self.original_speed - self.slow_speed)
            self.set_speed(self.slow_speed + fraction * difference)
            self.slow_steps_remaining = self.slow_steps_remaining - 1
            print(fraction)
            print(self.slow_steps_remaining, self.speed)

        if steer >= self.min_darkness:
            self.th[MOTOR_LEFT] = self.speed
            self.th[MOTOR_RIGHT] = new_speed_inner + 3 # slight correction for Thymio #13
        elif steer <= -self.min_darkness:
            self.th[MOTOR_LEFT] = new_speed_inner
            self.th[MOTOR_RIGHT] = self.speed + 3 # slight correction for Thymio #13
        else:
            self.th[MOTOR_LEFT] = self.speed
            self.th[MOTOR_RIGHT] = self.speed + 3 # slight correction for Thymio #13


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner(
        {PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, BUTTON_CENTER, BUTTON_FRONT, BUTTON_BACK},
        observer,
        0.1)
    runner.run()
