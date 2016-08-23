############
## This loads a layout file and returns a nested list of buttons
##   It is a list of pagename/column tuples, the latter containing
##   columnname/button tuples, the latter containing
##   buttonname and filename tuples
##	 -- (0.1.0) Improvements and encapsulation for gui/playback separation
##   -- Source files are now a list of files, for randomization options
##   -- Button tuples now include LOOP information
##   -- (0.9) Support for buffering music tracks, expandability for other args, crossfade
##   -- (0.8) Support for unsorted buttons in Layout.txt
##   -- (0.7) Additions by Dan Posluns to support loop intros and name-based modifier keys
##   -- (0.6) Comments supported in all files; Crash noise can now be customized in config.txt
############

import os
import re

defaultCrossfade = [1,1]
defaultFadetime = [1000,1000]

reHotkey = re.compile(r"((?:<ctrl>|<alt>|<cmd>|<shift>)*)([A-Za-z0-9\-\=\[\]\\\;\'\,\.\/\`])")
reHotkeyModifier = re.compile(r"(<ctrl>|<alt>|<cmd>|<shift>)")

### A Class that binds them all ###
class SynthLayout:
	def __init__(self,projectname):
		self.docroot = "../Projects/%s/" % projectname
		

	# This function loads layout specs from a file
	def loadLayout(self,file="Layout.txt"):
		# Each line from the loaded file!
		lines = []
		# A dictionary, for faster sorting
		#pages = {}
		# Lists, for order preservation
		# A list of pages, in order
		pageorder = []
		# A dictionary of pages, with frames in order
		frameorder = {}
		# A dictionary of frames, with buttons in order
		buttonorder = {}
		#frames = []
		#buttons = []

		# Grab all the lines from the file
		f = open(self.docroot+file)
		for line in f.readlines():
			# Ignore comments and blank lines
			if line[0] != "#" and len(line.strip()) > 2:
				lines.append(line.strip().split("|"))
		f.close()
		# Build a list of all the pages
		validCount = 0
		for line in lines:
			# Get the name of the page
			pageName = line[0]
			# See if this page has been created yet
			if not pageName in pageorder:
			   # # If not, make a dictionary in the pages list with it
			   # pages[pageName] = {}
			   # # Set the page number so we can access the list
			   # pagenum = len(pageorder)
				# Add the page to the pageorder list
				pageorder.append(pageName)
				
			# Get the name of the frame
			frameName = line[1]
			# Create a key with the frame name and a value that is a list (of buttons)
			if not pageName in frameorder.keys():
				frameorder[pageName] = [frameName,]
			elif not frameName in frameorder[pageName]:
				frameorder[pageName].append(frameName)
			   
				
			# Clear out whitespace before/after, just in case the file has extra spaces
			buttonName = line[2].strip()
			buttonSrc = line[3].strip().split(",")
			# Assume that we won't be looping the file, unless the loop flag is found
			buttonLoop = False
			loopFile = None
			buttonBuff = False
			# Have additional arguments been passed?
			if len(line) > 4:
				# We'll support multiple arguments, just for the heck of it!
				l4vals = line[4].strip().split(",")
				for l4val in l4vals:
					if l4val.startswith("LOOP="):
						buttonLoop = True
						loopFile = l4val[5:]
					elif l4val.startswith("LOOPEXT="):
						fileParts = os.path.splitext(buttonSrc[0])
						buttonLoop = True
						loopFile = fileParts[0] + l4val[8:] + fileParts[1]
					elif l4val == "LOOP":
						buttonLoop = True
					if l4val == "BUFFER":
						buttonBuff = 1
					elif l4val == "NOCACHE":
						buttonBuff = 2
			# Store each of the button's attributes
			buttoncode = (buttonName,buttonSrc,buttonLoop,loopFile,buttonBuff)
			# If the button name is not already in the frame, add it!
			if not frameName in buttonorder.keys():
				buttonorder[frameName] = [buttoncode,]
				validCount += 1
			elif not buttoncode in buttonorder[frameName]:
				buttonorder[frameName].append(buttoncode)
				validCount += 1
	   
		# Now we'll build a sorted list of everything
		# ... this is an obnoxious routine, but _finally_ allows us to
		# ... have layout files that are not in perfect order!
		pagelist = []
		# pageorder is a sorted list of pages
		for pageName in pageorder:
			# Create a list of frames in this page
			framelist = []
			# frameorder[pageName] is a sorted list of frames
			for frameName in frameorder[pageName]:
				# Create a list of buttons in this frame
				buttonlist = []
				# buttonorder[frameName] is a sorted list of buttons
				for button in buttonorder[frameName]:
					# Work back up the tree, appending to preserve sort order
					buttonlist.append(button)
				framelist.append( (buttonlist, frameName) )
			pagelist.append( (framelist, pageName) )
	 
		# Return this clusterfuck of nested lists and tuples
		return (pagelist, validCount)
		
	# This function loads a hotkeys file and builds an array of event/button combinations
	def loadHotkeys(self,file="Hotkeys.txt",functions=None):
		# Store a list of hotkeys
		hotkeys = []
		# Open the hotkeys file from the project folder
		f = open(self.docroot+file)
		# Read each line, yes
		for line in f.readlines():
			try:
				if line[0] != "#" and len(line) > 1:
					# Strip whitespace and split into a key event and a button name
					key = line.strip().split("|")
					match = reHotkey.match(key[0])
					if match is None:
						print "Error: %s is not a valid hotkey combination. Skipping hotkey entry." % key[0]
					elif not key[1] in functions:
						print "Error: %s is not a valid hotkey function. Skipping hotkey entry." % key[1]
					else:
						# Store a dictionary entry with the event as key and the button as value
						matchGroups = match.groups()
						hotkeys.append( (reHotkeyModifier.findall(matchGroups[0]), matchGroups[1], key[1], tuple(key[2:])) )
			except:
				print line
		# Close the hotkey file
		f.close()
		# Return the dictionary
		return hotkeys
		
	#--------------------------------------------------------------------------------#
	### This method loads a project's configuration settings and other information ###
	#--------------------------------------------------------------------------------#
	def loadConfig(self,file="Config.txt"):
		config = {}
		f = open(self.docroot+file)
		for line in f.readlines():
			if line[0] != "#" and len(line) >1:
				sliced = line.strip().split(":")
				if len(sliced) > 1:
					config[sliced[0]] = sliced[1]
		f.close()
		
		if config.has_key("modes"):
			config["modes"] = config["modes"].split(",")
		if config.has_key("default_window"):
			sizes = config["default_window"].split("x")
			config["default_window"] = (int(sizes[0]),int(sizes[1]))
		else:
			config["default_window"] = (900,750)
		if config.has_key("dj") and config["dj"] == "enabled":
			config["dj"] = True
		else:
			config["dj"] = False
			
		# Shall crossfades be enabled by default?
		crossfade = False
		if config.has_key("crossfade"):
			crossconfig = config["crossfade"].split(",")
			
			# New config files should have a comma
			if len(crossconfig) == 2:
				# Look for the first value
				if crossconfig[0] in ("cross","1"):
					crossfade = [1,]
				elif crossconfig[0] in ("wait","0"):
					crossfade = [0,]
				else:
					crossfade = [defaultCrossfade[0],]
				# Look for the second value
				if crossconfig[1] in ("fade","1"):
					crossfade.append(1)
				elif crossconfig[1] in ("wait","0"):
					crossfade.append(0)
				else:
					crossfade.append( defaultCrossfade[1] )
					
			# Legacy modes for older config files
			elif config["crossfade"] == "enabled":
				config["crossfade"] = [1,1]
			elif config["crossfade"] == "disabled":
				config["crossfade"] = [0,0]
		# If not specified (or not recognized), use the global default
		else:
			config["crossfade"] = defaultCrossfade
			
		if config.has_key("fadetime"):
			# If the crossfade specified is a number, we'll make it default
			try:
				# If we have two numbers, split it
				config["fadetime"] = [ int(val)*1000 for val in config["fadetime"].split(",") ]
				# If we only got one number, make it twice
				if len(config["fadetime"]) == 1:
					config["fadetime"].append(config["fadetime"][0])
			# If not, set a global default
			except(ValueError):
				config["fadetime"] = defaultFadetime
		else:
			config["fadetime"] = defaultFadetime
			

			
		# Look for a QuickReference file
		quickreference = []
		try:
			f = open(self.docroot+"QuickReference.txt")
			for line in f.readlines():
				quickreference.append(line)
		except(IOError):
			pass
		config["quickreference"] = "".join(quickreference)
		
		# Make sure we got everything
		for key in ("name","type","modes"):
			if not config.has_key(key):
				raise(AttributeError,"Missing configuration %s" % key)
		return config
		  