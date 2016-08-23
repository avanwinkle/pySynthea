'''  **** SYNTHEA PLAYBACK CLASSES ****

    This file contains:
        the SynthButton class, which should be a co-class of each GUI button
        the SynthMaster class, which should be an attribute of the GUI root
        ...
        the SynthQueue class, which is instantiated as an attribute SynthMaster.queue
'''



# -------- Current ----------------------
version = "0.5.0"  

# -------- Changelog --------------------
# 0.5.0 - Separation of GUI and Playback Classes, Kivy interface
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
import synth_layout_0_1_0 as synth_layout
# The game module that provides our audio interface
import pygame
# Import the random module for randomizing sound clips
import random
# Import numpy for creating the sound of silence (Posluns)
import numpy

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
'''
# Define the hotkey modifiers
hotkeyModifiers = {
    "<ctrl>": wx.ACCEL_CTRL,
    "<alt>": wx.ACCEL_ALT,
    "<cmd>": wx.ACCEL_CMD,
    "<shift>": wx.ACCEL_SHIFT
}
'''

        
# --------------------------------------------------------
#  This is the master queue, for adding and playing
# --------------------------------------------------------
class SynthQueue():

    def __init__(self):
        # Create a list to contain everything
        self.queue = []
        ''' self.wxFrame = wxFrame'''
        self.silence = pygame.sndarray.make_sound(numpy.array([[0, 0]], dtype=numpy.int16))
        self.lastActiveChannel = None
        self.deferSound = None
        self.deferChannel = None
        self.deferLoop = None
        '''  self.deferTimer = wx.Timer(wxFrame)
        wxFrame.Bind(wx.EVT_TIMER, self.DeferTimerCallback, self.deferTimer)'''
        
    # This method adds/removes items from the queue
    def Queue(self, item):
        
        if item in self.queue:
            print "Removing QUEUE item %s." % item.name
            self.queue.remove(item)
        else:
            print "Adding QUEUE item %s." % item.name
            self.queue.append(item)
        self.ShowStatus()
        # If something is added to the queue and we're not locked, play it immediately
        if self.queue and not master.frame.locked:
            # Call this Queue's on play method
            self.Play()
            
    # Update the status bar
    def GetStatus(self):
        if self.queue:
            queuelist = []
            for item in self.queue:
                queuelist.append(item.GetLabel())
                return "Queued: %s" % " ".join(queuelist)
        else:
            return " -- no queue  --"

    
    # This routine allows loop intros by queuing the file after playback starts
    def DeferTimerCallback(self, event):
        # Is a channel specified? If so, queue it there
        if self.deferChannel and self.deferChannel.get_queue() == None:
            # If the channel is open and we've been waiting, manually play() so we can include loop/fade parameters
            if not self.deferChannel.get_busy() and master.crossfade[1]:
                print "Defer call, now playing %s" % self.deferSound
                self.deferChannel.play(self.deferSound, loops=self.deferLoop, fade_ms=master.fadetime[1])
            # If the channel is busy, queue it
            else:
                print "Defer call, now queuing %s" % self.deferSound
                self.deferChannel.queue(self.deferSound)
        
    
    # This routine will defer playback of a Sound for a specified time to play a loop intro a queue a looping segment
    def DeferSound(self, channel, sound, oneshot, loop=None, delay=DEFAULT_DEFER):
        print "Starting a %s deferral delayed %d and looping " % ("one-shot" if oneshot else "continuous", delay),
        print loop
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
        print "Crossfade: ",
        print master.crossfade,
        print " Fade: ",
        print master.fadetime
        ''' This method doesn't loop itself; instead, it plays and then 'queues' the first item in the queue '''
        self.CancelDefer()
        queueChannel = None
        ##### REDUNDANT: The music check is done on a per-Button basis, because dialogue and SFX checks /HAVE/ to be
        # If music is chosen and music exists (except buffered), fadeout the mixer for a nice transition
       # if master.config["type"] == "music":# and self.queue[0].buffer != 1:
        #    pygame.mixer.fadeout(master.fadetime[0])
            # If the upcoming track is waiting for silence, put it on the same channel
            #if not master.crossfade[0]:
            #    queueChannel = self.lastActiveChannel
        # We can set a fadein according to configuration
        fadein = master.fadetime[1] if master.crossfade[1] else 0
         # Play (only) the first item in the queue by calling its play method
        self.queue[0].play(queueChannel)
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
# A custom class for the effects buttons themselves
# --------------------------------------------------------
class SynthButton():

    def initbutton(self, master, name,src,loop=False,loopFile=None,buffer=False):
        # Keep track of who the master is!
        self.master = master
        # Remember our name!
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
        # Track whether we stream or buffer this
        self.buffer = buffer


    # This method loads a sound file from the mode subdirectory
    def loadmode(self):
        # A list of the source soundfile objects, cleared of all previous files
        self.sounds = []
        # Loop through any sourcefiles provided from the layout file
        pathRoot = self.master.projectroot+self.master.frame.modes[self.master.frame.mode]        
        self.master.totalLoaded += 1
        for source in self.src:
            # Store the pathname of the sourcefile based on the current "mode"
            soundfile = pathRoot+"/"+source
            # Test mode doesn't load anything, for speediness
            if not self.master.testmode:
                # Don't cache in the mixer if it's going to be buffered or on-demand
                if self.buffer:
                    sound = soundfile
                else:
                    sound = self.cache(soundfile)
            else:
                sound = None
            
            # Store the sound object in this parent object's list of sounds
            self.sounds.append(sound)
        # Store a pointer back to this button, by way of dictionary, so it can be called by hotkeys
        self.master.frame.master_buttons[self.name] = self
        # Store the loop file if it exists
        if self.loopFile:
            loopFilePath = pathRoot+"/"+self.loopFile
            if not os.path.isfile(loopFilePath):
                print "Warning: sound loop file not found: " + self.loopFile
                self.loopFile = None
            else:
                if not self.master.testmode:
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
        if self.master.testmode:
            print "Caching file %s" % soundfile
        # Create a pygame sound object to cache the sound in memory
        if not os.path.isfile(soundfile):
            print "Warning: sound file not found: " + soundfile
            sound = self.master.frame.master_queue.silence   
        else:
            sound = pygame.mixer.Sound(soundfile)
        return sound
        
        
    # This method queues up a sound for playing (regardless of whether the queue is "locked")
    def queue(self,event=False):
        print "Queueing button %s." % self.name
        # If this is a streaming music track, we can get ready by buffering the file
        if self.buffer == 1:
            # Loading a file to the buffer will cancel playback, so only do so if we're not playing something
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load(self.sounds[0])
                self.loaded = True
            # ...but remember whether we've loaded or not, for when it's time to play this one
            else:
                self.loaded = False
        # If this is a cache track that has not been cached, do that now so it's ready when the queue is unlocked
        elif type(self.sounds[0]) == str:
            # The random playback isn't decided until playtime, so cache them all?
            for playnum in range(0,len(self.sounds)):
                self.sounds[playnum] = self.cache(self.sounds[playnum])
            if self.loopSound:
                self.loopSound = self.cache(self.loopSound)
        # The MasterQueue object handles redundancy and playback for streaming
        self.master.frame.master_queue.Queue(self)
       

    # This method actually plays the track! It's called by Queue.Play() when a button is first in the queue
    def play(self,queueChannel=None):
        # Default to playing
        dontplay = False
        
        #-------- STREAMING FILE PLAYBACK --------#
        if self.buffer == 1:
            # Don't play during test mode :P
            if not self.master.testmode:
                # If we're already musicing, fade out
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.fadeout(self.master.frame.fadetime[0])
                # If we haven't loaded the file, better do that now!
                if not self.loaded:
                    pygame.mixer.music.load(self.sounds[0])
                    
                # If we loop, do that first
                #### NOTE: the transition from loop intro to loop track is * NOT SEAMLESS *
                ####       when using the buffering system, so be cautious when choosing both!!
                if self.loop < 0 and self.loopFile:
                    if self.master.testmode:
                        print "Found loop, creating buffer for %s" % self.loopFile
                        print "JUST KIDDING"
                    # An event type for shifting the buffer from loop intro to loop
                  #  global BUFFERLOOP
                   # BUFFERLOOP = pygame.USEREVENT + 1
                  #  self.master.bufferLoop = self.loopSound
                  #  pygame.mixer.music.set_endevent(BUFFERLOOP)
                    # Play without looping, so we can trigger the end event
                    if self.master.testmode:
                        print "Starting with sound %s" % self.sounds[0]
                    pygame.mixer.music.load(self.sounds[0])
                    pygame.mixer.music.play()
                else:
                    if self.master.testmode:
                        print "Found buffer that doesn't require loopage."
                  #  BUFFERLOOP = False
                    pygame.mixer.music.play(self.loop)
            # In test mode, print the output is all
            else:
                print self.name + ": "+self.master.projectroot+self.master.frame.modes[self.master.frame.mode]+"/"+self.src[playnum]

                
        #------- CACHED FILE PLAYBACK ------------#
        else:
            #### Define some unique behaviours depending on what mode we're using ####
            #------------------------------------------------------------------------#
            # DIALOG MODE: Don't overlap! Wait for the channel to clear!
            if self.master.config["type"] == "dialog":
                while pygame.mixer.get_busy():
                    continue
            # MUSIC MODE: Only one track at a time, fade the existing track out first!
            elif self.master.config["type"] == "music":
                if pygame.mixer.get_busy():
                    pygame.mixer.fadeout(self.master.fadetime[0])                
            # SFX MODE: If this is already playing, fade it (and only it) out!
            elif self.master.config["type"] == "sfx" and self.channel:
                if self.channel.get_busy():
                    self.channel.fadeout(self.master.fadetime[0])
                    dontplay = True
            #------------------------------------------------------------------------#
                
            # Look for multiple versions to randomize
            if len(self.sounds) > 1:
                playnum = random.randint(0,len(self.sounds)-1)
            else:
                playnum = 0
            # Play the file, if applicable (...basically, unless this file was already playing in SFX Mode)
            if not dontplay:
                # Variable behaviour, whether we want to actually play the file or just see that we could have (test mode)
                if not self.master.testmode:
                    # If we haven't cached the file yet, do so now
                    if type(self.sounds[playnum]) == str:
                        self.sounds[playnum] = self.cache(self.sounds[playnum])
                        # If we have an intro and a loop sound, cache the loop sound too
                        if self.loopSound:
                            self.loopSound = self.cache(self.loopSound)  
                    
                    # We can fade in, or not
                    fadein = self.master.fadetime[1] if self.master.crossfade[1] else 0
                    
                    # Are we specifying a channel to playback to?
                    if queueChannel:
                        print "Sending playback to existing channel ",
                        print queueChannel
                        self.channel = queueChannel
                        # Play this track immediately, via the requested channel
                        queueChannel.play(self.sounds[playnum], fade_ms=fadein, loops=self.loop)
                        # Is there a loop sound different from the intro?
                        if self.loopSound:
                            self.master.frame.master_queue.DeferSound(self.channel, self.loopSound, self,loop, False )
                        # If not, start the loop on this one    
                       # elif self.loop < 0:
                        #    self.master.frame.master_queue.DeferSound(self.channel, self.sounds[playnum], False)
                    
                    # If no specific playback channel, find a new one
                    else:
                        # Grab a channel
                        self.channel = pygame.mixer.find_channel()
                        # Are we looping? Do we have an intro?
                        looper = self.loop if not self.loopSound else 0
                        # If we are waiting for another track to fade out, defer playback
                        if not self.master.crossfade[0]:
                            # Defer playback by the duration of the fadeout
                            self.master.frame.master_queue.DeferSound(self.channel, self.sounds[playnum], True,  looper, self.master.fadetime[0])
                        # Otherwise, play it immediately
                        else:
                            print "Playing immediately, looping ",
                            print looper
                            self.channel.play(self.sounds[playnum], loops=looper, fade_ms=fadein)
                            
                        # If we have a separate loop intro
                        if self.loopSound:
                            # Are we already deferring?
                            deferral = DEFAULT_DEFER + (self.master.fadetime[0] if not self.master.crossfade[0] else 0)
                            # then queue up the loop as a deferral
                            print "Deferring loop track after intro by %d" % deferral
                            self.master.frame.master_queue.DeferSound(self.channel, self.loopSound,  False, self.loop, deferral)
                        '''
                            KNOWN ISSUE:
                                Since there is only one Defer Channel, it does not work to defer a looped intro track.
                                The loop deferral will overwrite the intro deferral, and can "pop" in unexpectedly.
                                This could be solved by allowing multiple deferral channels, or including a loop intro
                                checker in the deferral playback method. Another time, maybe.
                        '''
                      
                                
                # In test mode, just print the file
                else:
                    print self.name + ": "+self.master.projectroot+self.master.frame.modes[self.master.frame.mode]+"/"+self.src[playnum]

		# Start the timer!
        if not self.loop:
            self.master.frame.timeremaining = self.sounds[playnum].get_length()
            '''  self.master.frame.statusBar.SetStatusText("Remaining: %d:%.2d" % (self.master.frame.timeremaining/60,self.master.frame.timeremaining%60),2)'''
            self.master.frame.timecounter.Start(1000)
        else:
            # Is there a previous loop going?
            if self.master.frame.timecounter.IsRunning():
                self.master.frame.timecounter.Stop()
        '''    self.master.frame.statusBar.SetStatusText("Looping: %s" % unichr(8734),2)'''
       
        # Reset the appearance of the button
        '''  self.clear()'''
        # Update the "now playing"
        if self.loop:
        	# If this is a loop, might as well make note of it
        	playing = "Now Looping: %s" % self.name
        else:
        	playing = "Now Playing: %s" % self.name
        
        '''   self.master.frame.statusBar.SetStatusText(playing, 1)
        # Should we start listening?
        if BUFFERLOOP:
            pygameListener()'''
                
        # Return the sound object that we ended up playing, in case somebody wants it
        return self.sounds[playnum]
        
    # This method just makes the button look unpressed
    def clear(self):
        self.SetValue(False)

# **************************************** #
# The MASTER CLASS                         #
# **************************************** #


class SynthMaster:

    def __init__(self,projectname,testmode=False):
        
        layoutobj = synth_layout.SynthLayout(projectname)
        
        #self.projectroot = projectroot
        config = layoutobj.loadConfig()
        self.layout = layoutobj.loadLayout()
        
        # ---- Top-Level Variables Here ---- #
        # A default folder for testing, no slashes
        self.testmode = testmode
        # Set the program title
        if self.testmode:
            testflag = " [TEST MODE]"
        else:
            testflag = ""
        self.name = config["name"]
        self.prog_version = "Synthea "+version+testflag
        self.totalLoaded = 0
        print "mixing mixer"
        # Initialize the mixer
        pygame.mixer.init()
        print "mixing display"
        #pygame.display.init()
        print "pumping event"
       # pygame.display.set_icon("Resources/synthea_icon_apple.icns")
        #pygame.event.pump()
	        
        # This is the QUEUE!
        self.master_queue = SynthQueue()
        
        ''' PARAMETERS FROM wx.Frame '''
		
        # Set some starting conditions and variables
        self.locked = False     
        self.paused = False
        self.musicpaused = False
        # Some inital values come from the config file
        self.modes = config["modes"]
        '''
        # A time-remaining timer
        self.timecounter = 
        self.timeremaining = 0
        self.Bind(wx.EVT_TIMER, self.timeRemaining, self.timecounter)
        '''
		
        self.mode = -1
       # self.master_queue = MasterQueue(self)
        # A dictionary of all buttons, for easy access!
        self.master_buttons = {}
        # A default or custom (or no) crash noise
        if config.has_key("crashnoise"):
            if config["crashnoise"] == "none":
                self.staticnoise = False
            else:
                self.staticnoise = pygame.mixer.Sound(self.projectroot+"/"+config["crashnoise"])
        # If no crash noise is specificed, use the default static
        else:
            self.staticnoise = pygame.mixer.Sound("Resources/crashnoise.wav")

        '''
    def layout(self):
        # Load the project's configuration file
        self.config = synth_layout.loadConfig(self.projectroot)
        # Import the project's layout data, which is now all order-preserved lists
        layoutResult = synth_layout.loadLayout(self.projectroot)
        self.layout_raw = layoutResult[0]
        self.totalSounds = layoutResult[1]
        self.layout_hotkeys = synth_layout.loadHotkeys(self.projectroot,functions=hotkeyFunctions)'''
        # A default crossfade position: [0,0] for wait/cross, full/fade
        self.crossfade = config["crossfade"]
        # Fadein and fadeout values
        self.fadetime = config["fadetime"]
		
    ''' METHODS FROM wx.Frame '''
	
	# Proper closure
    def OnCloseWindow(self,Event):
        # Stop the noise!
        pygame.mixer.stop()
        pygame.quit()
        
        '''
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
        '''
                
    # This sets some startup conditions
    def initializeButtons(self):
        # Set our default mode by forcing the changemode with an argument
        self.changeMode(True)
        # Set our default status bar value
        self.master_queue.ShowStatus()
        
    # This is the event handler, specially designed to accept the key codes and execute their functions
    def parseEvent(self,evttype):
        # Of course, only execute if there's an event that matches the key code
        if evttype in self.global_events.keys():
            # Under testmode, print to the console what's happening
            if master.testmode:
                print "Activating: ",
                print self.global_events[evttype]
            exec(self.global_events[evttype])
            
    # Change the crossfade mode
    def setCrossfadeEnabled(self, enabled):
       # master.crossfade = enabled
        print "Current crossfade: ",
        print master.crossfade
        master.crossfade = [enabled,enabled]
        print "Set crossfade: ",
        print master.crossfade
        self.updateFadeDisplay()
    
    def toggleCrossfade(self, method):
        # We can toggle either the 0 or the 1, depending
        master.crossfade[method] = not master.crossfade[method]
        print "New crossfade: ",
        print master.crossfade
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
        # Store (or reset) a list of our button objects, for later use (e.g. garbage collection)
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
                            print "%d%%: %s" % (int(float(master.totalLoaded * 100) / master.totalSounds), ", ".join(button.src) )
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
        '''# Set the DJ mode
        self.statusBar.SetStatusText("*DJ MODE*", 5)'''

        if self.djplay:
            # Keep the list down to 20
            if len(self.djplay) > 20:
                del( self.djplay[0] )

            # Choose a random track we haven't played recently
            while nexttrack in self.djplay:
                nexttrack = self.buttons[ random.randint(0,len(self.buttons)-1)]
             
        self.djplay.append(nexttrack)
        
        # Start playing, and get the sound file in return
        soundfile = nexttrack.play()
        
        # If we loop, loop randomly for 2-4 minutes
        if nexttrack.loop:
            countdown = random.randint(90,150)
        # If not a loop, get the length of the track
        else:
            countdown = soundfile.get_length()

        # Wait for just before the fadetime, then loop
        if master.testmode:
            print "Countdown: %d, Fadetime: %g/%g" % (countdown, float(master.fadetime[0])/1000, float(master.fadetime[1])/1000 )
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
                pygame.mixer.stop()
            elif fadeOut and not self.paused:
                pygame.mixer.fadeout(master.fadetime[0])
            else:
                pygame.mixer.stop()
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
           # BUFFERLOOP = False
        # If cancel was called with a crash noise, insert some static
        if interrupt and self.staticnoise:
            self.staticnoise.play()
        # Clear the pause status, but don't process any pause toggles
        self.pause(False,False)
        '''    # Clean the "Now Playing" status and "Remaining"
        self.statusBar.SetStatusText("", 1)
        self.statusBar.SetStatusText("", 2)'''
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
                    print "Clearing cache of %s" % button.name
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
        

    