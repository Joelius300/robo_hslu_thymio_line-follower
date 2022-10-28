from __future__ import annotations

import datetime
import math

import numpy as np

from thymio_python.thymiodirect import ThymioObserver, SingleSerialThymioRunner
from thymio_python.thymiodirect.thymio_constants import BUTTON_CENTER, \
    PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
    MOTOR_LEFT, MOTOR_RIGHT, GROUND_SENSOR_LEFT, GROUND_SENSOR_RIGHT


def clamp(num, min_value, max_value):
    num = max(min(num, max_value), min_value)
    return num


class LineFollower(ThymioObserver):
    """
    Ideen:
    #sobald er dreht und die differenz kleiner wird nicht weiter drauf machen

-> Differenz von links und rechts
-> variabler speed

-> DIfferenz vo dä helligkeit. Schaue die history an von den letzten unterschieden. (also ob es
sich verkleiner hat) Falls es sich verkleinert hat, wieder in die andere richtung (langsam drehen)
auch wenn die Helligkeitsdifferenz immer noch.
Historie der Helligskeitsdifferenzzen anstelle von totalen Helligskeitsdifferenzen

-> KOnfiguration der momentanen Räder beachten


-> Nur dann mehr drauftun wenn es nötig ist (ich speichere die letzten
helligkeiten und schau ob es in die entgegengesetze richtung geht, wenn
ja, nicht weiterghehen)

    """
    def __init__(self):
        super().__init__()
        self.reflection_delta_history = []
        self.reflection_delta_history_max = 20

        self.right_reflection_history = []
        self.left_reflection_history = []

        self.left_speed = 200
        self.right_speed = 200
        self.base_speed = 250

        self.counter = 0
        self.consecutive_steps = 1 # determines the average of reflection steps that i take

        self.right_correction_mode = False
        self.left_correction_mode = False
        self.darkness_correction_condition = 650

        self.correction_steps = 0
        self.correction_mode_counter = 0
        self.refreshing_rate_factor = 1 #10 or so when refreshingr rate 20, 1 when refreshing rate 100
        self.correction_marker_low_refreshing_rate = 70

        self.set_speed(self.base_speed)
    def exponential_curve(self, steps: int, stop: float, log_base: float):
        base = math.log(steps, log_base)
        points = [math.floor(stop / math.pow(base, i)) for i in range(steps)]
        points.reverse()
        return points

    def set_speed(self, new_speed):
        self.speed = math.floor(new_speed)
        print(self.speed)
        return

    def check_correction_mode(self):
        exit()

    def _update(self):
        self.follow_the_darkness()
        self.handle_buttons()

    def handle_buttons(self):
        if self.th[BUTTON_CENTER]:
            print("done")
            self.th[MOTOR_LEFT] = 0
            self.th[MOTOR_RIGHT] = 0
            self.stop()

    def calculate_reflection_difference_trend(self, reflection_history):
        trend = 0
        starting_reflection = np.mean(reflection_history[-self.consecutive_steps])

        for i in range(-self.consecutive_steps - 1, -1001, -self.consecutive_steps):
            new_left_trend = starting_reflection - np.mean(reflection_history[i - self.consecutive_steps: i])

            if 0 <= trend <= new_left_trend:
                trend = new_left_trend

            elif 0 >= trend >= new_left_trend:
                trend = new_left_trend
            else:
                return trend

    def determine_reflection_speed_delta(self):

        #Trend with which you can determine the short term validaty of turning around or whatever
        small_reflection_trend = np.mean(self.reflection_delta_history[-1:]) - np.mean(self.reflection_delta_history[-4:-3])
        medium_reflection_trend = np.mean(self.reflection_delta_history[-1:]) - np.mean(self.reflection_delta_history[-6:-5])
        bigger_reflection_trend = np.mean(self.reflection_delta_history[-1:]) - np.mean(self.reflection_delta_history[-9:-7])


        #Calculate the left and right reflection trend of the
        left_reflection_trend = self.calculate_reflection_difference_trend(self.left_reflection_history)
        right_reflection_trend = self.calculate_reflection_difference_trend(self.right_reflection_history)


        starting_reflection_trend = np.mean(self.reflection_delta_history[-self.consecutive_steps:])
        consecutive_trend = 0
        consecutive_reach = 0

        # Calculate Consecutive Reflection difference between left and right reflection and the reach (meaning how far the trend goes back)
        for i in range(-self.consecutive_steps - 1, -1001, -self.consecutive_steps):
            mean_steps_ago = np.mean(self.reflection_delta_history[i - self.consecutive_steps: i])
            trend = starting_reflection_trend - mean_steps_ago

            if 0 <= consecutive_trend <= trend:
                consecutive_trend = trend
                consecutive_reach = consecutive_reach + self.consecutive_steps

            elif 0 >= consecutive_trend >= trend:
                consecutive_trend = trend
                consecutive_reach = consecutive_reach + self.consecutive_steps
            else:
                break


        #Determines the Correction Mode. Can add self.darkness_correction_condition, which means that if will not be activated on following a regular straight
        #black line, so only when an actual curves comes it will activate.
        if (left_reflection_trend < -300 or self.left_correction_mode): #and self.darkness_correction_condition < self.right_reflection_history[-1]:
            self.left_correction_mode = True
        elif (right_reflection_trend < -300 or self.right_correction_mode): #and self.darkness_correction_condition < self.left_reflection_history[-1]:
            self.right_correction_mode = True


        if (self.left_correction_mode):
            consecutive_trend = -250 - self.correction_steps
            self.correction_steps = self.correction_steps + ((2 + math.floor(self.correction_mode_counter // 4)) * self.refreshing_rate_factor)

            self.correction_mode_counter = self.correction_mode_counter + 1

            if self.refreshing_rate_factor == 10 and self.correction_marker_low_refreshing_rate > 0:
                self.correction_steps = self.correction_steps + self.correction_marker_low_refreshing_rate
                self.correction_marker_low_refreshing_rate = self.correction_marker_low_refreshing_rate - 10


            if self.darkness_correction_condition > self.right_reflection_history[-1]:
                self.correction_mode_counter = 0
                self.left_correction_mode = False
                self.correction_steps = 0
                self.correction_marker_low_refreshing_rate = 70

        if (self.right_correction_mode):
            consecutive_trend = 250 + self.correction_steps
            self.correction_steps = self.correction_steps + ((2 + math.floor(self.correction_mode_counter // 4)) * self.refreshing_rate_factor)

            self.correction_mode_counter = self.correction_mode_counter + 1

            if self.refreshing_rate_factor == 10 and self.correction_marker_low_refreshing_rate > 0:
                self.correction_steps = self.correction_steps + self.correction_marker_low_refreshing_rate
                self.correction_marker_low_refreshing_rate = self.correction_marker_low_refreshing_rate - 10

            if self.darkness_correction_condition > self.left_reflection_history[-1]:
                self.correction_mode_counter = 0
                self.right_correction_mode = False
                self.correction_steps = 0
                self.correction_marker_low_refreshing_rate = 70

        print(f"Consecutive Trend: {consecutive_trend}")
        print(f"Left Trend {left_reflection_trend}        Right Trend {right_reflection_trend}")
        print(f"Consecutive Reach: {consecutive_reach}")
        print(f"---------------------------------------------------->{self.left_correction_mode}")


        #Still not sure here. Tried different things with math pow and log and stuff, but as long as refreshing rate is 100, this is fine, because
        #as soon as the curves comes the correction mode corrects
        is_negative = consecutive_trend < 0
        consecutive_trend_abs = math.floor(abs(consecutive_trend))
        speed_correction = math.floor(consecutive_trend_abs // 10) #math.pow(consecutive_trend_abs, 1.2)) // 10 # np.log(abs(consecutive_trend) + 10))
        speed_correction = -speed_correction if is_negative else speed_correction
        print(f"Correction: {speed_correction}")

        now = datetime.datetime.now()
        print (f"Time {now.time()}")

        return speed_correction

    def follow_the_darkness(self):


        #Notice, sadly i figured out that it works best with a refreshing rate of 100, and it seems like this only really works with a cable
        #Without a cable, it is worse.
        steer = self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT] - \
                self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT]

        print(f"Reflection Left  Sensor:  {self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT]}")
        print(f"Reflection Right Sensor: {self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT]}")

        self.reflection_delta_history.append(steer)
        self.left_reflection_history.append(self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_LEFT])
        self.right_reflection_history.append(self.th[PROXIMITY_GROUND_REFLECTED][GROUND_SENSOR_RIGHT])

        speed_correction = 0
        if (len(self.reflection_delta_history) > 5):
                speed_correction = self.determine_reflection_speed_delta()

        self.right_speed = self.base_speed - speed_correction
        self.left_speed = self.base_speed + speed_correction

        print(f"Right Speed: {self.right_speed}     Left Speed: {self.left_speed}")
        self.th[MOTOR_RIGHT] = self.right_speed
        self.th[MOTOR_LEFT] = self.left_speed


if __name__ == "__main__":
    observer = LineFollower()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA},
                                      observer,
                                      1 / 100)
    runner.run()
