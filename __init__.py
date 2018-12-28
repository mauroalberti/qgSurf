"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 Processing of geological planes and surfaces
 
                              -------------------
        begin                : 2011-12-21
        copyright            : (C) 2011-2019 by Mauro Alberti - www.malg.eu
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
from __future__ import absolute_import


def classFactory( iface ):    
    from .QgSurfGui import QgSurfGui
    return QgSurfGui(iface)



