import serial
import yaml
import os
import csv
import time
import sys
from threading import Thread, Event
from ..algo import calc_cg
from ..algo.cg import calc_mass
from ..scale import SerialScale


class ScaleCLI(object):
    def __init__(self):
        self.x_dom = (0.0, 0.0, 0.0)
        self.y_dom = (0.0, 0.0, 0.0)
        self.evt_enter = Event()

    def __print_intro(self):
        print("=== FlatPlates CoG Calculator ===")
        print()

    def __print_report(self):
        ports: dict = self.config["scale_ports"]
        print("Constants loaded:")
        print(f"g (Gravity): {self.config['gravity']} m/s^2")
        print(f"L (Sensor distance): {self.config['sensor_distance']} m")
        print()
        print("Scales configured with serial ports:")
        print(f"Scale A: {ports['a']}")
        print(f"Scale B: {ports['b']}")
        print(f"Scale C: {ports['c']}")
        print()
        print("===")
        print()

    def __print_dom_values(self):
        print(f"Current x_dom: {self.x_dom}")
        print(f"Current y_dom: {self.y_dom}")
        print()
        print("===")
        print()

    def __change_dom_values(self):
        selection = input("Change x_dom and y_dom? (y/N):\n")
        if selection.lower() == "y":
            raw_x_dom = input(
                "Enter x_dom value(s) in m (example: 0.15, 0.14, 0.13):\n"
            )
            raw_y_dom = input(
                "Enter y_dom value(s) in m (example: 0.15, 0.14, 0.13):\n"
            )
            self.x_dom = (float(t.trim()) for t in raw_x_dom.split(","))
            self.y_dom = (float(t.trim()) for t in raw_y_dom.split(","))
        print()
        print("===")
        print()

    def __print_measurements(self, x_cg, y_cg, z_cg, tm_a, tm_b, tm_c, tm_avg, m_a, m_b, m_c, x_dom, y_dom):
        print("Current set of results:")
        print()

        print("Calculated from measurements:")
        print()

        print()
        print("===")
        print()

    def __print_statusline(self, msg: str, clear_last: bool = True, hide_cursor: bool = True):
        last_msg_length = len(self.__last_msg) if hasattr(self, "last_msg") else 0
        if hide_cursor:
            print("\033[?25l", end="")
        if clear_last:
            print(" " * last_msg_length, end="\r")
        print(msg, end="\r")
        sys.stdout.flush()
        self.__last_msg = msg

    def __show_cursor(self):
        print("\033[?25h", end="")

    def wait_for_enter(self):
        self.evt_enter.clear()
        def wait_input():
            input()
            self.evt_enter.set()

        t = Thread(target=wait_input, daemon=True)
        t.start()

    def setup(self, root_dir=os.getcwd()) -> None:
        self.__print_intro()

        with open(os.path.join(root_dir, "config.yaml"), "r") as stream:
            try:
                self.config: dict = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(
                    "Error! Please ensure the configuration file exists and is formatted properly..."
                )
                raise exc

        self.__print_report()

        self.fp_out = open(
            os.path.join(os.getcwd(), f"data.{int(time.time())}.csv"), "w"
        )
        self.csv_writer = csv.writer(self.fp_out)
        self.csv_writer.writerow(
            [
                "x1",
                "x2",
                "y1",
                "y2",
                "z1",
                "z2",
                "tma",
                "tmb",
                "tmc",
                "tmavg",
                "ma1",
                "ma2",
                "ma3",
                "mb1",
                "mb2",
                "mb3",
                "mc1",
                "mc2",
                "mc3",
                "xdoma",
                "ydoma",
                "xdomb",
                "ydomb",
                "xdomc",
                "ydomc",
            ]
        )

        ports: tuple[str, str, str] = (self.config["scale_ports"]["1"], self.config["scale_ports"]["2"], self.config["scale_ports"]["3"])
        self.ser = tuple(serial.Serial() for _ in range(0, 3))

        for port, s in zip(ports, self.ser):
            s.timeout = 1
            s.baudrate = 9600
            s.port = port

        self.scales = (SerialScale(s) for s in self.ser)
        for scale in self.scales:
            scale.start()

    def measurement(self) -> None:
        while True:
            self.__print_dom_values()
            self.__change_dom_values()

            questions = [
                "Press enter to take first readings:",
                "Press enter to take second readings:",
                "Press enter to take third readings:"
            ]
            measurements: list[float] = []
            for question in questions:
                print(question)
                self.wait_for_enter()
                v = [0.0, 0.0, 0.0]
                while not self.evt_enter.is_set():
                    v = tuple(s.get_value() for s in self.scales)
                    self.__print_statusline(str(v), clear_last=False)
                    time.sleep(0.05)
                print()
                self.__show_cursor()
                r, u = zip(*v)
                measurements.append(r)

            m_a, m_b, m_c = zip(*measurements)

            x_cg, y_cg, z_cg = calc_cg(
                m_a,
                m_b,
                m_c,
                self.x_dom,
                self.y_dom,
                self.config["gravity"],
                self.config["sensor_distance"],
            )

            tm_a = calc_mass(m_a)
            tm_b = calc_mass(m_b)
            tm_c = calc_mass(m_c)
            tm_avg = sum(tm_a, tm_b, tm_c) / 3

            self.__print_measurements(
                x_cg,
                y_cg,
                z_cg,
                tm_a,
                tm_b,
                tm_c,
                tm_avg,
                m_a,
                m_b,
                m_c,
                self.x_dom,
                self.y_dom
            )

            readings = [
                *x_cg,
                *y_cg,
                *z_cg,
                tm_a,
                tm_b,
                tm_c,
                tm_avg,
                *m_a,
                *m_b,
                *m_c,
                *self.x_dom,
                *self.y_dom,
            ]
            self.csv_writer.writerow(readings)

            selection = input("Take another set of readings? (Y/n):\n")
            if selection.lower() == "n":
                break

    def cleanup(self):
        for scale in self.scales:
            scale.stop()

        self.fp_out.close()

        for s in self.ser:
            s.close()
