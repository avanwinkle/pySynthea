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


''' A quick and dirty program to merge the separate gui/playback modules '''

# import some basic IO modules
import sys, os
# import the wx module for GUI rendering
#import wx
# set a special path for module loading
#sys.path.append("Resources")
# load the latest version of the gui module
#import synth_board_0_4_3 as synth_board

#### GUI
import synth_kivy_0_1_0 as synth_gui
#### PLAYBACK
import synth_playback_0_5_0 as synth_playback
#### LAYOUT
import synth_layout_0_1_0 as synth_layout  

''' A Super-Button Class '''
class FXButton(synth_playback.SynthButton, synth_gui.SyButton):
	# Pass the args to the playback module
	def __init__(self,config):
		super(synth_playback.SynthButton).__init__(config)
		super(synth_gui.SyButton).__init__(config[0])

class Master(synth_playback.SynthMaster,synth_gui.Master):
	
	def __init__(self,projectname):
		self.Layout = synth_layout.SynthLayout(projectname)
		# Initialize the separate modules
		super(synth_playback.SynthMaster).__init__( self.Layout.docroot,self.Layout.loadConfig() )
		super(synth_gui.SyMaster).__init__( synth_playback.version, self.config["name"] )
			
		# Create our top-level gui object
		self.Board = self.initBoard()
		# Build the layout
		self.buildBoard()
	
	
	# Walk the layout and double-instantiate everything!
	def buildBoard(self,layoutobj):
		for pagetuple in layoutobj.loadLayout()[0]:
			page = self.Board.addPage( pagetuple[1] )
			for frametuple in pagetuple[0]:
				frame = page.addFrame( frametuple[1] )
				for buttontuple in frametuple[0]:
					# We create an object first, to get the merged class
					button = FXButton( buttontuple)
					frame.addButton( button )
			

def main(projectname):

	board = Master("BlakCloud")