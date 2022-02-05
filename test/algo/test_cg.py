from flatplates.algo import calc_cg, calc_mass


def test_calc_mass():
    assert calc_mass((1, 2, 3)) == 6

def test_calc_cg():
    x, y, z = calc_cg(
        (0.03, 0.034, 0.074),
        (0.035, 0.039, 0.065),
        (0.045, 0.019, 0.076),
        (0.1525),
        (0.1465),
        9.799,
        0.4
    )

    x1, x2 = x
    y1, y2 = y
    z1, z2 = z

    assert round(x1, 5) == 0.05330
    assert round(x2, 5) == 0.05326
    assert round(y1, 5) == 0.03926
    assert round(y2, 5) == 0.04155
    assert round(z1, 5) == 0.01549
    assert round(z2, 5) == 0.01036
