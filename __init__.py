"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 geological planes operations
 
                              -------------------
        begin                : 2011-12-21
        version              : 0.2.2 for QuantumGIS 2.0, released 2013-10-23 
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


def classFactory( iface ):    
    from qgSurf_gui import qgSurf_gui 
    return qgSurf_gui( iface )



