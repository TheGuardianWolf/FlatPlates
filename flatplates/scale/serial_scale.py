from threading import Thread, Lock
from time import sleep
import re
import serial


class SerialScale(object):
    def __init__(self, serial: serial.Serial) -> None:
        super().__init__()

        self.l = Lock()
        self.serial = serial
        self.value = 0.0
        self.unit = "g"

    def start(self) -> None:
        self.serial.open()
        self.t = Thread(target=self.__read_loop)
        self.t.start()

    def stop(self) -> None:
        self.l.release()
        self.t.join(timeout=3)
        self.serial.close()

    def get_value(self) -> tuple[float, str]:
        return (self.value, self.unit)

    def __read_loop(self) -> None:
        self.serial.read_all()
        self.l.acquire(timeout=1)
        while self.l.locked():
            self.__read()
            sleep(0.05)

    def __read(self) -> None:
        line = self.serial.readline()
        start_index = line.find("W:")
        if start_index == -1:
            return

        m = re.search(r"^W:([+-])\s*([\d.]+)(\w+)", line[start_index:])
        if m is None:
            return

        sign: str = m.group(1)
        value: float = float(m.group(2))
        unit: str = m.group(3)

        self.value = value if sign == "+" else value * -1
        self.unit = unit
