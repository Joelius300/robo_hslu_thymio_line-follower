import math

from thymio_python.thymiodirect import SingleSerialThymioRunner, ThymioObserver
from thymio_python.thymiodirect.thymio_constants import PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, \
	BUTTON_CENTER, BUTTON_FRONT, BUTTON_BACK, MOTOR_LEFT, MOTOR_RIGHT, LEDS_TOP

from inputs import get_gamepad
import threading

class XboxController(object):
		MAX_TRIG_VAL = math.pow(2, 8)
		MAX_JOY_VAL = math.pow(2, 15)

		def __init__(self):
				self.LeftJoystickY = 0
				self.LeftJoystickX = 0
				self.LeftTrigger = 0
				self.RightTrigger = 0
				self.LeftBumper = 0
				self.RightBumper = 0
				self.A = 0
				self.X = 0
				self.Y = 0
				self.B = 0
				self.UpDPad = 0
				self.DownDPad = 0

				self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
				self._monitor_thread.daemon = True
				self._monitor_thread.start()

		def read(self):
				joyX = self.LeftJoystickX
				lt = self.LeftTrigger
				rt = self.RightTrigger
				lb = self.LeftBumper
				rb = self.RightBumper
				a = self.A
				b = self.B
				return [joyX, lt, rt, lb, rb, a, b]

		def _monitor_controller(self):
				while True:
						events = get_gamepad()
						for event in events:
								if event.code == 'ABS_X':
										self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL
								elif event.code == 'ABS_Z':
										self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL
								elif event.code == 'ABS_RZ':
										self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL
								elif event.code == 'BTN_TL':
										self.LeftBumper = event.state
								elif event.code == 'BTN_TR':
										self.RightBumper = event.state
								elif event.code == 'BTN_SOUTH':
										self.A = event.state
								elif event.code == 'BTN_EAST':
										self.B = event.state



class LineFollower(ThymioObserver):
	def __init__(self):
		super().__init__()
		self.step = 0
		self.speed_step = 10
		self.original_speed = 250
		self.speed = None
		self.set_speed(self.original_speed)

	def set_speed(self, new_speed):
		self.speed = math.floor(new_speed)
		return

	def _update(self):
		self.step = self.step + 1
		self.rainbow(self.step)
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
		(joyX, lt, rt, lb, rb, a, b) = controller.read()

		self.set_speed(lt * -self.original_speed + rt * self.original_speed)
		
		if abs(joyX) > 0.05:
			if self.speed > 0:
				speed_adjustment = self.speed * joyX
			else:
				speed_adjustment = self.original_speed * joyX
			self.th[MOTOR_LEFT] = self.speed + math.floor(speed_adjustment)
			self.th[MOTOR_RIGHT] = self.speed - math.floor(speed_adjustment)
		else:
			self.th[MOTOR_LEFT] = self.speed
			self.th[MOTOR_RIGHT] = self.speed

		if self.th[BUTTON_CENTER]:
			print("done")
			self.th[MOTOR_LEFT] = 0
			self.th[MOTOR_RIGHT] = 0
			self.stop()
		if self.th[BUTTON_FRONT] or rb == 1 or a == 1:
			self.original_speed = self.original_speed + self.speed_step
			self.set_speed(self.original_speed)
			print(self.original_speed)
		if self.th[BUTTON_BACK] or lb == 1 or b == 1:
			self.original_speed = self.original_speed - self.speed_step
			self.set_speed(self.original_speed)
			print(self.original_speed)


if __name__ == "__main__":
	controller = XboxController()
	observer = LineFollower()
	runner = SingleSerialThymioRunner(
		{PROXIMITY_GROUND_REFLECTED, PROXIMITY_GROUND_DELTA, BUTTON_CENTER, BUTTON_FRONT, BUTTON_BACK},
		observer,
		0.1)
	runner.run()
