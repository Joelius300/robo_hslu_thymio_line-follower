# This file is part of thymiodirect.
# Copyright 2020 ECOLE POLYTECHNIQUE FEDERALE DE LAUSANNE,
# Miniature Mobile Robots group, Switzerland
# Author: Yves Piguet
#
# SPDX-License-Identifier: BSD-3-Clause

# Test of the communication with Thymio via serial port

from thymio_python.thymiodirect import Thymio
from thymio_python.thymiodirect.thymio_serial_ports import ThymioSerialPort
import sys
import os
import time


if __name__ == "__main__":

    # check arguments
    use_tcp = False
    serial_port = None
    host = None
    tcp_port = None
    if len(sys.argv) == 3:
        # tcp: argv[1] = host, argv[2] = port
        use_tcp = True
        host = sys.argv[1]
        tcp_port = int(sys.argv[2])
    elif len(sys.argv) == 2:
        if sys.argv[1] == "--help":
            print("Usage: {sys.argv[0]} [serial_port | host port]")
            sys.exit(0)
        # serial port: argv[1] = serial port
        serial_port = sys.argv[1]

    # use thymio_serial_ports for default Thymio serial port
    if not tcp_port and serial_port is None:
        thymio_serial_ports = ThymioSerialPort.get_ports()
        if len(thymio_serial_ports) > 0:
            serial_port = thymio_serial_ports[0].device
            print("Thymio serial ports:")
            for thymio_serial_port in thymio_serial_ports:
                print(" ", thymio_serial_port, thymio_serial_port.device)

    # connect
    try:
        th = Thymio(use_tcp=use_tcp,
                    serial_port=serial_port,
                    host=host, tcp_port=tcp_port,
                    refreshing_rate=0.05,
                    refreshing_coverage={"prox.horizontal", "button.center", "prox.ground.ambiant", "prox.ground.reflected", "prox.ground.delta"},
                    )
        # constructor options: on_connect, on_disconnect, on_comm_error,
        # refreshing_rate, refreshing_coverage, discover_rate, loop
    except Exception as error:
        print(error)
        exit(1)


    def on_comm_error(error):
        # loss of connection: display error and exit
        print(error)
        os._exit(1)  # forced exit despite coroutines


    th.on_comm_error = on_comm_error

    th.connect()

    # wait 2-3 sec until robots are known
    id = th.first_node()
    print(f"id: {id}")
    print(f"variables: {th.variables(id)}")
    print(f"events: {th.events(id)}")
    print(f"native functions: {th.native_functions(id)[0]}")

    # get a variable
    th[id]["prox.horizontal"]

    # set a variable (scalar or array)
    th[id]["leds.top"] = [0, 0, 32]

    # set a function called after new variable values have been fetched
    prox_prev = 0
    done = False
    up = True
    speed = 50
    #right_speed = 100
    #left_speed = 100

    sensor_width = 3700

    def obs(node_id):
        global prox_prev, done
        prox = (th[node_id]["prox.horizontal"][5] - th[node_id]["prox.horizontal"][2]) // 5
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


    def straight_line(node_id):
        global up, done, speed

        print(th[node_id]["prox.horizontal"])
        print(up)
        print(speed)

        if up and (th[node_id]["prox.horizontal"][0] > 0 or th[node_id]["prox.horizontal"][1] > 0 or
                th[node_id]["prox.horizontal"][2] > 0 or th[node_id]["prox.horizontal"][3] > 0 or
                th[node_id]["prox.horizontal"][4] > 0):
            up = False
            speed = speed - (2 * speed)

        if not up and (th[node_id]["prox.horizontal"][5] > 0 or th[node_id]["prox.horizontal"][6]):
            up = True
            speed = speed - (2 * speed)

        th[node_id]["motor.left.target"] = speed
        th[node_id]["motor.right.target"] = speed

        if th[node_id]["button.center"]:
            print("button.center")
            done = True
    def variable_testing(node_id):
        global done
        # print(th[node_id]["prox"])
        print(th[node_id]["prox.ground.ambiant"])
        print(th[node_id]["prox.ground.reflected"])
        print(th[node_id]["prox.ground.delta"])

        if th[node_id]["button.center"]:
            print("button.center")
            done = True


    def basic_follow_line(node_id):
        def follow_line(node_id):
            global done, right_speed, left_speed, left_sensor_line_found, right_sensor_line_found



            if (th[node_id]["prox.ground.reflected"][0] > 300):
                left_speed = 120
            else:
                left_speed = 100

            if (th[node_id]["prox.ground.reflected"][1] > 300):
                right_speed = 120
            else:
                right_speed = 100

            th[node_id]["motor.left.target"] = left_speed
            th[node_id]["motor.right.target"] = right_speed

            if th[node_id]["button.center"]:
                print("button.center")
                done = True

            # Sobald er die Richtung verliert, sollte ich beginnen heftiger in diese richtung zu gegensteuern
            # damit er die Linie wieder findet.

        # def set_motor_speed_according_to_reflection():


    left_sensor_line_found = True
    right_sensor_line_found = True

    second_sensor_line_found = True

    line_not_found_for_turns = 0


    def follow_big_line(node_id):
        global done, speed, turn_speed, left_speed, right_speed, left_sensor_line_found, right_sensor_line_found, line_not_found_for_turns, second_sensor_line_found

        #print(th[node_id]["prox"])
        print(th[node_id]["prox.ground.ambiant"])
        print(th[node_id]["prox.ground.reflected"])
        print(th[node_id]["prox.ground.delta"])

        #First sensor that does not recognize the line anymore
        #Could implement that as soon as a second sensor also doesn't see it that it turns faster
        if (th[node_id]["prox.ground.reflected"][0] > 300):
            if (not right_sensor_line_found):
                second_sensor_line_found = False
            else:
                left_sensor_line_found = False
        else:
            left_sensor_line_found = True
            right_sensor_line_found = True
            second_sensor_line_found = True

        if (th[node_id]["prox.ground.reflected"][1] > 300):
            if (not left_sensor_line_found):
                second_sensor_line_found = False
            else:
                right_sensor_line_found = False

        else:
            left_sensor_line_found = True
            right_sensor_line_found = True
            second_sensor_line_found = True

        if (not right_sensor_line_found or not  left_sensor_line_found):
            line_not_found_for_turns = line_not_found_for_turns + 1
            if (not second_sensor_line_found):
                line_not_found_for_turns = line_not_found_for_turns + 1
        else:
            second_sensor_line_found = True

        #I Could stabilize by counting the line not found for turns down and correct the left or right
        #speed with it

        if (not left_sensor_line_found):
            left_speed = turn_speed + line_not_found_for_turns * 1
            right_speed = turn_speed
        elif (not right_sensor_line_found):
            right_speed = speed + line_not_found_for_turns * 1
            left_speed = turn_speed
        else:
            right_speed = speed
            left_speed = speed

        th[node_id]["motor.left.target"] = left_speed
        th[node_id]["motor.right.target"] = right_speed

        if th[node_id]["button.center"]:
            print("button.center")
            done = True

        #Sobald er die Richtung verliert, sollte ich beginnen heftiger in diese richtung zu gegensteuern
        #damit er die Linie wieder findet.

    turn_speed = 20
    speed = 50
    right_speed = 100
    left_speed = 100

    left_sensor_line_touched = False
    right_sensor_line_touched = False

    #second_sensor_line_found = True

    line_touched_for_turns = 0


    def follow_small_line(node_id):
        global done, speed, turn_speed, left_speed, right_speed, left_sensor_line_touched, right_sensor_line_touched, line_touched_for_turns #second_sensor_line_found

        #print(th[node_id]["prox"])
        print(th[node_id]["prox.ground.ambiant"])
        print(th[node_id]["prox.ground.reflected"])
        print(th[node_id]["prox.ground.delta"])

        #First sensor that does not recognize the line anymore
        #Could implement that as soon as a second sensor also doesn't see it that it turns faster

        if (th[node_id]["prox.ground.reflected"][0] < 300):
            if (not right_sensor_line_touched):
                left_sensor_line_touched = True
        else:
            left_sensor_line_touched = False

        if (th[node_id]["prox.ground.reflected"][1] < 300):
            if (not left_sensor_line_touched):
                right_sensor_line_touched = True
        else:
            right_sensor_line_touched = False



        if (right_sensor_line_touched or left_sensor_line_touched):
            line_touched_for_turns = line_touched_for_turns + 5

        #I Could stabilize by counting the line not found for turns down and correct the left or right
        #speed with it

        if (left_sensor_line_touched):
            right_speed = turn_speed + line_touched_for_turns
            left_speed = turn_speed
        elif (right_sensor_line_touched):
            left_speed = turn_speed + line_touched_for_turns
            right_speed = turn_speed
        else:
            right_speed = speed
            left_speed = speed

        th[node_id]["motor.left.target"] = left_speed
        th[node_id]["motor.right.target"] = right_speed

        if th[node_id]["button.center"]:
            print("button.center")
            done = True

        #Sobald er die Richtung verliert, sollte ich beginnen heftiger in diese richtung zu gegensteuern
        #damit er die Linie wieder findet.



    #def set_motor_speed_according_to_reflection():


    def balanced_straight_line(node_id):
        global up, done, left_speed, right_speed, sensor_width

        print(th[node_id]["prox.ground.ambiant"])
        print(th[node_id]["prox.ground.reflected"])
        print(th[node_id]["prox.ground.delta"])

        #print(th[node_id]["prox.ground"])
        #print(th[node_id]["prox.horizontal"])
        #print(up)
        #print(left_speed)
        #print(right_speed)


        if up and (th[node_id]["prox.horizontal"][0] > sensor_width or th[node_id]["prox.horizontal"][1] > sensor_width or
                th[node_id]["prox.horizontal"][2] > sensor_width or th[node_id]["prox.horizontal"][3] > sensor_width or
                th[node_id]["prox.horizontal"][4] > sensor_width):
            up = False
            left_speed = -left_speed
            right_speed = -right_speed
            right_speed += 6

        if not up and (th[node_id]["prox.horizontal"][5] > sensor_width or th[node_id]["prox.horizontal"][6] > sensor_width):
            up = True
            left_speed = -left_speed
            right_speed = -right_speed
            right_speed += 6

        th[node_id]["motor.left.target"] = left_speed
        th[node_id]["motor.right.target"] = right_speed

        if th[node_id]["button.center"]:
            print("button.center")
            done = True

#100, 106 Sweet SPot for straight line backwards

    #th.set_variable_observer(id, obs)

    #th.set_variable_observer(id, straight_line)

    th.set_variable_observer(id,  follow_small_line)
    while not done:
        time.sleep(0.1)
    th.disconnect()
