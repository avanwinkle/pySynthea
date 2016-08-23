''' KIVY CLASSES FOR SYNTHEA '''

import kivy
kivy.require('1.7.2') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stacklayout import StackLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem

from kivy.graphics import Color
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget

import synth_layout_0_1_0 as synth_layout
import synthea_0_5_0 as synth_core

class TitleBar(Label):
	pass

class SyButton(Button,synth_core.SynthButton):

	def __init__(self,master,buttonconfig,**kwargs):
		super(SyButton,self).__init__(**kwargs)
		# SynthButton will initialize all playback functions
		self.initbutton(master,*buttonconfig)

class SyFrame(StackLayout):

	def __init__(self,framename,**kwargs):
		super(SyFrame,self).__init__(**kwargs)
		self.name = framename
		
	def addButton(self, buttonObj ):
		# For convenience, pass the Button array as a tuple, not *args
		self.add_widget( buttonObj )


class SyPage(BoxLayout):

	def __init__(self,pagename,**kwargs):
		super(SyPage,self).__init__(**kwargs)
		self.name = pagename
		self.columns = {}
		
	def addColumn(self, framename ):
		# Convert the layout Frame into a Kivy Column
		column = SyFrame( framename )
		# Store a reference to this column via dictionary
		self.columns[framename] = column
		# Append the widget
		self.add_widget(column)
		# Return it
		return column
		
class MainWindow(BoxLayout):

	def __init__(self,**kwargs):
		super(MainWindow,self).__init__(**kwargs)
		
		titlebar = TitleBar()
		self.add_widget(titlebar)
		
		# Store ourselves
		self.pages = {}
		
		# Build a tabbed panel
		self.board = TabbedPanel(do_default_tab=False)
			
		# Add the board to the Master window
		self.add_widget(self.board)
	
	''' Encapsulated methods for building a board '''
	
	# Walk the layout and double-instantiate everything!
	def propagateLayout(self,master):
		for pagetuple in master.layout[0]:
			page = self.addPage( pagetuple[1] )
			for frametuple in pagetuple[0]:
				frame = page.addColumn( frametuple[1] )
				for buttontuple in frametuple[0]:
					# We create an object first, to get the merged class
					button = SyButton( master, buttontuple)
					frame.addButton( button )
					
	def addPage(self, pagename ):
		if not pagename in self.pages.keys():
			# Build a TPI to encapsulate the widget within the tabbed structure
			tab = TabbedPanelItem( text=pagename )
			# Build a Page object to be the TabbedPanelItem child
			page = SyPage( pagename )
			# Append the page to the tab
			tab.add_widget( page )
			# Store a reference to the *PAGE* directly, via dictionary
			self.pages[pagename] = tab
			# Append the tab to the board
			self.board.add_widget( page )
			# Return it
			return page
		



class MasterApp(App):

	# I don't know _what_ we'll pass yet, but here it will be
	def initBoard(self, projectname ):
		
		#self.layout = parameters["layout"]
		# We are the master!
		self.master = synth_core.SynthMaster( projectname , testmode=True)
		self.title = "%s - %s " % (self.master.name, self.master.prog_version)
		
		self.Board = MainWindow( )
		self.Board.propagateLayout( self.master )

	def build(self):
		return self.Board


# A way to get the program running
def runApplication():
	synthboard = MasterApp()
	synthboard.initBoard( "BlakCloud" )
	synthboard.run()
	
if __name__ == '__main__':


	runApplication()