# -*- coding: utf-8 -*-


latitude_one_degree_45degr_meters = 111131.745  #  source: http://www.csgnetwork.com/degreelenllavcalc.html, consulted on 2018-12-23


def latLengthOneMinutePrime() -> float:
    """
    Approximate length (in meters) of one minute prime at latitude 45°.
    :return: length in meters.
    :rtype: float
    """

    return latitude_one_degree_45degr_meters / 60.0


def latLengthOneMinuteSecond() -> float:
    """
    Approximate length (in meters) of one minute second at latitude 45°.
    :return: length in meters.
    :rtype: float
    """

    return latitude_one_degree_45degr_meters / 3600.0


if __name__ == "__main__":

    print("Approximate length of one minute prime at 45° latitude: {} meters".format(latLengthOneMinutePrime()))
    print("Approximate length of one minute second at 45° latitude: {} meters".format(latLengthOneMinuteSecond()))

