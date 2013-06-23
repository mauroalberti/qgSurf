"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 DEM - planes intersections
                              -------------------
        begin                : 2011-12-21
        version              : 0.2.1 for QuantumGIS 
        copyright            : (C) 2011-2013 by Mauro Alberti - www.malg.eu
        email                : alberti.m65@gmail.com
        
 ***************************************************************************/

# licensed under the terms of GNU GPL 3

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""



def name():
    return "qgSurf"

def description():
    return "Compute intersections between DEM and planes"

def version():
    return "0.2.1"

def authorName():
    return "Mauro Alberti"

def author():
    return "Mauro Alberti"

def email():
    return "alberti.m65@gmail.com"

def homepage():
    return "https://bitbucket.org/mauroalberti/qgsurf"

def icon():
    return "icons/qgsurf.png"

def qgisMinimumVersion():
    return "1.8"

def classFactory( iface ):    
    from qgSurf_gui import qgSurf_gui 
    return qgSurf_gui( iface )



