"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 DEM - planes intersections
                              -------------------
        begin                : 2011-12-21
        version              : 0.1.3 for QuantumGIS - 2012-10-7
        copyright            : (C) 2011-2012 by Mauro Alberti - www.malg.eu
        email                : alberti.m65@gmail.com
        
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""


from qgSurf_gui import qgSurf_gui


def name():
    return "qgSurf"

def description():
    return "Compute intersections between DEM and planes"

def version():
    return "0.1.3"

def author():
    return "Mauro Alberti"

def email():
    return "alberti.m65@gmail.com"

def icon():
    return "icon.png"

def qgisMinimumVersion():
    return "1.8"

def classFactory(iface):    
    # create qgSurf_gui class   
    return qgSurf_gui(iface)



