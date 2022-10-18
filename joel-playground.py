from thymio_utils import BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
    PROXIMITY_FRONT_BACK, MOTOR_LEFT, MOTOR_RIGHT, ThymioObserver, print_thymio_functions_events, \
    SingleSerialThymioRunner


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


# for straight and sightly curved lines without intersections
# class ScaledAdjustmentLineDriver(ThymioObserver):


if __name__ == "__main__":
    observer = HandAvoider()
    runner = SingleSerialThymioRunner({BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED,
                                       PROXIMITY_GROUND_DELTA, PROXIMITY_FRONT_BACK},
                                      observer)

    runner.run()
