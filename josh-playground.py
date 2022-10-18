from thymio_python.thymiodirect import Thymio
from thymio_python.thymiodirect.thymio_serial_ports import ThymioSerialPort
import thymio_utils
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
										refreshing_coverage={thymio_utils.PROXIMITY_GROUND_AMBIANT, thymio_utils.PROXIMITY_GROUND_REFLECTED, thymio_utils.PROXIMITY_GROUND_DELTA},
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
		print("CONNECTIONN")

		# wait 2-3 sec until robots are known
		id = th.first_node()

		def obs(node_id):
			print(f'a: {th[id][thymio_utils.PROXIMITY_GROUND_AMBIANT]} | r: {th[id][thymio_utils.PROXIMITY_GROUND_REFLECTED]} | d: {th[id][thymio_utils.PROXIMITY_GROUND_DELTA]}')
			# print("Ambiend: {}\nDelda: {}\nReflecded: {}".format(th[node_id][thymio_utils.PROXIMITY_GROUND_AMBIENT], th[node_id][thymio_utils.PROXIMITY_GROUND_DELTA], th[node_id][thymio_utils.PROXIMITY_GROUND_REFLECTED]))

		th.set_variable_observer(id, obs)
		
		def set_lights(r, g, b):
			th[id]["leds.top"] = [r, g, b]

		def rainbow(step):
			step = step % (6 * 32)
			i = step % 32
			if step < 1 * 32:
				set_lights(31, i, 0)
			elif step < 2 * 32:
				set_lights(31 - i, 31, 0)
			elif step < 3 * 32:
				set_lights(0, 31, i)
			elif step < 4 * 32:
				set_lights(0, 31 - i, 31)
			elif step < 5 * 32:
				set_lights(i, 0, 31)
			elif step < 6 * 32:
				set_lights(31, 0, 31 - i)

		step = 0
		while True:
			try:
				step = step + 1
				rainbow(step)
				time.sleep(0.05)
			except KeyboardInterrupt:
				break
		th.disconnect()
