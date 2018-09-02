
from builtins import str
from qgis.PyQt.QtCore import QSettings, QFileInfo
from qgis.PyQt.QtWidgets import QFileDialog


    
 
def define_save_file_name( parent, show_msg, filter_extension, filter_text ):
        
    output_filename, __ = QFileDialog.getSaveFileName(parent, 
                                                  show_msg, 
                                                  filter_extension, 
                                                  filter_text )        
    if not output_filename: 
        return ''
    else:
        return output_filename 
    
    
def define_existing_file_name( parent, show_msg, filter_extension, filter_text ):
        
    input_filename, __ = QFileDialog.getOpenFileName( parent, 
                                                  show_msg, 
                                                  filter_extension, 
                                                  filter_text )        
    if not input_filename: 
        return ''
    else:
        return input_filename   
    
        