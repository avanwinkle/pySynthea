# A GUI Program

# -------- Current ----------------------
version = "0.3.9"  

# -------- Changelog --------------------
# 0.3.9 - Exported config parsing to layout file
# 0.3.8 - Renamed from gui to synth_board; Added testmode selection from main window checkbox
# 0.3.7 - Removed wx.App calls for spawning within parent process (Synthea.py)
# 0.3.6 - Encapsulated globals in a Master class for modular portability
# 0.3.5 - Consolidated global hotkey events into single dictionary iterator; added titlebar icon; general code cleanup and documentation
# 0.3.4 - Moved crew hotkeys to hotkeys.txt; moved quickreference popup content to quickreference.txt; added dynamic F1-F12 counting; general code cleanup
# 0.3.3 - Added music support; added fadeouts for channel stoppage; added fadeout for individual FX buttons; fixed dialog overlap bug; added window dimensions to config file
# 0.3.2 - Fixed indexerror bug on random files due to toggle; implemented project subfolder structures; added soundboard type support
# 0.3.1 - Added support for external hotkey file; added random file playback; added modifier keys for crew names; added this changelog
# 0.3.0 - Improved hotkey support; improved playback/queue/cancel functions
# 0.2.9 - Created a separate class for MasterQueue; added support for fast-switching modes;
# 0.2.8 - Added quick-reference dialogue; added hotkeys for crew members; improved layout parsing and order preservation
# 0.2.7 - Imported pygame and added basic audio support
# 0.2.6 - Added support for storing and parsing a queue via toggle-switch
# 0.2.5 - 'Notebook'-style layout; global keyboard events via Accelerometer table; preserved layout page orders
# 0.2.4 - Added keyboard binding; column/button loading from external file
# 0.2.3 - Build an original GUI from scratch in wxPython
# 0.2.1 - Move TKinter GUI elements to wxPython
# 0.2.0 - "Hello world" in wxPython
# 0.1.9 - General cleanup
# 0.1.8 - Added pygame support for audio; added mode toggle for source folder switching
# 0.1.7 - Added tkSound support for audio;
# 0.1.6 - Redesigned frame/button storage as persistent arrays
# 0.1.5 - Builds a button array from an external layout configuration file
# 0.1.4 - Added class definitions and methods for lists of buttons and frames
# 0.1.3 - Added support for a lock toggle; added queue logging
# 0.1.2 - Added hotkey support for toggle and page navigation
# 0.1.1 - Basic Tkinter window/frame layouts; added StaticText elements
# 0.1.0 - "Hello world" in Tkinter

import wx
# Import the sys module for arguments
import sys
sys.path.append("Resources")
# The fourth version of gui import includes numerous sorting and other improvements
import synth_layout_0_6 as synth_layout
# The game module that provides our audio interface
import pygame
# Import the random module for randomizing variable sound sources
import random


# --------------------------------------------------------
# The main Window!
# --------------------------------------------------------
class MyFrame(wx.Frame):

    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self,parent,ID,title, size=master.config["default_window"])

        # Set some starting conditions and variables
        self.locked = False     
        self.paused = False
        self.modes = master.config["modes"]
        self.mode = -1
        self.master_queue = MasterQueue()
        # A dictionary of all buttons, for easy access!
        self.master_buttons = {}
        if master.config.has_key("crashnoise"):
            if master.config["crashnoise"] == None:
                self.staticnoise = False
            else:
                self.staticnoise = pygame.mixer.Sound(master.projectroot+"/"+master.config["crashnoise"])
        # If no crash noise is specificed, use the default static
        else:
            self.staticnoise = pygame.mixer.Sound("Resources/static.wav")

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
        
        ###--- Define some universal hotkeys ---###
        ###########################################
        self.global_events = {}
        self.global_events[wx.WXK_ESCAPE] = "self.cancel()"
        self.global_events[wx.WXK_SPACE] = "self.toggle()"
        self.global_events[wx.WXK_RIGHT] = "self.pageadvance(True)"
        self.global_events[wx.WXK_LEFT] = "self.pageadvance(False)"
        self.global_events[wx.WXK_DELETE] = "self.cancel()"
        self.global_events[wx.WXK_BACK] = "self.cancel(True)"
        self.global_events[wx.WXK_PAUSE] = "self.pause()"
        self.global_events[wx.WXK_TAB] = "self.changeMode()"
        # Store the keycodes for the top-row numbers F1-F11
        for i in range(340,350):
            self.global_events[i] = "self.pagejump("+str(i-339)+")"
        # A special condition for F12 behaviour
        if master.config["quickreference"]:
            self.global_events[wx.WXK_F12] = "dialog = QuickReference(self)"
        else:
            self.global_events[wx.WXK_F12] = "self.pagejump(12)"
        # Add any events to capture from the project hotkeys file
        for hotkey in master.layout_hotkeys:
            # Convert the hotkey value into an int and then string, to prevent malicious code execution
            self.global_events[hotkey] = "self.master_buttons[master.layout_hotkeys["+str(int(hotkey))+"]].queue()"

        # Create an Id, a Bind, and a 3-item tuple for each keyboard event
        for eventname in self.global_events:
            # A routine to pass the event keycode to the parse function
            def passKeyCode(event):
                type = event.GetId()
                # Cannot call exec inside a nested function, so jump outside to call it
                self.parseEvent(type)
            # Bind the event handler to its special routine
            self.Bind(wx.EVT_MENU, passKeyCode)
            # Store the event handler to the accelerator table instruction list
            shortcut_table.append( (wx.ACCEL_NORMAL, eventname, eventname) )
            # Add qualifiers for CONTROL (add 1000) and ALT (add 2000)
            shortcut_table.append( (wx.ACCEL_CTRL, eventname, eventname + 1000) )
            shortcut_table.append( (wx.ACCEL_ALT, eventname, eventname + 2000) )
        
        # Create an accelerator table from the list of tuples
        shortcuts = wx.AcceleratorTable(shortcut_table)
        # Give the accelerator table global scope in the program
        self.SetAcceleratorTable(shortcuts)
                
        # Create a titlebar icon
        ib = wx.IconBundle()
        ib.AddIconFromFile("Resources/synthea.ico",wx.BITMAP_TYPE_ANY)
        self.SetIcons(ib)

        # Calculate and render the layout
        self.SetAutoLayout(True)
        self.SetSizer(masterbox)
        self.Layout()
        
                
    # This sets some startup conditions
    def initialize(self):
        # Set our default mode
        self.changeMode()
        # Set our default status bar value
        self.master_queue.ShowStatus()
        
    # This is the event handler, specially designed to accept the key codes and execute their functions
    def parseEvent(self,type):
        if type in self.global_events:
            exec(self.global_events[type])
      
    # A method to control the "mode" of the sound by changing source directories
    def changeMode(self):
        # A basic loop cycle, add one until we reach the end, then reset to zero
        if self.mode+1 < len(self.modes):
            self.mode += 1
        else:
            self.mode = 0
        # Link through all the nested pages, panels, and buttons
        for page in self.contentPanel.pages:
            for group in page.groups:
                for button in group.buttons:
                    # Instruct each button to load a new sound file
                    button.loadmode()
        # Update the status bar with the current mode
        self.statusBar.SetStatusText("["+master.config["type"].upper()+"]  "+self.modes[self.mode].upper(), 1)
            
        
    # A method to advance notebook pages: true for right, false for left
    def pageadvance(self,adv=True):
        self.contentPanel.AdvanceSelection(adv)
        
    # A method to jump to a specific notebook page
    def pagejump(self,pagenum):
        if pagenum <= len(self.contentPanel):
            self.contentPanel.ChangeSelection(pagenum-1)
        
    # A way to cutoff any play and, optionally, make static noise
    def cancel(self,interrupt=False):
        # Stop anything that's playing, with a hard cut for dialog and a 1s fadeout for sfx/music
        if master.config["type"] == "dialog":
            pygame.mixer.stop()
        else:
            pygame.mixer.fadeout(1000)
        # Call the queue's own cancellation method
        self.master_queue.Cancel()
        # If cancel is called while locked, clear the lock
        if self.locked:
            self.toggle()
        # If cancel was called by DEL and not locked, insert some static
        elif interrupt and self.staticnoise:
            self.staticnoise.play()

    # A method to pause globally
    def pause(self):
        # The pause button will only perform if the mixer is working
        if pygame.mixer.get_busy():
            if self.paused: 
                pygame.mixer.unpause()
                self.paused = False
            else:
                pygame.mixer.pause()
                self.paused = True
            
        
    # A method to toggle the lock status
    def toggle(self,evt=False):
        # Tell the footer to change its color and text as necessary
        self.footerPanel.toggle(self.locked)
        # If locked, unlock
        if self.locked:
            self.locked = False
            if self.master_queue:
                self.master_queue.Play()
        # If unlocked, lock
        elif not self.locked:
            self.locked = True
            

        
# --------------------------------------------------------
#  This is the master queue, for adding and playing
# --------------------------------------------------------
class MasterQueue():

    def __init__(self):
        # Create a list to contain everything
        self.queue = []
        
    # This method adds/removes items from the queue
    def Queue(self, item):
        if item in self.queue:
            self.queue.remove(item)
        else:
            self.queue.append(item)
        self.ShowStatus()
        # If something is added to the queue and we're not locked, play it immediately
        if self.queue and not master.frame.locked:
            self.Play()
            
    # Update the status bar
    def ShowStatus(self):
        if self.queue:
            queuelist = []
            for item in self.queue:
                queuelist.append(item.GetLabel())
            master.frame.statusBar.SetStatusText(" ".join(queuelist), 0)
        else:
            master.frame.statusBar.SetStatusText(" -- no queue  --", 0)
            
    # A method to clear the queue, whether playing all the files queued or not
    def Play(self):
        ''' This method doesn't loop itself; instead, it plays and then 'queues' the first item in the queue '''
        # If music is chosen and music exists, fadeout the mixer for a nice transition
        if master.config["type"] == "music":
            pygame.mixer.fadeout(2000)
        # Play (only) the first item in the queue
        self.queue[0].play()
        # Use this class' remove method
        self.Queue(self.queue[0])
        ''' The Queue method removes the existing item and continues play, thus creating our loop! '''

        
    # A method to clear the queue without playing any files
    def Cancel(self):
        # Run each queued file's clear method to reset appearance
        for queuedfile in self.queue:
            queuedfile.clear()
        # Set a null queue list
        self.queue = []
        # Reset the status bar
        self.ShowStatus()

        
    # Return a boolean value for whether there are items in the queue
    def __nonzero__(self):
        if self.queue:
            return True
        else:
            return False
        
        
# --------------------------------------------------------        
# This panel is the title bar atop the screen
# --------------------------------------------------------
class TitlePanel(wx.Panel):

    def __init__(self,parent,ID):
        wx.Panel.__init__(self,parent,ID)
        
        # Create a text object for the graphic title    
        titleText = wx.StaticText(self, -1, master.prog_version+" - "+master.config["name"])
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

        
# --------------------------------------------------------        
# This panel is the NOTEBOOK section, holding content
# --------------------------------------------------------
class ContentNotebook(wx.Notebook):

    def __init__(self, parent, id):
        # Initialize all the notebook properties
        wx.Notebook.__init__(self,parent,id,style=wx.BK_DEFAULT)
        # Create a list to contain the Panel objects for each page
        self.pages = []
        # Use the layout_order list, which is the order-preserved list from synth_layout_2
        for group in master.layout_raw:
            # Generate a wx.Panel object using the dictionary value paired to the page name
            page = ContentPage(self, -1, group[1])
            # If the page number is 12 or less, give it a hotkey (maybe)
            hotstring = ""
            if len(self.pages) <= 11:
                # Maximum of 11 pages get hotkeys unless there's no quickreference file, in which case 12
                if len(self.pages) <= 10 or not master.config["quickreference"]:
                    hotstring = "F"+str(len(self.pages)+1)+" - "
            # Add the panel object as a new "page" in the notebook
            self.AddPage(page, hotstring+group[0])
            self.pages.append(page)
        
    def __len__(self):
        return len(self.pages)

        
# --------------------------------------------------------        
# This panel is a "page" of the notebook, which is placed in ContentPanel and contains ContentGroups
# --------------------------------------------------------
class ContentPage(wx.Panel):

    def __init__(self,parent,ID,page):
        # Initialize a default panel object
        wx.Panel.__init__(self,parent,ID)
                
        # Create a list of each child column, which will contain a group of buttons
        self.groups = []
        for column in page:
            # Generate the child object that is a group of buttons
            self.groups.append(ContentGroup(self,-1,column[0],column[1]))
        
        # Create an external sizer that places vertically, for horizontal centering
        outerbox = wx.BoxSizer(wx.VERTICAL)
        # Create an internal sizer that places horizontally, for vertical centering
        innerbox = wx.BoxSizer(wx.HORIZONTAL)
        # Mount each group of buttons in the internal sizer
        for group in self.groups:
            # No relative scaling, align top, 5-pixel border on all sides
            innerbox.Add(group, 0, wx.ALIGN_TOP|wx.ALL, 5)
        # Mount the internal sizer in the external sizer
        outerbox.Add(innerbox, 0, wx.ALIGN_CENTER)
        
        # Run the layout rendering
        self.SetAutoLayout(True)
        self.SetSizer(outerbox)
        self.Layout()   
 

        
# --------------------------------------------------------    
# This panel is a subsection of the main section, contains a group of content
# --------------------------------------------------------
class ContentGroup(wx.Panel):

    def __init__(self, parent, ID,name,column):
        wx.Panel.__init__(self,parent,ID,size=(-1,400))
        
        # Create a static box to contain the list of buttons
        static = wx.StaticBox(self)
        # Create a sizer for the static box, stacking buttons vertically
        staticbox = wx.StaticBoxSizer(static, wx.VERTICAL)
        # Create a title text, because we have more control than using the static box built-in title
        title = wx.StaticText(self, -1, name)
        # Mount the title text in the box sizer
        staticbox.Add(title, 0, wx.ALIGN_CENTER|wx.BOTTOM, 10)
        
        self.buttons = []
        # Progagate the box contents
        for tag in column:
            # Create a button object for each designation in the layout
            button = FX_Button(self, -1, tag[0], tag[1], tag[2])
            # Create an event handler for the pushing of this button
            self.Bind(wx.EVT_TOGGLEBUTTON, button.queue, button)
            # Mount the button in the box sizer
            staticbox.Add(button, 0, wx.EXPAND|wx.ALL, 12)
            # Track the button
            self.buttons.append(button)
        
        # Create an external box sizer to contain the static box
        enclosure = wx.BoxSizer(wx.VERTICAL)
        # Mount the static box in the external box
        enclosure.Add(staticbox, 0)
        self.SetSizer(enclosure)


# --------------------------------------------------------        
# A custom class for the effects buttons
# --------------------------------------------------------
class FX_Button(wx.ToggleButton):

    def __init__(self, parent, ID, name,src,loop=False):
        wx.ToggleButton.__init__(self,parent,ID,name, size=(-1,30))
        self.name = name
        # Store a value whether the sound is playing
        self.channel = False
        # A list of source files
        self.src = src
        if loop:
            self.loop = -1
        else: 
            self.loop = 0

    # This method loads a sound file from the mode subdirectory
    def loadmode(self):
        # A list of the source soundfile objects, cleared of all previous files
        self.sounds = []
        # Loop through any sourcefiles provided from the layout file
        for source in self.src:
            # Store the pathname of the sourcefile based on the current "mode"
            soundfile = master.projectroot+master.frame.modes[master.frame.mode]+"/"+source
            # Create a pygame sound object to cache the sound in memory
            sound = pygame.mixer.Sound(soundfile)
            # Store the sound object in this parent object's list of sounds
            self.sounds.append(sound)
        # Store a pointer back to this button, by way of dictionary, so it can be called by hotkeys
        master.frame.master_buttons[self.name] = self
        
    # This method queues up a sound for playing (regardless of whether the queue is "locked")
    def queue(self,event=False):
        # The MasterQueue object handles redundancy and playback
        master.frame.master_queue.Queue(self)

    # This method actually plays the track!
    def play(self):
        # Default to playing
        dontplay = False
        
        #### Define some unique behaviours depending on what mode we're using ####
        #------------------------------------------------------------------------#
        # DIALOG MODE: Don't overlap! Wait for the channel to clear!
        if master.config["type"] == "dialog":
            while pygame.mixer.get_busy():
                continue
        # MUSIC MODE: Only one song at a time, fade the existing music out first!
        elif master.config["type"] == "music":
            if pygame.mixer.get_busy():
                pygame.mixer.fadeout(2000)                
        # SFX MODE: If this is already playing, fade it (and only it) out!
        elif master.config["type"] == "sfx" and self.channel:
            if self.channel.get_busy():
                self.channel.fadeout(2000)
                dontplay = True
        #------------------------------------------------------------------------#
                
        # Look for multiple versions to randomize
        if len(self.sounds) > 1:
            playnum = random.randint(0,len(self.sounds)-1)
        else:
            playnum = 0
        # Play the file, if applicable... basically, unless this file was already playing (SFX Mode)
        if not dontplay:
            # Variable behaviour, whether we want to actually play the file or just see that we could have (test mode)
            if not master.testmode:
                self.channel = self.sounds[playnum].play(loops=self.loop)
            else:
                print self.name + ": "+master.projectroot+master.frame.modes[master.frame.mode]+"/"+self.src[playnum]

        # Reset the appearance of the button
        self.clear()
        
    # This method just makes the button look unpressed
    def clear(self):
        self.SetValue(False)


# --------------------------------------------------------
# This panel is the footer, which displays the lock status
# --------------------------------------------------------
class FooterPanel(wx.Panel):

    def __init__(self,parent,ID):
        wx.Panel.__init__(self,parent,ID)
        
        # Create our status text
        self.footerText = wx.StaticText(self, -1, "UNLOCKED")
        # Create a box sizer to contain the text, centered horizontally
        footerbox = wx.BoxSizer(wx.VERTICAL)
        # Mount the footer text in the box
        footerbox.Add(self.footerText, 0, wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5)
        
        # Render the layout
        self.SetAutoLayout(True)
        self.SetSizer(footerbox)
        self.Layout()

    # A method to toggle the display of the footer
    def toggle(self,locked):
        # If the boolean says that we're currently locked...
        if locked:
            self.SetBackgroundColour("")
            self.footerText.SetForegroundColour("")
            self.footerText.SetLabel("UNLOCKED")
        # Otherwise, assume we're unlocked
        else:
            self.SetBackgroundColour("RED")
            self.footerText.SetForegroundColour("white")
            self.footerText.SetLabel("LOCKED")
        # Refresh the rendering to show the changes
        self.Refresh()
     

     
# --------------------------------------------------------
# A dialogue for the hotkey shortcuts
# --------------------------------------------------------
class QuickReference(wx.MessageDialog):
    
    def __init__(self,parent):
    
        # Build a Dialog object based on the contents of the quickreference file
        wx.MessageDialog.__init__(self, parent, master.config["quickreference"], "Quick Reference",wx.CANCEL)
        # Show it!
        self.ShowModal()
        # Destroy it!
        self.Destroy()
  
  
        

# **************************************** #
# The MAIN FUNCTION                        #
#   ...This is not in a main() function,   #
#   because these all need to be globals   #
# **************************************** #


class Master:

    def __init__(self,projectroot,testmode=False):
        
        self.projectroot = projectroot
        # ---- Global Variables Here ---- #
        # A default folder for testing, no slashes
        self.testmode = testmode
        # Set the program title
        if self.testmode:
            testflag = " [TEST MODE]"
        else:
            testflag = ""
        self.prog_version = "Synthea "+version+testflag
        

        # Initialize the mixer
        pygame.mixer.init()

    def layout(self):
        # Load the project's configuration file
        self.config = synth_layout.loadConfig(self.projectroot)
        # Import the project's layout data, which is now all order-preserved lists
        self.layout_raw = synth_layout.loadLayout(self.projectroot)
        self.layout_hotkeys = synth_layout.loadHotkeys(self.projectroot)
        
    def render(self):
        # Create the master window
        self.frame = MyFrame(None, -1, self.prog_version)
        # Run some startup functions to set initial values
        self.frame.initialize()
        # Render the master window
        self.frame.Show()

def createMaster(projectsource,testmode=False):
    global master
    master = Master(projectsource,testmode)
    master.layout()
    master.render()
    
    
if __name__ == "__main__":
    createMaster("Projects\\MUSIC\\")