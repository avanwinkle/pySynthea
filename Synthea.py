#!/usr/bin/python
##########################################
##  ---   SYNTHEA PROJECT LOADER   ---  ##
## ____________________________________ ##

#-------------------------------------------------------------#
#  This function loads all project directories and presents   #
#  the user with a list from which to choose. Once chosen,    #
#  this function's own Panel is destroyed and replaced with   #
#  the MainPanel from the primary operating program.          #
#-------------------------------------------------------------#

# ... For the complete changelog, see the latest synth_board.py

# import some basic IO modules
import sys, os
# import the wx module for GUI rendering
import wx
# set a special path for module loading
sys.path.append("Resources")
# load the latest version of the gui module
import synth_board_0_4_3 as synth_board

# Do we include a checkbox to toggle test mode?
enabletestmode = True

# *********
# This Class defines the main frame of the selection window
# -----------------

class ProjectFrame(wx.Frame):

    def __init__(self,parent,ID,title):
        # Start with the standard window init
        wx.Frame.__init__(self,parent,ID,title)
        self.testmode = False
        # Create a title panel and a content panel
        self.titlePanel = TitlePanel(self,-1)
        self.content = ContentPage(self,-1)
        # Create a box sizer to contain the title and content
        masterbox = wx.BoxSizer(wx.VERTICAL)
        masterbox.Add(self.titlePanel, 0, wx.EXPAND)
        masterbox.Add(self.content, 4, wx.EXPAND|wx.ALIGN_TOP)
        
        # Create a status bar!
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(2)
        self.statusBar.SetStatusWidths([-1,140])
        self.SetStatusBar(self.statusBar)
        self.statusBar.SetStatusText("Synthea Engine "+synth_board.version, 1)
       
        # Create a titlebar icon
        if sys.platform == "win32":
            self.iconset = wx.IconBundle()
            self.iconset.AddIconFromFile("Resources\synthea.ico",wx.BITMAP_TYPE_ANY)
            self.SetIcons(self.iconset)
            FileMenu = wx.Menu()
            item = FileMenu.Append(wx.ID_EXIT, text="&Quit")
            self.Bind(wx.EVT_MENU, self.OnCloseWindow, item)
            self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        # Some menus
        if sys.platform == "darwin":
            MenuBar = wx.MenuBar()
            FileMenu = wx.Menu()
            item = FileMenu.Append(wx.ID_EXIT, text="&Quit")
            self.Bind(wx.EVT_MENU, self.OnCloseWindow, item)
            MenuBar.Append(FileMenu, "&Synthea")
            
            self.SetMenuBar(MenuBar)
            self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        masterbox.Fit(self)
        # Calculate and render the layout
        self.SetAutoLayout(True)
        self.SetSizer(masterbox)
        self.Layout()

	# Proper closure for OSX
    def OnCloseWindow(self,Event):
        #self.Close()
        self.Destroy()
        
# *********
# This Class defines the selection window title text
# -----------------

class TitlePanel(wx.Panel):

    def __init__(self,parent,ID):
        wx.Panel.__init__(self,parent,ID)
        
        # Create a text object for the graphic title    
        titleText = wx.StaticText(self, -1, "Synthea Project Loader")
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
        
# *********
# This Class defines the content frame, which holds the buttons
# -----------------

class ContentPage(wx.Panel):

    def __init__(self,parent,ID):
        # Initialize a default panel object
        wx.Panel.__init__(self,parent,ID)
        # Add some descriptive text to instruct the user
        self.title = wx.StaticText(self, -1, "Please select a project file to open.")
                
        # Store a list of all the buttons
        self.projects = []
        # Read through the Projects folder looking for projects
        for folder in os.listdir("Projects"):
            # Exception catching is useful, since we don't know what's in the Projects folder
            try:
                # Attempt to open the config file
                f = open("Projects/"+folder+"/Config.txt")
                # Read the config file to find the name
                for line in f.readlines():
                    if line.split(":")[0] == "name":
                        # Parse the long title of the project
                        title = line.split(":")[1].strip()
                # Generate the button for that project file
                project = PJ_Button(self,-1,title,folder)
                # Set an event handler for the clicking of the button
                self.Bind(wx.EVT_TOGGLEBUTTON, project.open, project)
                # Add that button to the list of buttons
                self.projects.append(project)
            except:
                continue
                
        aboutb = wx.Button(self, -1, "About Synthea", (50,50))
        self.Bind(wx.EVT_BUTTON, self.aboutSynthea, aboutb)
        
		# We're pretty stable now, so no test mode unless manually defined
        if enabletestmode:
            testm = wx.CheckBox(self, -1, "TEST MODE")
            self.Bind(wx.EVT_CHECKBOX, self.testtoggle, testm)
          
        # Create an external sizer that places vertically, for horizontal centering
        outerbox = wx.BoxSizer(wx.VERTICAL)
        # Create an internal sizer that places vertically, for horizontal centering
        innerbox = wx.BoxSizer(wx.VERTICAL)
        # Add the text
        outerbox.Add(self.title, 0, wx.ALIGN_CENTER|wx.ALL, 10)
        # Mount each group of buttons in the internal sizer
        for project in self.projects:
            # No relative scaling, align top, 5-pixel border on all sides
            innerbox.Add(project, 0, wx.ALIGN_CENTER|wx.ALL, 15)
        # Mount the internal sizer in the external sizer
        outerbox.Add(innerbox, 0, wx.ALIGN_CENTER)
        outerbox.Add( wx.StaticText(self,-1,"-------------------------"),0,wx.ALIGN_CENTER)
        outerbox.Add(aboutb,0,wx.ALIGN_CENTER|wx.ALL,15)
        if enabletestmode:
			outerbox.Add(testm,0,wx.ALIGN_CENTER|wx.ALL,10)
      

        # Run the layout rendering
        self.SetAutoLayout(True)
        self.SetSizer(outerbox)
        self.Layout()   
        
    def aboutSynthea(self,evt):
        info = wx.AboutDialogInfo()
        info.Name = "Synthea"
        info.Version = synth_board.version+"\n"
        info.Description = "\nSynthea, short for SYNthetic THEater Audio, is a realtime audio playback system designed for improvised theater. It was first written by Anthony van Winkle for the unscripted play FINAL TRANSMISSION in the summer of 2011."
        info.Description += "\n\nThis program relies on project subfolders stored in its \'Projects\' subdirectory; the Project Loader you are currently using reads these subfolders to offer a list of valid projects. Choose one to load that project's soundboard."
        info.Description += "\n\nEach project file has a Config file that defines its name, type (dialog, sound effects, or music), and its optional playback modes. The types are distinguished by the following characteristics:"
        info.Description += "\n\n   DIALOG: Concurrent cues are queued and played back sequentially"
        info.Description += "\n   EFFECTS: Concurrent cues are played simultaneously"
        info.Description += "\n   MUSIC: New cues fade in as the previous cue is faded out"
        info.Description += "\n\nAdditionally, each project configuration file can declare multiple 'modes', which are subdirectories that contain mirrors of all the cue files. These modes allow on-the-fly switching between audio sets while maintaining the project's board layout."
        info.Description += "\n\nEach project folder also contains a Layout file, which is a delimited text file that defines the hierarchy of pages, groups, effects buttons, and cue files for that soundboard. Multiple cue files can be assigned to the same button; in such cases, a random file will be selected each time the button is queued."
        info.Description += "\n\nFinally, each project has an optional Hotkeys file, where global keyboard events can be programmed. These events will override the built-in hotkeys, and are a simple delimited list of keyboard event codes (triggers) and effect button names (actions)."
        info.Copyright = "(C) 2011-2012 Anthony van Winkle\n"
        wx.AboutBox(info)
        
    def testtoggle(self,evt):
        if evt.IsChecked():
            loadframe.testmode = True
        else:
            loadframe.testmode = False
 
# *********
# This Class defines the buttons, each linking back to a project directory
# -----------------

class PJ_Button(wx.ToggleButton):

    def __init__(self, parent, ID, name,path):
        # Create a normal button named after the long name
        wx.ToggleButton.__init__(self,parent,ID,name, size=(-1,30))
        # Remember the path submitted with this button
        self.path = path
        
    # This method actually loads the project file
    def open(self,evt):
        loadframe.statusBar.SetStatusText("Loading project directory '"+self.path+"'...", 0)
        # Store the test mode before we destroy the frame
        testmode = loadframe.testmode
        # Remove the current master Frame in wx.App
        loadframe.Destroy()
        # Close the app because we're going to open a new one
        #loadapp.ExitMainLoop()
        # Call the synth_board master Frame method, which will create a now master Frame object
        # using the project file data found in the given path
        synth_board.createMaster("Projects/"+self.path+"/",testmode)

        loadapp.Destroy()
        loadapp.Exit()
        
        

def main():

    global loadapp, loadframe
    # Initialize the wx framework
    loadapp = wx.App(0)
    # OSX Features
    if sys.platform == "darwin":
        loadapp.SetAppName("Synthea")
        loadapp.SetAppDisplayName("Synthea")
    # Create a main Frame object
    loadframe = ProjectFrame(None, -1,"Synthea Loader")
    # Render the main Frame object
    loadframe.Show()
    # Wait for a captured event to handle
    loadapp.MainLoop()

if __name__ == "__main__":
    print sys.argv
    # We can pass a project as a command line variable!
    if len(sys.argv) > 1:
        try:
            synth_board.createMaster("Projects/%s/" % sys.argv[1],False)
        except(IOError):
            main()
    else:
        main()