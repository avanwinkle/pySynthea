import synth_layout_0_5 as synth_layout
import wx


class Project:
    def __init__(self,projectroot="../Projects/SFX/"):
        # Load the project's configuration file
        self.config = synth_layout.loadConfig(projectroot)
        # Import the project's layout data, which is now all order-preserved lists
        self.layout_raw = synth_layout.loadLayout(projectroot)
        self.layout_hotkeys = synth_layout.loadHotkeys(projectroot)
    
# --------------------------------------------------------
# The main Window!
# --------------------------------------------------------
class MyFrame(wx.Frame):

    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self,parent,ID,title, size=master.config["default_window"])

        # Instantiate the major panels that divide the screen
        self.titlePanel = TitlePanel(self, -1)
        self.contentPanel = ContentNotebook(self, -1)
        self.footerPanel = FooterPanel(self, -1)

        # Create a status bar!
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(2)
        self.statusBar.SetStatusWidths([-1,140])
        self.SetStatusBar(self.statusBar)
        
        # Create the master sizer box to lay out the major panels        
        masterbox = wx.BoxSizer(wx.VERTICAL)
        masterbox.Add(self.titlePanel, 0, wx.EXPAND)
        masterbox.Add(self.contentPanel, 4, wx.EXPAND|wx.ALIGN_TOP)
        masterbox.Add(self.footerPanel, 0, wx.EXPAND)
        

        ## An "accelerator table" for global bindings
        # Create a table of event tuples for the accelerator table
        shortcut_table = []
    
        # Create a titlebar icon
        ib = wx.IconBundle()
        ib.AddIconFromFile("Resources\synthea.ico",wx.BITMAP_TYPE_ANY)
        self.SetIcons(ib)

        # Calculate and render the layout
        self.SetAutoLayout(True)
        self.SetSizer(masterbox)
        self.Layout()
        
# --------------------------------------------------------        
# This panel is the title bar atop the screen
# --------------------------------------------------------
class TitlePanel(wx.Panel):

    def __init__(self,parent,ID):
        wx.Panel.__init__(self,parent,ID)
        
        # Create a text object for the graphic title    
        titleText = wx.StaticText(self, -1, "Synthea Project Editor - "+master.config["name"])
        # Set some font properties to make it purdy
        titlefont = wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL)
        titleText.SetFont(titlefont)
        # Create a sizer to horizontally center the title text
        titlebox = wx.BoxSizer(wx.VERTICAL)
        # Mount the text object in the sizer with a 20-pixel border
        titlebox.Add(titleText, 0, wx.ALIGN_CENTER|wx.ALL, 20)
        
        # Run the layout rendering
        self.SetAutoLayout(True)
        self.SetSizer(titlebox)
        self.Layout()
        
                

    
if __name__ == "__main__":
    p = Project()
    print p.config
    
    