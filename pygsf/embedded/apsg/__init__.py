# -*- coding: utf-8 -*-


from .core import (
    Vec3,
    Fol,
    Lin,
    Pair,
    Fault,
    Group,
    PairSet,
    FaultSet,
    Cluster,
    StereoGrid,
    G,
    settings,
)

from .tensors import DefGrad, VelGrad, Stress, Tensor, Ortensor, Ellipsoid
from .helpers import sind, cosd, tand, acosd, asind, atand, atan2d
from .plotting import StereoNet, VollmerPlot, RamsayPlot, FlinnPlot, HsuPlot, RosePlot
from .database import SDB


__all__ = (
    "Vec3",
    "Fol",
    "Lin",
    "Pair",
    "Fault",
    "Group",
    "PairSet",
    "FaultSet",
    "Cluster",
    "StereoGrid",
    "G",
    "settings",
    "SDB",
    "DefGrad",
    "VelGrad",
    "Stress",
    "Tensor",
    "Ortensor",
    "Ellipsoid",
    "sind",
    "cosd",
    "tand",
    "acosd",
    "asind",
    "atand",
    "atan2d",
    "StereoNet",
    "VollmerPlot",
    "RamsayPlot",
    "FlinnPlot",
    "HsuPlot",
    "RosePlot"
)

__version__ = "0.7.0"
__author__ = "Ondrej Lexa"
__email__ = "lexa.ondrej@gmail.com"
