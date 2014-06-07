# -*- coding: utf-8 -*-

from PyQt4.QtGui import QDialog, QVBoxLayout, QTextBrowser

    
class about_Dialog( QDialog ):


    def __init__( self ):

        super( about_Dialog, self ).__init__() 
                            
        self.setup_gui() 

        
    def setup_gui( self ):

        dialog_layout = QVBoxLayout()
        
        htmlText = """
        <h3>qgSurf - release 0.3.2</h3>
        Created by M. Alberti (www.malg.eu).
        <br /><br />Processing of geological planes and surfaces.  
        <br /><br />Licensed under the terms of GNU GPL 3.
        """ 
               
        aboutQTextBrowser = QTextBrowser( self )
        aboutQTextBrowser.insertHtml( htmlText )         
                
        dialog_layout.addWidget( aboutQTextBrowser )                                    
        self.setLayout( dialog_layout )                    
        self.adjustSize()                       
        self.setWindowTitle( 'qgSurf about' )        


