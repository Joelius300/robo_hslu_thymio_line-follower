from abc import ABC, abstractmethod
import time
from typing import Optional

from serial import PortNotOpenError

from thymio_python.thymiodirect import Thymio

PROXIMITY_FRONT_BACK = "prox.horizontal"
PROXIMITY_GROUND_AMBIENT = "prox.ground.ambiant"
PROXIMITY_GROUND_REFLECTED = "prox.ground.reflected"
PROXIMITY_GROUND_DELTA = "prox.ground.delta"

BUTTON_CENTER = "button.center"

MOTOR_LEFT = "motor.left.target"
MOTOR_RIGHT = "motor.right.target"


def print_thymio_functions_events(th: Thymio, node_id: int):
    print(f"id: {node_id}")
    print(f"variables: {th.variables(node_id)}")
    print(f"events: {th.events(node_id)}")
    print(f"native functions: {th.native_functions(node_id)[0]}")


class ThymioObserver(ABC):
    def __init__(self):
        self.thymio: Thymio = None
        self.th: Thymio.Node = None
        self._node_id: int = None
        self.done = False

    def set_thymio_node(self, thymio: Thymio, node_id: int):
        self.thymio = thymio
        self.th = thymio[node_id]
        self._node_id = node_id

    def run(self):
        self.done = False
        self.thymio.set_variable_observer(self._node_id, self._observe)
        while not self.done:
            try:
                time.sleep(.05)
            except KeyboardInterrupt:
                self.done = True

    def _observe(self, node_id):
        if self.done:
            return

        assert (node_id == self._node_id)
        self._update()

    @abstractmethod
    def _update(self):
        pass

    def stop(self):
        self.done = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


class SingleSerialThymioRunner:
    def __init__(self,
                 refreshing_coverage: set,
                 observer: ThymioObserver,
                 refreshing_rate=0.1,
                 serial_port: Optional[str] = None,
                 connection_delay=1.5
                 ):
        self.thymio = Thymio(refreshing_coverage=refreshing_coverage,
                             refreshing_rate=refreshing_rate,
                             serial_port=serial_port,
                             on_comm_error=lambda e: self._on_error(e),
                             discover_rate=1)
        self.observer = observer
        self._connection_delay = connection_delay

    def _on_error(self, error):
        print(error)
        self.observer.stop()

    def run(self):
        with self.thymio, self.observer:
            self.thymio.connect()

            time.sleep(self._connection_delay)

            id = self.thymio.first_node()
            self.observer.set_thymio_node(self.thymio, id)

            try:
                self.observer.run()  # blocks until end
            except PortNotOpenError as error:
                if not self.observer.done:
                    raise error  # during disconnect, there may be a serial port error but we don't care about that
