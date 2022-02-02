from typing import Union, cast
import logging
from math import sqrt

log = logging.getLogger(__name__)

# Type of a set of measurements
measurement = tuple[float, float, float]


def calc_mass(m: measurement) -> float:
    """Calculate mass using the three scale method. Is a sum of mass from all scale measurements.

    Args:
        m (tuple[float, float, float]): Three mass measurements in kg

    Returns:
        float: Calculated mass from the three measurements in kg.
    """

    return sum(m)


def calc_cg(
    m_a: measurement,
    m_b: measurement,
    m_c: measurement,
    x_dom: Union[measurement, float],
    y_dom: Union[measurement, float],
    g: float = 9.799,
    l: float = 0.4,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Calculate center of gravity for a set of measurements. Uses the three scale method.

    Args:
        m_a (tuple[float, float, float]): Three mass measurements from A in kg
        m_b (tuple[float, float, float]): Three mass measurements from B in kg
        m_c (tuple[float, float, float]): Three mass measurements from C in kg
        x_dom (Union[tuple[float, float, float], float]): Single value or a set of three different origin coordinates in m
        y_dom (Union[tuple[float, float, float], float]): Single value or a set of three different origin coordinates in m
        g (float, optional): Gravity constant in m/s^2. Defaults to 9.799.
        l (float, optional): Distance between sensors in m. Defaults to 0.4.

    Returns:
        tuple[tuple[float, float], tuple[float, float], tuple[float, float]]: In order: (x from A, x from B), (y from A, y from C), (z from B, z from C)
    """
    # Check if x_dom and y_dom have triplets, if so use that, otherwise duplicate
    try:
        assert len(x_dom) >= 3 and len(y_dom) >= 3
    except AssertionError:
        x_dom = tuple([x_dom[0]] * 3)
        y_dom = tuple([y_dom[0]] * 3)
    except TypeError:
        x_dom = tuple([x_dom] * 3)
        y_dom = tuple([y_dom] * 3)

    x_dom_t = cast(measurement, x_dom[0:3])
    y_dom_t = cast(measurement, y_dom[0:3])

    w_a = (n * g for n in m_a)
    w_b = (n * g for n in m_b)
    w_c = (n * g for n in m_c)

    tm_a = calc_mass(m_a)
    tm_b = calc_mass(m_b)
    tm_c = calc_mass(m_c)

    x1 = ((0.5 * w_a[2] * l + l * w_a[1]) / (tm_a * g)) - x_dom_t[0]
    x2 = ((0.5 * w_b[2] * l + l * w_b[1]) / (tm_b * g)) - x_dom_t[1]

    y1 = ((0.5 * sqrt(3) * w_a[2] * l) / (tm_a * g)) - y_dom_t[0]
    y2 = ((0.5 * sqrt(3) * w_c[2] * l) / (tm_c * g)) - y_dom_t[2]

    z1 = ((0.5 * sqrt(3) * w_b[2] * l) / (tm_b * g)) - y_dom_t[1]
    z2 = ((0.5 * w_c[2] * l + l * w_c[1]) / (tm_c * g)) - x_dom_t[2]

    return ((x1, x2), (y1, y2), (z1, z2))
