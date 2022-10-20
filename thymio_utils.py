from abc import ABC, abstractmethod
import time
from typing import Optional

from thymio_python.thymiodirect import Thymio

PROXIMITY_FRONT_BACK = "prox.horizontal"
PROXIMITY_GROUND_AMBIENT = "prox.ground.ambiant"
PROXIMITY_GROUND_REFLECTED = "prox.ground.reflected"
PROXIMITY_GROUND_DELTA = "prox.ground.delta"

GROUND_SENSOR_LEFT = 0
GROUND_SENSOR_RIGHT = 1

BUTTON_CENTER = "button.center"
BUTTON_RIGHT = "button.right"
BUTTON_LEFT = "button.left"

MOTOR_LEFT = "motor.left.target"
MOTOR_RIGHT = "motor.right.target"

LEDS_TOP = "leds.top"


def print_thymio_functions_events(th: Thymio, node_id: int):
    print(f"id: {node_id}")
    print(f"variables: {th.variables(node_id)}")
    print(f"events: {th.events(node_id)}")
    print(f"native functions: {th.native_functions(node_id)[0]}")


class ThymioObserver(ABC):
    """
    Abstract observer to execute code in an update loop after the newest values are fetched.
    Only one observer can run per node; you have to implement a combined observer to run multiple observers per thymio node.
    """
    def __init__(self):
        self.thymio: Thymio = None
        self.th: Thymio.Node = None
        self._node_id: int = None
        self._done = False

    @property
    def done(self) -> bool:
        """
        Gets whether the observer is done observing.
        """
        return self._done

    def set_thymio_node(self, thymio: Thymio, node_id: int):
        """
        Sets the thymio node this observer runs on
        """
        self.thymio = thymio
        self.th = thymio[node_id]
        self._node_id = node_id

    def run(self):
        """
        Run the observer until it is stopped or interrupted (blocking).
        Before running the observer, you need to set the thymio node (set_thymio_node)!
        """
        self.start()
        self.block_until_done()

    def _observe(self, node_id):
        if self.done:
            return

        if node_id != self._node_id:
            print("Observe called by a node that is not the registered thymio node of this observer!")

        self._update()

    @abstractmethod
    def _update(self):
        """
        Called everytime the values are fetched from the thymio (refreshing_rate configurable on the thymio itself).
        """
        pass

    def _reset(self):
        self._done = False

    def start(self):
        """
        Registers and enables the observer without blocking (returns immediately).
        Before starting the observer, you need to set the thymio node (set_thymio_node)!
        """
        self._reset()
        self.thymio.set_variable_observer(self._node_id, self._observe)

    def block_until_done(self):
        """
        Blocks until the observer is done (stopped) or interrupted.
        """
        while not self.done:
            try:
                time.sleep(.05)
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """
        Stop operation and prevent _update from being called again.
        This also stops run() and block_until_done() from blocking and makes them return.
        """
        self._done = True
        self.thymio.set_variable_observer(self._node_id, lambda: None)

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
        """
        Runs the specified observer on the first (and only) thymio node connected via serial until the observer is
        stopped or interrupted.
        """
        with self.thymio, self.observer:
            self.thymio.connect()

            time.sleep(self._connection_delay)

            id = self.thymio.first_node()
            self.observer.set_thymio_node(self.thymio, id)

            self.observer.run()  # blocks until done
