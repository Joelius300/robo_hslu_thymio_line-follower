import os

from thymio_python.thymiodirect import Connection, Thymio
from thymio_python.thymiodirect.thymio_serial_ports import ThymioSerialPort
import sys
import time
from thymio_utils import BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, PROXIMITY_FRONT_BACK

if __name__ == "__main__":
    def on_error(error):
        print(error)
        global done
        done = True  # should make the waiting loop exit which (thanks to the with) will disconnect the Thymio

    th = None
    try:
        th = Thymio(refreshing_coverage={BUTTON_CENTER, PROXIMITY_GROUND_AMBIENT, PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, PROXIMITY_FRONT_BACK})
        th.on_comm_error = on_error
        th.connect()
    except Exception as error:
        if th is not None:
            th.disconnect()
        print(error)
        sys.exit(1)

    # wait 2-3 sec until robots are known
    time.sleep(2)

    with th:
        id = th.first_node()

        print(f"id: {id}")
        print(f"variables: {th.variables(id)}")
        print(f"events: {th.events(id)}")
        print(f"native functions: {th.native_functions(id)[0]}")

        # get a variable
        print(f'prox.horizontal: {th[id]["prox.horizontal"]}')

        # set a variable (scalar or array)
        th[id]["leds.top"] = [0, 0, 32]

        # set a function called after new variable values have been fetched
        prox_prev = 0
        done = False

        def obs(node_id):
            global prox_prev, done
            prox = (th[node_id]["prox.horizontal"][5] - th[node_id]["prox.horizontal"][2]) // 10

            print(th[node_id][PROXIMITY_GROUND_AMBIENT])

            if prox != prox_prev:
                th[node_id]["motor.left.target"] = prox
                th[node_id]["motor.right.target"] = prox
                print(prox)
                if prox > 5:
                    th[id]["leds.top"] = [0, 32, 0]
                elif prox < -5:
                    th[id]["leds.top"] = [32, 32, 0]
                elif abs(prox) < 3:
                    th[id]["leds.top"] = [0, 0, 32]
                prox_prev = prox
            if th[node_id]["button.center"]:
                print("button.center")
                done = True

        th.set_variable_observer(id, obs)

        while not done:
            try:
                time.sleep(.05)
            except KeyboardInterrupt:
                break
