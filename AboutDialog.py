"""
/***************************************************************************
 qgSurf - plugin for Quantum GIS

 Processing of geological planes and surfaces

                              -------------------
        begin                : 2011-12-21
        copyright            : (C) 2011-2018 by Mauro Alberti
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

# -*- coding: utf-8 -*-


from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTextBrowser

    
class AboutDialog(QDialog):

    def __init__(self, plugin_nm, version):

        super(AboutDialog, self).__init__()

        dialog_layout = QVBoxLayout()
        
        htmlText = """
        <h3>qgSurf - release {}</h3>
        Created by M. Alberti (alberti.m65@gmail.com).
        <br /><br /><a href="https://github.com/mauroalberti/qgSurf">https://github.com/mauroalberti/qgSurf</a>
        <br /><br />Processing of geological data.  
        <br /><br />Licensed under the terms of GNU GPL 3.
        """.format(version)
               
        aboutQTextBrowser = QTextBrowser(self)
        aboutQTextBrowser.insertHtml(htmlText)         
        aboutQTextBrowser.setMinimumSize(400, 200)
        dialog_layout.addWidget(aboutQTextBrowser)

        self.setLayout(dialog_layout)                    

        self.setWindowTitle('{} about'.format(plugin_nm))


