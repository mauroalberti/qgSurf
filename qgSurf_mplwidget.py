
"""
        
        This file contains modified code from Tosi book - Matplotlib for Python Developers
        
"""


import os
import webbrowser

# Python Qt4 bindings for GUI objects
from PyQt4 import QtCore, QtGui

from matplotlib import rcParams


# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

# import the NavigationToolbar Qt4Agg widget
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

# Matplotlib Figure object
from matplotlib.figure import Figure


set_srcpt_count = 0
  
        

class MplCanvas(FigureCanvas):
    """
    Class to represent the FigureCanvas widget.
    """
    
    def __init__( self, map_extent_x, map_extent_y ):
        
        self.set_rcParams()        
        self.setup_Figure(map_extent_x, map_extent_y)        
        self.setup_FigureCanvas()
            

    def set_rcParams(self):
    
        rcParams["font.size"] = 9.0
        rcParams["xtick.direction"] = 'out'        
        rcParams["ytick.direction"] = 'out'  
        
        rcParams["figure.subplot.left"] = 0.1  
        rcParams["figure.subplot.right"] = 0.96  
        rcParams["figure.subplot.bottom"] = 0.06  
        rcParams["figure.subplot.top"] = 0.96  
        rcParams["figure.subplot.wspace"] = 0.1  
        rcParams["figure.subplot.hspace"] = 0.1  
        
        rcParams["figure.facecolor"] = 'white' 


    def setup_Figure(self, map_extent_x, map_extent_y):        
        
        # setup Matplotlib Figure and Axis
        
        self.fig = Figure()
        
        self.ax = self.fig.add_subplot(111)
        
        self.ax.set_aspect(1.)

        x_min_init,x_max_init = map_extent_x 
        y_min_init,y_max_init = map_extent_y
                
        self.ax.set_xlim(x_min_init,x_max_init)
        self.ax.set_ylim(y_min_init,y_max_init) 
        
        
    def setup_FigureCanvas(self):        
        
        FigureCanvas.__init__(self, self.fig)
        
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self) 
        
        
class MplWidget(QtGui.QWidget):
    """
    Widget defined in Qt Designer.
    """
    
    def __init__(self, map_extent_x, map_extent_y, parent = None):
        
        # initialization of Qt MainWindow widget
        QtGui.QWidget.__init__(self, parent)
        
        # set the canvas to the Matplotlib widget
        self.canvas = MplCanvas( map_extent_x, map_extent_y )
        
        # manage the navigation toolbar
        self.ntb = NavigationToolbar(self.canvas, self)        
        #self.ntb.removeAction(self.ntb.buttons[0])
        self.ntb.clear()
        
        
        program_folder = os.path.join(os.path.dirname(__file__), "ims" )

        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "world.png")), 'Home', self.zoom2fullextent)
        a.setToolTip('Reset original view')
        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "arrow_left.png")), 'Back', self.ntb.back)
        a.setToolTip('Back to previous view')
        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "arrow_right.png")), 'Forward', self.ntb.forward)
        a.setToolTip('Forward to next view')

        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "arrow_out.png")), 'Pan', self.ntb.pan)
        a.setToolTip('Pan axes with left mouse, zoom with right')
        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "zoom.png")), 'Zoom', self.ntb.zoom)
        a.setToolTip('Zoom to rectangle')

        action_SetSrcPt = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "bullet_red.png")), 'Source point', self.pt_map)
        action_SetSrcPt.setToolTip('Set source point in map') 

        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "camera.png")), 'Save',
                self.ntb.save_figure)
        a.setToolTip('Save map as image')

        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "help.png")), 'Help',
                self.openHelp)
        a.setToolTip('Help')
        
        a = self.ntb.addAction(self.ntb._icon(os.path.join(program_folder, "information.png")), 'About',
                self.helpAbout)
        a.setToolTip('About')

        self.canvas.fig.canvas.mpl_connect('draw_event', self.update_limits)
          
                                            
        # create a vertical box layout
        self.vbl = QtGui.QVBoxLayout()
        
        # add widgets to the vertical box
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.ntb)
                                                             
        # set the layout to the vertical box
        self.setLayout(self.vbl)
        
        
    def onclick(self, event): 
        """
        Emit a signal to induce the update of source point location.
        
        @param event: press event.
        @type event: Matplotlib event.
        """  
                
        global set_srcpt_count, cid
        
        set_srcpt_count += 1
        
        if set_srcpt_count == 1:             
            self.canvas.emit( QtCore.SIGNAL("map_press"), (event.xdata, event.ydata) )
            
        self.canvas.fig.canvas.mpl_disconnect(cid)
 
        
                
    def pt_map(self):
        """
        Connect the press event with the function for updating the source point location.
        
        """ 
               
        global set_srcpt_count, cid            
        set_srcpt_count = 0        
        cid = self.canvas.fig.canvas.mpl_connect('button_press_event', self.onclick)
    
                
    def zoom2fullextent(self):
        """
        Emit the signal for updating the map view to the extent of the DEM, in alternative of
        the shapefile, or at the standard extent.
        
        """
        
        self.canvas.emit( QtCore.SIGNAL("zoom_to_full_view") )
 
 
    def update_limits(self, *args):

        x_limits = self.canvas.ax.get_xlim()
        y_limits = self.canvas.ax.get_ylim()  
 
        # QtGui.QMessageBox.information( self, "x_limits", str( x_limits[0]) + " " + str( x_limits[1]) ) 
        
        self.canvas.emit( QtCore.SIGNAL("updated_limits"), ( x_limits, y_limits ) )
          
        
    # after CADTOOLS module in QG     
    def openHelp(self):
        """
        Open an Help HTML file
        
        """
        
        help_path = os.path.join(os.path.dirname(__file__), 'help', 'help.html')         
        webbrowser.open(help_path)          

            
    def helpAbout(self):
        """
        Visualize an About window.
        """
        
        QtGui.QMessageBox.about(self, "About qgSurf", 
        """
            <p>qgSurf version 0.1.3<br />2012-10-7<br />License: GPL v. 3</p>
            <p>Mauro Alberti, <a href="http://www.malg.eu">www.malg.eu</a></p> 
            <p>This application calculates the intersection between a plane and a DEM in an interactive way.
            The result is a set of points/lines that can be saved as shapefiles.
            
            </p>
             <p>Created with Python 2.7 in Eclipse/PyDev.</p>
             <p>Tested in QuantumGIS 1.8.0 - Ubuntu 12.04 and Windows Vista </p>
             <p>Please report any bug to <a href="mailto:alberti.m65@gmail.com">alberti.m65@gmail.com</a></p>
        """)              
            
                  
        
