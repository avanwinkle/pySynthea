# A GUI Program

# -------- Current ----------------------
version = "0.4.5"

# -------- Changelog --------------------
# 0.4.5 - Added VLC support as playback audio handler
# 0.4.4 - Added override buffer value for SFX in music boards
# 0.4.3 - Added buffering and no-cache options, more crossfade options
# 0.4.2 - Fixed hotkey behaviour, added titlebar image
# 0.4.1 - Additions by Dan Posluns to support loop intros
# 0.4.0 - Support for custom/no crash sound; Improved OSX support, cross-platform
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

### HIGH-LEVEL IMPORTS
# WX is how we make our GUI elements
import wx
# Import os for path features
import os
# Import time so we can sleep
import time
# Import the sys module for arguments
import sys
# Pull from our customized resource folder
sys.path.append("Resources")

### FUNCTION-LEVEL IMPORTS
# The current version of gui import includes numerous sorting and other improvements
import synth_layout_0_92 as synth_layout
# The game module that provides our audio interface
import pygame
import vlc
# Import the random module for randomizing sound clips
import random
# Import numpy for creating the sound of silence (Posluns)
import numpy
# Import subprocess and re so we can query the system volume level
import subprocess, re

# For manual fadeouts, we need to sleep
import threading
import logging
logger = logging.getLogger(__name__)
logger.addHandler( logging.StreamHandler() )
logger.setLevel(logging.DEBUG)

BUFFERLOOP = False
DEFAULT_DEFER = 500

# Dan Posluns made a little loader status counter
displayLoadingProgress = True

# Define the hotkey actions
hotkeyFunctions = {
    "PLAY": "self.master_buttons[\"%s\"].queue()",
    "FADE_TIME": "self.setFadeTime(%s)",
    "FADE_IN": "self.setFadeTime(%s,0)",
    "FADE_OUT": "self.setFadeTime(%s,1)",
    "TOGGLE_CROSSFADE": "self.toggleCrossfadeEnabled()",
    "ENABLE_CROSSFADE": "self.setCrossfadeEnabled(True)",
    "DISABLE_CROSSFADE": "self.setCrossfadeEnabled(False)",
    "STOP_SOUND": "self.cancel(disableFade=True)",
}
# Define the hotkey modifiers
hotkeyModifiers = {
    "<ctrl>": wx.ACCEL_CTRL,
    "<alt>": wx.ACCEL_ALT,
    "<cmd>": wx.ACCEL_CMD,
    "<shift>": wx.ACCEL_SHIFT
}

# --------------------------------------------------------
# The main Window!
# --------------------------------------------------------
class MyFrame(wx.Frame):

    def __init__(self, parent, ID, title):
        wx.Frame.__init__(self,parent,ID,title, size=master.config["default_window"])

        # Set some starting conditions and variables
        self.locked = False
        self.paused = False
        self.musicpaused = False
        # Some inital values come from the config file
        self.modes = master.config["modes"]


        # A time-remaining timer
        self.timecounter = wx.Timer(self)
        self.timeremaining = 0
        self.Bind(wx.EVT_TIMER, self.timeRemaining, self.timecounter)

        self.mode = -1
        self.master_queue = MasterQueue(self)
        # A dictionary of all buttons, for easy access!
        self.master_buttons = {}
        # A default or custom (or no) crash noise
        if master.config.has_key("crashnoise"):
            if master.config["crashnoise"] == "none":
                self.staticnoise = False
            else:
                self.staticnoise = pygame.mixer.Sound(master.projectroot+"/"+master.config["crashnoise"])
        # If no crash noise is specificed, use the default static
        else:
            self.staticnoise = pygame.mixer.Sound("Resources/crashnoise.wav")

        # Instantiate the major panels that divide the screen
        self.titlePanel = TitlePanel(self, -1)
        self.contentPanel = ContentNotebook(self, -1)
        self.footerPanel = FooterPanel(self, -1)

        # Create a status bar!
        self.statusBar = wx.StatusBar(self, -1)
        # If we have multiple modes or DJ mode, include a status bar field for it
        if len(self.modes) > 1 or master.config["dj"]:
            self.statusBar.SetFieldsCount(6)
            self.statusBar.SetStatusWidths([-3,-3,-2,-2,-2,-2])
        else:
            self.statusBar.SetFieldsCount(5)
            self.statusBar.SetStatusWidths([-2,-2,-1,-1,-1])
        self.SetStatusBar(self.statusBar)
        self.updateFadeDisplay()



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

        # A master dictionary, which will do all lookups on keypress
        self.global_events = {}

        global_hotkeys = [
            # wx.ACCEL_NORMAL == 0, so no reason to lookup
            # SPACE will toggle the lock
            (0, wx.WXK_SPACE, "self.toggle()"),
            # LEFT and RIGHT will move from page to page
            (0, wx.WXK_RIGHT, "self.pageadvance(True)"),
            (0, wx.WXK_LEFT, "self.pageadvance(False)"),
            # PAUSE will pause the board with tuple args for (effects,music)
            #(0, wx.WXK_CAPITAL, "self.pause(True,False)"),
            (wx.ACCEL_SHIFT, wx.WXK_CAPITAL, "self.pause(False,True)"),
            (wx.ACCEL_CTRL|wx.ACCEL_SHIFT, wx.WXK_CAPITAL, "self.pause(True,True)"),
            # TAB will toggle the playback mode, i.e. the folder containing sound files
            (0, wx.WXK_CAPITAL, "self.changeMode"),
            # TAB will toggle the crossfade, +SHIFT for waittime, +CTRL to reset
            (0, wx.WXK_TAB, "self.toggleCrossfade(1)"),
            (wx.ACCEL_SHIFT, wx.WXK_TAB, "self.toggleCrossfade(0)"),
            (wx.ACCEL_CTRL, wx.WXK_TAB, "self.setCrossfadeEnabled()"),
            # BACKSPACE/DELETE will cancel the everything, with a fadeout
            (0, wx.WXK_BACK, "self.cancel(True,True)"),
            #(0, wx.WXK_DEL, "self.cancel(True,True)"),
            # SHIFT+BACKSPACE/DELETE will cancel the sound effects, with a fadeout
            (wx.ACCEL_SHIFT, wx.WXK_BACK, "self.cancel(True,False)"),
            # CTRL+SHIFT+BACKSPACE/DELETE will cancel the music, with a fadeout
            (wx.ACCEL_CTRL|wx.ACCEL_SHIFT, wx.WXK_BACK, "self.cancel(False,True)"),
            # ESCAPE will unceremoniously kill all sound, no fadeout
            (0, wx.WXK_ESCAPE, "self.cancel(True,True,False,True)"),
            ]

        # SHIFT-TAB will turn on and off DJ mode, if enabled by the config
        if master.config["dj"]:
            # SHIFT-CAPS will go into DJ mode, if we have it!
            global_hotkeys.append( (0, wx.WXK_F12, "self.playDj()") )
            self.djplay = []
            self.djtimer = wx.Timer(self)
            #self.djtimer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.playDj, self.djtimer)


        # Store the keycodes for the top-row numbers F1-F12
        for i in range(340,351):
            global_hotkeys.append( (0, i, "self.pagejump(%d)" % (i-339) ) )

        # A special condition for F12 behaviour, if a quickreference is defined
        if master.config["quickreference"]:
            # This will overwrite the above F12 behaviour
            global_hotkeys.append( (0,wx.WXK_F11, "dialog = QuickReference(self)") )

        for hotkey in global_hotkeys:
            # Store the combined modifier and keypress, using bitwise shift for convenience
            hotkeyID = hotkey[0]<<16|hotkey[1]
            # Store a dictionary with the modified keypress and the action
            self.global_events[hotkeyID] = hotkey[2]
            # Store an accelerator shortcut that includes the modifier
            shortcut_table.append( (hotkey[0], hotkey[1], hotkeyID) )

        # Set up generic hotkey event processing
        def passKeyCode(event):
            type = event.GetId()
            # Cannot call exec inside a nested function, so jump outside to call it
            self.parseEvent(type)
        self.Bind(wx.EVT_MENU, passKeyCode)

        # Add any events to capture from the project hotkeys file
        for hotkey in master.layout_hotkeys:
            # Gather the hotkey information
            modifiers = hotkey[0]
            key = ord(hotkey[1])
            fn = hotkeyFunctions[hotkey[2]]
            params = hotkey[3]
            # Determine key modifiers
            wxModifier = wx.ACCEL_NORMAL
            # With bitshifting we can combine the modifiers and remain unique
            for modifier in modifiers:
                wxModifier = wxModifier | hotkeyModifiers[modifier]
            # Build a hotkeyID as a combination of modifier(s) and the key itself
            hotkeyID = key | (wxModifier << 16)
            # Set the hotkey
            self.global_events[hotkeyID] = fn % params
            shortcut_table.append( (wxModifier, key, hotkeyID) )

        # Create an accelerator table from the list of tuples we just made
        shortcuts = wx.AcceleratorTable(shortcut_table)
        # Give the accelerator table global scope in the program
        self.SetAcceleratorTable(shortcuts)

        # Create a titlebar icon for the Windows platform
        if sys.platform == "win32":
            ib = wx.IconBundle()
            ib.AddIconFromFile("Resources/synthea_flat.ico",wx.BITMAP_TYPE_ANY)
            self.SetIcons(ib)
            self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        # Some menus based on the OSX platform
        if sys.platform == "darwin":
            MenuBar = wx.MenuBar()
            FileMenu = wx.Menu()

            litem = FileMenu.Append(wx.NewId(), "Reload Layout")
            self.Bind(wx.EVT_MENU, self.reloadLayout, litem)

            qitem = FileMenu.Append(wx.ID_EXIT, text="&Quit")
            self.Bind(wx.EVT_MENU, self.OnCloseWindow, qitem)

            MenuBar.Append(FileMenu, "&Synthea")

            self.Bind(wx.EVT_MENU, self.reloadLayout, litem)
            self.Bind(wx.EVT_MENU, self.OnCloseWindow, qitem)
            self.SetMenuBar(MenuBar)


            self.SetMenuBar(MenuBar)
            self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

            # Fetch the volume level if we want to check it, only for OSX right now
            if master.config.has_key("volume"):
                self.sysVol = False
                sysvol = subprocess.check_output('osascript -e "get volume settings"',shell=True).strip()
                # Split it up and find what we want ("output volume:13, input volume:100, alert volume:100, output muted:false")
                for volume in map(lambda x: x.groups(),re.finditer("([^:]*):([^,]*),? ?",sysvol)):
                    if volume[0] == "output volume":
                        self.sysVol = volume[1]
                    # No else, so this will overwrite in case the order is unexpected
                    if volume[0] == "output muted" and volume[1] == "true":
                        self.sysVol = "MUTED"
                # See where we are, and raise a dialogue warning
                if self.sysVol == "MUTED" or int(self.sysVol) != int(master.config["volume"]):
                    if VolumeWarning(self, (self.sysVol, master.config["volume"])):
                        # If the warning box returns true, change the system volume to the target
                        subprocess.check_output('osascript -e "set volume output volume %s"' % master.config["volume"], shell=True)

        # Calculate and render the layout
        self.SetAutoLayout(True)
        self.SetSizer(masterbox)
        self.Layout()

    # Proper closure
    def OnCloseWindow(self,Event):
        # Stop the noise!
        pygame.mixer.stop()
        pygame.quit()

        # If we have a timer, shut it down
        if master.config["dj"] and self.djtimer.IsRunning():
        	self.djtimer.Stop()
        if self.timecounter.IsRunning():
        	self.timecounter.Stop()

        # Exit the app
        newapp.Exit()
        # Remove the frame ?
        self.Destroy()
        sys.exit()

    def reloadLayout(self,Event):
        logger.debug("Reloading layout!")
        master.reload()


    # This sets some startup conditions
    def initialize(self):
        # Set our default mode by forcing the changemode with an argument
        self.changeMode(True)
        # Set our default status bar value
        self.master_queue.ShowStatus()

    # This is the event handler, specially designed to accept the key codes and execute their functions
    def parseEvent(self,evttype):
        # Of course, only execute if there's an event that matches the key code
        if evttype in self.global_events.keys():
            # Under testmode, logger.debug(to the console what's happening)
            if master.testmode:
                logger.debug("Activating: ",)
                logger.debug(self.global_events[evttype])
            exec(self.global_events[evttype])

    # Change the crossfade mode
    def setCrossfadeEnabled(self, enabled):
       # master.crossfade = enabled
        logger.debug("Current crossfade: ",)
        logger.debug(master.crossfade)
        master.crossfade = [enabled,enabled]
        logger.debug("Set crossfade: ",)
        logger.debug(master.crossfade)
        self.updateFadeDisplay()

    def toggleCrossfade(self, method):
        # We can toggle either the 0 or the 1, depending
        master.crossfade[method] = not master.crossfade[method]
        logger.debug("New crossfade: ",)
        logger.debug(master.crossfade)
        self.updateFadeDisplay()

    # Change the fade speed
    def setFadeTime(self, time, method=2):
        if method == 2:
            master.fadetime = [ int(time * 1000), int(time * 1000) ]
        else:
            master.fadetime[method] = int(time * 1000)
        self.updateFadeDisplay()

    # This updates the status bar display of our fade settings
    def updateFadeDisplay(self):
        if master.fadetime[0] == master.fadetime[1]:
            self.statusBar.SetStatusText("Fade Time: %g sec" % (float(master.fadetime[0]) / 1000), 3)
        else:
            self.statusBar.SetStatusText("Fade In/Out: %g sec / %g sec" % ( float(master.fadetime[0])/1000, float(master.fadetime[1])/1000), 3)
        cross = "Cross" if master.crossfade[0] else "Wait"
        fade = "Fade" if master.crossfade[1] else "Full"
        self.statusBar.SetStatusText("%s-%s " % (cross,fade), 4)

	# This sets a time-remaining counter
    def timeRemaining(self,event=False):

        self.timeremaining = self.timeremaining - 1

         # Make sure we're really done?
        if self.timeremaining <= 0 and not pygame.mixer.get_busy():
        	# Stop the timer
            self.timecounter.Stop()
            self.statusBar.SetStatusText("",1)
            # Clear the "Now Playing"
            self.statusBar.SetStatusText("",2)
        else:
        	# Update the timer
            self.statusBar.SetStatusText("Remaining: %d:%.2d" % (self.timeremaining/60,self.timeremaining%60), 2)




    # A method to control the "mode" of the sound by changing source directories
    def changeMode(self, firstrun=False):
        # Store a list of our button objects, for later use (e.g. garbage collection)
        self.buttons = []
        # Save the compute cycles if there's no mode to change
        if len(self.modes) > 1 or firstrun:
            # A basic loop cycle, add one until we reach the end, then reset to zero
            if self.mode+1 < len(self.modes):
                self.mode += 1
            else:
                self.mode = 0
            # Link through all the nested pages, panels, and buttons
            for page in self.contentPanel.pages:
                for group in page.groups:
                    for button in group.buttons:
                        # Show where we are so far
                        if displayLoadingProgress or master.testmode:
                            logger.debug("%d%%: %s" % (int(float(master.totalLoaded * 100) / master.totalSounds), ", ".join(button.src) ))
                        # Instruct each button to load a new sound file
                        button.loadmode()
                        # Store that we have this button
                        self.buttons.append(button)

            # Update the status bar with the current mode
            if len(self.modes) > 1:
                self.statusBar.SetStatusText("Mode: %s" % self.modes[self.mode].upper(),5) # no longer showing board type master.config["type"].upper()
            elif master.config["dj"]:
                self.statusBar.SetStatusText("Mode: Normal",5)
            # If we've run once, stop showing the loading status
            if firstrun and displayLoadingProgress:
                displayLoadingProgress

    # A method to shuffle playback indefinitely, like a DJ
    def playDj(self,event=False):

        # Store the previous mode
        previousmode = self.statusBar.GetStatusText(4)
        # Pick a random button
        nexttrack = self.buttons[ random.randint(0,len(self.buttons)-1)]
        # Set the DJ mode
        self.statusBar.SetStatusText("*DJ MODE*", 5)

        if self.djplay:
            # Keep the list down to 20
            if len(self.djplay) > 20:
                del( self.djplay[0] )

            # Choose a random track we haven't played recently
            while nexttrack in self.djplay:
                nexttrack = self.buttons[ random.randint(0,len(self.buttons)-1)]

        self.djplay.append(nexttrack)

        # Cache the file if we need to
        if type(nexttrack) == str:
            nexttrack = nexttrack.cache(soundfile)
        # Start playing, and get the sound file in return
        soundfile = nexttrack.play()

        # If we loop, loop randomly for 2-4 minutes
        if nexttrack.loop:
            countdown = random.randint(90,150)
        # If not a loop, get the length of the track
        else:
            try:
                countdown = soundfile.get_length()
            except(AttributeError):
                countdown = 0

        # Wait for just before the fadetime, then loop
        if master.testmode:
            logger.debug("Countdown: %d, Fadetime: %g/%g" % (countdown, float(master.fadetime[0])/1000, float(master.fadetime[1])/1000 ))
        self.djtimer.Start( (countdown*1000)-master.fadetime[0], True )


    # A method to advance notebook pages: true for right, false for left
    def pageadvance(self,adv=True):
        self.contentPanel.AdvanceSelection(adv)

    # A method to jump to a specific notebook page
    def pagejump(self,pagenum):
        if pagenum <= len(self.contentPanel):
            self.contentPanel.ChangeSelection(pagenum-1)

    # A way to cutoff any play and (optionally) play a "crash" noise
    def cancel(self,canceleffects,cancelmusic,fadeOut=True,interrupt=False,):
        if canceleffects:
        # Stop anything that's playing, with a hard cut for dialog and a fadeout for sfx/music
            if master.config["type"] == "dialog":
                master.mixer.stop()
            elif fadeOut and not self.paused:
                master.mixer.fadeout(master.fadetime[0])
            else:
                master.mixer.stop()
            # Call the queue's own cancellation method
            self.master_queue.Cancel()
            # If cancel is called while locked, clear the lock
            if self.locked:
                self.toggle()
            # If it's cancelled, it cannot be paused
            self.paused = False
        if cancelmusic:
            if fadeOut and not self.musicpaused:
                pygame.mixer.music.fadeout(master.fadetime[0])
            else:
                pygame.mixer.music.stop()
            # If it's cancelled, it cannot be paused
            self.musicpaused = False
            # To be safe, shut down any buffer listeners
            BUFFERLOOP = False
        # If cancel was called with a crash noise, insert some static
        if interrupt and self.staticnoise:
            self.staticnoise.play()
        # Clear the pause status, but don't process any pause toggles
        self.pause(False,False)
        # Clean the "Now Playing" status and "Remaining"
        self.statusBar.SetStatusText("", 1)
        self.statusBar.SetStatusText("", 2)
        # Clear the DJ mode if we have it
        if master.config["dj"]:
            self.djplay = []
            if self.djtimer.IsRunning():
                self.djtimer.Stop()
        # Garbage collect? Clear out any NOCACHE buttons
        for button in self.buttons:
            if button.buffer == 2 and type(button.sounds[0]) != str:
                # Re-initializing the button's load method will clear it... I think?
                if master.testmode:
                    logger.debug("Clearing cache of %s" % button.name)
                button.loadmode()
        # Time-counter?
        if self.timecounter.IsRunning():
            self.timecounter.Stop()


    # A method to pause globally
    def pause(self,effects,music):
        # Shall we address the music streaming channel?
        if music:
            if pygame.mixer.music.get_busy():
                if self.musicpaused:
                    pygame.mixer.music.unpause()
                    self.musicpaused = False
                else:
                    pygame.mixer.music.pause()
                    self.musicpaused = True
            else:
                self.musicpaused = False

        # Shall we address the cached effects channels?
        if effects:
            # The pause button will only perform if the mixer is working, to avoid accidental pausing
            if pygame.mixer.get_busy():
                if self.paused:
                    pygame.mixer.unpause()
                    self.paused = False
                else:
                    pygame.mixer.pause()
                    self.paused = True
            else:
                self.paused = False

        # Generate a note to the status bar
        if not self.paused and not self.musicpaused:
            note = ""
        elif not self.musicpaused:
            note = "-- effects paused --"
        elif not self.paused:
            note = "-- music paused --"
        else:
            note = "-- all paused --"
        self.statusBar.SetStatusText(note, 1)


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

    def seticon(self):
        # Make some icons
        self.tbicon = TaskBarIcon(self)


# --------------------------------------------------------
#  This is the master queue, for adding and playing
# --------------------------------------------------------
class MasterQueue():

    def __init__(self, wxFrame):
        # Create a list to contain everything
        self.queue = []
        self.wxFrame = wxFrame
        self.silence = pygame.sndarray.make_sound(numpy.array([[0, 0]], dtype=numpy.int16))
        self.lastActiveChannel = None
        self.deferSound = None
        self.deferChannel = None
        self.deferLoop = None
        self.deferTimer = wx.Timer(wxFrame)
        wxFrame.Bind(wx.EVT_TIMER, self.DeferTimerCallback, self.deferTimer)

    # This method adds/removes items from the queue
    def Queue(self, item):

        if item in self.queue:
            logger.debug("Removing QUEUE item %s." % item.name)
            self.queue.remove(item)
        else:
            logger.debug("Adding QUEUE item %s." % item.name)
            self.queue.append(item)
        self.ShowStatus()
        # If something is added to the queue and we're not locked, play it immediately
        if self.queue and not master.frame.locked:
            # Call this Queue's on play method
            self.Play()

    # Update the status bar
    def ShowStatus(self):
        if self.queue:
            queuelist = []
            for item in self.queue:
                queuelist.append(item.GetLabel())
            master.frame.statusBar.SetStatusText("Queued: %s" % " ".join(queuelist), 0)
        else:
            master.frame.statusBar.SetStatusText(" -- no queue  --", 0)

    # This routine allows loop intros by queuing the file after playback starts
    def DeferTimerCallback(self, event):
        # Is a channel specified? If so, queue it there
        if self.deferChannel and self.deferChannel.get_queue() == None:
            # If the channel is open and we've been waiting, manually play() so we can include loop/fade parameters
            if not self.deferChannel.is_playing() and master.crossfade[1]:
                logger.debug("Defer call, now playing %s" % self.deferSound)
                self.deferChannel.play(self.deferSound, loops=self.deferLoop, fade_ms=master.fadetime[1])
            # If the channel is busy, queue it
            else:
                logger.debug("Defer call, now queuing %s" % self.deferSound)
                self.deferChannel.queue(self.deferSound)


    # This routine will defer playback of a Sound for a specified time to play a loop intro a queue a looping segment
    def DeferSound(self, channel, sound, oneshot, loop=None, delay=DEFAULT_DEFER):
        logger.debug("Starting a %s deferral delayed %d and looping " % ("one-shot" if oneshot else "continuous", delay),)
        logger.debug(loop)
        self.deferChannel = channel
        self.deferSound = sound
        self.deferLoop = loop
        # If this is a loop, we will defer continuously
        # If this is not, we will one_shot
        self.deferTimer.Start(delay, oneshot)

    def CancelDefer(self):
        if self.deferChannel:
            self.deferChannel.queue(self.silence)
        self.deferTimer.Stop()
        self.deferSound = None
        self.deferChannel = None

    # A method to clear the queue, whether playing all the files queued or not
    def Play(self):
        logger.debug("Crossfade: ",)
        logger.debug(master.crossfade,)
        logger.debug(" Fade: ",)
        logger.debug(master.fadetime)
        ''' This method doesn't loop itself; instead, it plays and then 'queues' the first item in the queue '''
        self.CancelDefer()

        # We can set a fadein according to configuration
        fadein = master.fadetime[1] if master.crossfade[1] else 0
         # Play (only) the first item in the queue by calling its play method
        self.queue[0].play()
        # Track what channel the button is playing on
        self.lastActiveChannel = self.queue[0].channel
        # Use this class' remove method: re-queuing an existing file will remove it
        self.Queue(self.queue[0])
        ''' The Queue method removes the existing item and continues play, thus creating our loop! '''


    # A method to clear the queue without playing any files
    def Cancel(self):
        self.CancelDefer()
        # Run each queued file's clear method to reset appearance
        for queuedfile in self.queue:
            queuedfile.clear()
        self.lastActiveChannel = None
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


        # Make the icon
        png = wx.Image("Resources/synthea_icon_title.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        wx.StaticBitmap(self, -1, png, (10,5))


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
            # No relative scaling, align top, this number controls the space between columns #SIZECONTROL
            innerbox.Add(group, 0, wx.ALIGN_TOP|wx.ALL, 5)
        # Mount the internal sizer in the external sizer
        outerbox.Add(innerbox, 0, wx.ALIGN_CENTER)




        # Run the layout rendering
        self.SetAutoLayout(True)
        self.SetSizer(outerbox)
        self.Layout()


# --------------------------------------------------------
# This panel is a subsection of the main section, a column containing a group of buttons
# --------------------------------------------------------
class ContentGroup(wx.Panel):

    def __init__(self, parent, ID,name,column):
        wx.Panel.__init__(self,parent,ID,size=(-1,-1))

        # Create a static box to contain the list of buttons
        static = wx.StaticBox(self)
        # Create a sizer for the static box, stacking buttons vertically
        staticbox = wx.StaticBoxSizer(static, wx.VERTICAL)
        # Create a title text, because we have more control than using the static box built-in title
        # ...strip the page name from the name
        if "/$/$" in name:
            name = name.split("/$/$")[1]
        title = wx.StaticText(self, -1, name)
        # Mount the title text in the box sizer, this last number is unknown #SIZECONTROL
        staticbox.Add(title, 0, wx.ALIGN_CENTER|wx.BOTTOM, 0)

        self.buttons = []
        # Progagate the box contents
        for buttoncode in column:
            # Create a button object for each designation in the layout
            button = FX_Button(self, -1, **buttoncode)
            # Create an event handler for the pushing of this button
            self.Bind(wx.EVT_TOGGLEBUTTON, button.queue, button)
            # Mount the button in the box sizer, this last number is the margin around buttons #SIZECONTROL
            if sys.platform == "win32":
                staticbox.Add(button, 0, wx.EXPAND|wx.ALL, 12)
            else:
                staticbox.Add(button, 0, wx.EXPAND|wx.ALL, 6)
            # Track the button
            self.buttons.append(button)

        # Create an external box sizer to contain the static box
        enclosure = wx.BoxSizer(wx.VERTICAL)
        # Mount the static box in the external box
        enclosure.Add(staticbox, 0)
        self.SetSizer(enclosure)


# --------------------------------------------------------
# A custom class for the effects buttons themselves
# --------------------------------------------------------
class FX_Button(wx.ToggleButton):

    def __init__(self, parent, ID, name,src,loop=False,loopFile=None,exclusive=False,tooltip=None):
        wx.ToggleButton.__init__(self,parent,ID,name, size=(-1,30))
        self.name = name

        # Store a value whether the sound is playing
        self.channel = False
        # A list of source files
        self.src = src
        if loop:
            self.loop = -1
            self.loopFile = loopFile
        else:
            self.loop = 0
            self.loopFile = None
        # A reference to the vlc Media object
        self.buffer = None
        # Track whether this has been loaded into cache
        self.loaded = False
        # Track whether this button has exclusivity conditions
        if exclusive:
            self.exclusive = exclusive
        # Otherwise, use the board default
        else:
            # If we're on music mode, every track is music unless otherwise specified
            if master.config['type'] == "music":
                self.exclusive = "MUSIC"
            else:
                self.exclusive = "__any__"
        # Track what our last source file was, for random
        self._lastplaynum = None

        # A friendly tooltip!
        if tooltip:
            self.SetToolTip(wx.ToolTip(tooltip))

    # This method loads a sound file from the mode subdirectory
    def loadmode(self):
        # A list of the source soundfile objects, cleared of all previous files
        self.sounds = []
        # Loop through any sourcefiles provided from the layout file
        pathRoot = master.projectroot+master.frame.modes[master.frame.mode]
        master.totalLoaded += 1
        for source in self.src:
            # Store the pathname of the sourcefile based on the current "mode"
            soundfile = pathRoot+"/"+source
            # Test mode doesn't load anything, for speediness
            if not master.testmode:
                # Don't cache in the mixer if it's going to be buffered or on-demand
                if self.buffer:
                    sound = soundfile
                else:
                    sound = soundfile
                    #sound = self.cache(soundfile)
            else:
                sound = None

            # Store the sound object in this parent object's list of sounds
            self.sounds.append(sound)
        # Store a pointer back to this button, by way of dictionary, so it can be called by hotkeys
        master.frame.master_buttons[self.name] = self
        # Store the loop file if it exists
        if self.loopFile:
            loopFilePath = pathRoot+"/"+self.loopFile
            if not os.path.isfile(loopFilePath):
                logger.warn("  ! Warning: sound loop file not found: " + self.loopFile)
                self.loopFile = None
            else:
                if not master.testmode:
                    # If we are buffering, just note the full path
                    if self.buffer:
                        self.loopSound = pathRoot+"/"+self.loopFile
                    # If we are not buffering, load the sound file into an object
                    else:
                        self.loopSound = self.cache(pathRoot+"/"+self.loopFile)


                else:
                    self.loopSound = None
        else:
            self.loopSound = None

    # This method caches a sound file into memory, for non-buffered tracks
    def cache(self,soundfile):
        if master.testmode:
            logger.debug("Caching file %s" % soundfile)
        # Is the file already cached?
        if type(soundfile) == vlc.Media:
            logger.debug("File is already cached!")
            logger.debug(soundfile.get_mrl())
            sound = master.mixer.cachefile(soundfile.get_mrl())
        # Create a pygame sound object to cache the sound in memory
        elif not os.path.isfile(soundfile):
            logger.warn("  ! Warning: sound file not found: " + soundfile)
            sound = master.frame.master_queue.silence
        else:
            sound = master.mixer.cachefile(soundfile)
        return sound


    # This method queues up a sound for playing (regardless of whether the queue is "locked")
    def queue(self,event=False):

        if self.buffer:
            # AVW: this was for VLC, but might not be needed?
            #self.buffer.release()
            self.buffer = None

        # If this has exclusivity, check it
        if self.exclusive != "__any__" and self.channel and self.channel.is_playing():
            logger.debug("  Exclusive media already playing, time to fade out")
            # Fade out this channel according to the rules
            self.channel.fadeout(master.fadetime[0] if master.crossfade[0] else 0)
            return

        # Look for multiple versions to randomize
        if len(self.sounds) > 1:
            playnum = random.randint(0,len(self.sounds)-1)
            # Don't allow the same one to be played twice
            while self._lastplaynum == playnum:
                playnum = random.randint(0,len(self.sounds)-1)
        else:
            playnum = 0

        # Remember what we played
        self._lastplaynum = playnum

        logger.debug("Queueing button %s." % self.name) # Store a buffer with the Media object
        # Instead of passing the media object, why not pass the mri?
        # self.buffer = self.sounds[playnum]
        self.buffer = self.cache(self.sounds[playnum])

        # try:
        #     if getattr(self,"loopSound"):
        #         self.loopSound = self.cache(self.loopSound)
        # except(AttributeError):
        #     self.loopSound = False

        # self.loopSound = getattr(self,"loopSound",False)

        # Store what file we have
        if master.mixer.mode=="vlc":
            self.path = self.name + ": "+master.projectroot+master.frame.modes[master.frame.mode]+"/"+self.buffer.get_mrl()
        elif master.mixer.mode=="pygame":
            self.path =  self.name + ": "+master.projectroot+master.frame.modes[master.frame.mode]+"/"+self.src[playnum]

        # Get a channel
        self.channel = master.mixer.find_channel(group=self.exclusive)
        # Queue this track into the channel
        self.channel.queue(self.buffer)

        # The MasterQueue object handles redundancy and playback for streaming
        master.frame.master_queue.Queue(self)


    # This method actually plays the track! It's called by Queue.Play() when a button is first in the queue
    def play(self):
        # Default to playing
        dontplay = False


        #-------- STREAMING FILE PLAYBACK --------#

        #### Define some unique behaviours depending on what mode we're using ####
        #------------------------------------------------------------------------#
        # DIALOG MODE: Don't overlap! Wait for the channel to clear!
        # if master.config["type"] == "dialog":
        #     while pygame.mixer.get_busy():
        #         continue
        # # MUSIC MODE: Only one track at a time, fade the existing track out first!
        # elif self.exclusive == "MUSIC" or (master.config["type"] == "music" and not self.exclusive):
        #     logger.debug("Looking for existing music track...")
        #     existingmusic = master.mixer.get_current_music_channel()
        #     if existingmusic:
        #         # Is this channel playing THIS track?
        #         if self.channel and self.channel == existingmusic:
        #             dontplay = True
        #             # Clear the channel, in case this is called again before the fadeout
        #             self.channel = None
        #         # Fade out whatever the existing music is
        #         existingmusic.fadeout(master.fadetime[0])
        #     else:
        #         logger.debug("it's not playing?")
        # # SFX MODE: If this is already playing, fade it (and only it) out!
        # elif master.config["type"] == "sfx" and self.exclusive:
        #     logger.debug("  Playback called on exclusive track '%s'" % self.exclusive)
        #     # Is this a single track? Already playing? Kill it
        #     if self.exclusive == 1 and self.channel and self.channel.is_playing():
        #         self.channel.fadeout(master.fadetime[0])
        #         dontplay = True
        #         # Clear the channel, in case this is called again before the fadeout
        #         self.channel = None

        #------------------------------------------------------------------------#

        # Play the file, if applicable (...basically, unless this file was already playing in SFX Mode)
        if not dontplay:

            # Variable behaviour, whether we want to actually play the file or just see that we could have (test mode)
            if master.testmode:
                logger.debug(self.path)
            else:
                # If we haven't cached the file yet, do so now
                # if type(self.sounds[playnum]) == str:
                #     # With VLC we need to instantiate every time
                #     # self.sounds[playnum] = self.cache(self.sounds[playnum])
                #     # If we have an intro and a loop sound, cache the loop sound too
                #     if self.loopSound:
                #         self.loopSound = self.cache(self.loopSound)

                # We can fade in, or not
                fadein = master.fadetime[1] if master.crossfade[1] else 0

                # # Are we specifying a channel to playback to?
                # if queueChannel:
                #     logger.debug("Sending playback to existing channel ",)
                #     logger.debug(queueChannel)
                #     self.channel = queueChannel
                #     # Play this track immediately, via the requested channel
                #     queueChannel.play(self.sounds[playnum], fade_ms=fadein, loops=self.loop)
                #     # Is there a loop sound different from the intro?
                #     if self.loopSound:
                #         master.frame.master_queue.DeferSound(self.channel, self.loopSound, self,loop, False )
                #     # If not, start the loop on this one
                #    # elif self.loop < 0:
                #     #    master.frame.master_queue.DeferSound(self.channel, self.sounds[playnum], False)

                # If no specific playback channel, find a new one
                # else:

                # Are we looping? Do we have an intro?
                looper = self.loop if not self.loopSound else 0
                # If we are waiting for another track to fade out, defer playback
                if not master.crossfade[0]:
                    # Defer playback by the duration of the fadeout
                    master.frame.master_queue.DeferSound(self.channel, self.sounds[self._lastplaynum], True,  looper, master.fadetime[0])
                # Otherwise, play it immediately
                else:
                    logger.info("Playing immediately, looping %s " % looper)
                    # The master mixer will control fading out other channels
                    master.mixer.play(self,loops=looper, fade_ms=fadein)

                # If we have a separate loop intro
                if self.loopSound:
                    # Are we already deferring?
                    deferral = DEFAULT_DEFER + (master.fadetime[0] if not master.crossfade[0] else 0)
                    # then queue up the loop as a deferral
                    logger.debug("Deferring loop track after intro by %d" % deferral)
                    master.frame.master_queue.DeferSound(self.channel, self.loopSound,  False, self.loop, deferral)
                    '''
                        KNOWN ISSUE:
                            Since there is only one Defer Channel, it does not work to defer a looped intro track.
                            The loop deferral will overwrite the intro deferral, and can "pop" in unexpectedly.
                            This could be solved by allowing multiple deferral channels, or including a loop intro
                            checker in the deferral playback method. Another time, maybe.
                    '''

		# Start the timer!
        if not self.loop:
            try:
                master.frame.timeremaining = self.get_time_remaining()
                master.frame.statusBar.SetStatusText("Remaining: %d:%.2d" % (master.frame.timeremaining/60,master.frame.timeremaining%60),2)
                master.frame.timecounter.Start(1000)
            except(AttributeError):
                raise
                pass
        else:
            # Is there a previous loop going?
            if master.frame.timecounter.IsRunning():
                master.frame.timecounter.Stop()
            master.frame.statusBar.SetStatusText("Looping: %s" % unichr(8734),2)

        # Reset the appearance of the button
        self.clear()
        # Update the "now playing"
        if self.loop:
        	# If this is a loop, might as well make note of it
        	playing = "Now Looping: %s" % self.name
        else:
        	playing = "Now Playing: %s" % self.name

        master.frame.statusBar.SetStatusText(playing, 1)
        # Should we start listening?
        if BUFFERLOOP:
            pygameListener()

        # Return the sound object that we ended up playing, in case somebody wants it
        return self.buffer

    # Get the time remaining, for different play modes
    def get_time_remaining(self):
        # Only if we have a thing
        if not self.buffer:
            return 0

        if master.mixer.mode == "vlc":
            logger.debug("duration:", self.buffer.get_duration())
            logger.debug("time:", self.channel.get_time())
            # Duration is in ms
            return (self.buffer.get_duration() / 1000) - self.channel.get_time()
        elif master.mixer.mode == "pygame":
            return self.buffer.get_length()


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
            self.SetBackgroundColour("#C90C0C")
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
        wx.MessageDialog.__init__(self, parent, master.config["quickreference"], "Quick Reference",wx.OK)
        # Show it!
        self.ShowModal()
        # Destroy it!
        self.Destroy()

# --------------------------------------------------------
# A dialogue for system volume
# --------------------------------------------------------
def VolumeWarning(parent, volumes):

    # What do we say?
    message = "The system volume level (%s) does not match this board's target volume (%s).\r\n\r\nWould you like to change the system volume to match the board settings?" % volumes
    # Build a Dialog object based
    warning = wx.MessageDialog(parent, message, "Volume Level Alert",wx.YES_NO|wx.YES_DEFAULT|wx.ICON_EXCLAMATION)
    # Show it!
    answer = warning.ShowModal() == wx.ID_YES
    # Destroy it!
    warning.Destroy()
    # Return the answer
    return answer


# -------------------------------------------------------
# A handler for actual audo playback
#
# This abstracts the control from the board, so we can
# implement different handlers
# -------------------------------------------------------
class Mixer(object):

    def __init__(self,mode='pygame'):

        logger.debug("Creating %s mixer!" % mode)

        self.mode = mode

        # VLC
        if self.mode == 'vlc':
            # Until we extract ALL pygame references, we still need this
            pygame.mixer.init()

        # Default (pygame)
        elif self.mode == 'pygame':
            pygame.mixer.init()

        else:
            logging.error("Unknown mixer mode {}".format(mode))

        # Create an array of general SFX channels
        self.channels = {"__any__": [ Channel(group="__any__")]}

    def cachefile(self,path):
        if self.mode == 'vlc':
            # We want to parse the media so we have metadata, like duration
            media = vlc.Media(path)
            media.parse()
            return media
        elif self.mode == 'pygame':
            return pygame.mixer.Sound(path)

    # Play a sound
    def play(self,sound,loops=None,fade_ms=0):
        # Is this exclusive?
        if sound.exclusive != "__any__" and sound.exclusive in self.channels:
            # Fade out any existing channels in this group
            for channel in self.channels[sound.exclusive]:
                if channel != sound.channel and channel.media and not channel.is_fading_out:
                    channel.fadeout(master.fadetime[0] if master.crossfade[0] else 0)
                    logger.debug("  Fading out %s in %s" % (channel.media,fade_ms))
        # Look for a channel that's available in this group
        # AVW: This sound already got a channel when it was queued
        # sound.channel = self.find_channel(group=sound.exclusive)
        # Load the sound into the channel
        sound.channel.play(loops=loops,fade_ms=fade_ms)

    def find_channel(self,group=None):
        logger.debug("  Looking for a channel for %s" % group)

        # Have we never encountered this group before?
        if not group in self.channels.keys():
            logger.debug("    New channel required for group {}".format(group))
            self.channels[group] = []
        # If we have, look for an empty channel in it
        # AVW: Reusing channels doesn't seem to work. Always a new one?
        else:
        #    self.channels[group] = []
        #     for idx,channel in enumerate(self.channels[group]):
        #         if not channel.is_playing():
        #             logger.debug("   - Found empty channel %d for group '%s'" % (idx,group))
        #             return channel
            logger.info("    No channel exists, make a new one")
        channel = Channel(group=group)
        # Add this channel to the group
        self.channels[group].append(channel)
        return channel

    def fadeout(self,time,group=None):
        logger.debug("  Fading out in {}".format(master.fadetime[1]))
        if self.mode == 'vlc':
            # Are we just fading a specific group?
            if group:
                groups  = [ self.channels[group] ]
            # Or all of them
            else:
                groups = self.channels.values()
            for group in groups:
                for channel in group:
                    if channel.is_playing():
                        channel.fadeout(time)
        elif self.mode == 'pygame':
            # Make this easy :)
            pygame.mixer.fadeout(time)

    def stop(self):
        if self.mode == 'vlc':
            logger.debug(self.channels)
            for group in self.channels.values():
                for channel in group:
                    logger.debug(channel)
                    if channel.is_playing():
                        channel._channel.set_media(None)
        elif self.mode == 'pygame':
            pygame.mixer.stop()

    def delete_channel(self,channel):
        deleted = False
        for channels in self.channels.values():
            if channel in channels:
                logger.debug("  Deleting channel {}".format(channel))
                deleted = True
                #channel._channel.release()
                #del( channels[channels.index(channel)])
                #return
        if not deleted:
            logger.warn("  ! Unable to delete channel!")


class Channel(object):

    def __init__(self,mode=None,group=None):
        self.mode = mode or master.config['playback']
        # What media is in this channel
        self.media = None

        if self.mode == 'vlc':
            self._channel = vlc.MediaPlayer( vlc.Instance() )
            logger.debug("Created channel {}".format(self._channel.get_instance()))
        elif self.mode == 'pygame':
            self._channel = pygame.mixer.find_channel()
        else:
            logger.warn("Unable to assign mode {} to channel".format(mode))


    def is_playing(self):
        if self.mode == 'vlc':
            return self._channel.is_playing()
        elif self.mode == 'pygame':
            return self._channel.get_busy()

    def set_volume(self,vol=100):
        if self.mode == 'vlc':
            self._channel.audio_set_volume(vol)

    # A callable function with no args, for Timer
    def _fadeout(self):
        vol = self._channel.audio_get_volume()
        if vol > 0:
            self._channel.audio_set_volume(vol - 1)
            t = threading.Timer(self.fadetime/1000.0/100.0, self._fadeout)
            t.start()
        else:
            self._channel.set_pause(True)
            self._channel.audio_set_volume(100)
            self.stop()


    def fadeout(self,time):
        # AVW: Is it fading out that breaks channels?
        # self._channel.stop()
        self.fadetime = time
        self.is_fading_out = True
        if self.mode == 'vlc':
            # Get the volume
            vol = self._channel.audio_get_volume()
            # How many steps
            steps = 100.0
            shift = vol / steps
            # Call the timer, which lives in seconds instead of ms
            t = threading.Timer(self.fadetime/1000.0/100.0, self._fadeout)
            t.start()

        elif self.mode == 'pygame':
            self._channel.fadeout(time)

    def stop(self):
        self._channel.stop()
        self.is_fading_out = False
        logger.debug("Channel that used to have %s STOPPED" % self.media)
        master.mixer.delete_channel(self)

    def pause(self):
        self._channel.pause()

    def queue(self,soundobj):
        self.media = soundobj
        # For VLC, we need to set the media now to cache it
        if self.mode == "vlc":
            self._channel.set_media(self.media)
        # For pygame, we'll set it later (since we're already cached)
        self.is_fading_out = False

    def play(self,loops=None,fade_ms=0):
        logger.debug("Plaing channel {}".format(self._channel))
        if self.mode == 'vlc':
            # ALways start with default volume, until we have fadein
            self._channel.play()
        elif self.mode == 'pygame':
            self._channel.play(self.media, loops=loops, fade_ms=fade_ms)
        self.set_volume(100)

    def get_time(self):
        if self.mode == 'vlc':
            return self._channel.get_time()
        elif self.mode == 'pygame':
            return self._channel.get_sound().get_length()

    def get_queue(self):
        if self.mode == 'vlc':
            # TODO: determine whether a sound is queued
            return
        elif self.mode == 'pygame':
            return self._channel.get_queue()




# **************************************** #
# The MAIN FUNCTION                        #
#   ...This is not in a main() function,   #
#   because these all need to be globals   #
# **************************************** $

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
        self.totalLoaded = 0

    def layout(self):
        # Load the project's configuration file
        self.config = synth_layout.loadConfig(self.projectroot)
        # Import the project's layout data, which is now all order-preserved lists
        layoutResult = synth_layout.loadLayout(self.projectroot)
        self.layout_raw = layoutResult[0]
        self.totalSounds = layoutResult[1]
        self.layout_hotkeys = synth_layout.loadHotkeys(self.projectroot,functions=hotkeyFunctions)
        # A default crossfade position: [0,0] for wait/cross, full/fade
        self.crossfade = self.config["crossfade"]
        # Fadein and fadeout values
        self.fadetime = self.config["fadetime"]

        logger.debug("Layouts and config loaded, mixing mixer...")
        # Initialize the mixer
        self.mixer = Mixer(self.config["playback"])


    def render(self):
        # Create the master window
        self.frame = MyFrame(None, -1, self.prog_version)
        # Run some startup functions to set initial values
        self.frame.initialize()
        # Render the master window
        self.frame.Show()

    def reload(self):
        logger.debug("Reloading self, Master!")
        master.mixer.stop()
        self.frame.Destroy()
        self.layout()
        self.render()

# This is it! This routine creates a soundboard and runs it!
def createMaster(projectsource,testmode=False):

    global master, newapp
    newapp = wx.App(0)
    #newapp.ExitOnFrameDelete = True
    # OSX Features
    #if sys.platform == "darwin":
     #   newapp.SetAppName("Synthea")
      #  newapp.SetAppDisplayName("Synthea")

    master = Master(projectsource,testmode)

    master.layout()

    master.render()

    newapp.MainLoop()

    return newapp

# This is a listener so we can catch the end of a streaming loop intro
# ... but it's dumb and I hate it, so it probably shouldn't be used.
def pygameListener():
    global BUFFERLOOP
    while BUFFERLOOP:
        for event in pygame.event.get():
            if event.type == BUFFERLOOP:
                if master.testmode:
                    logger.debug("Initializing buffer loop: ",)
                    logger.debug(master.bufferLoop)
                pygame.mixer.music.load(master.bufferLoop)
                pygame.mixer.music.play(-1)
                BUFFERLOOP = False
