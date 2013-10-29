############
## This loads a layout file and returns a nested list of buttons
##   It is a list of pagename/column tuples, the latter containing
##   columnname/button tuples, the latter containing
##   buttonname and filename tuples
##   -- Source files are now a list of files, for randomization options
##   -- Button tuples now include LOOP information
############

# This function loads layout specs from a file
def loadLayout(docroot="",file="Layout.txt"):
    # Each line from the loaded file!
    lines = []
    # A dictionary, for faster sorting
    pages = {}
    # Lists, for order preservation
    pageorder = []
    frames = []
    buttons = []

    # Grab all the lines from the file
    f = open(docroot+file)
    for line in f.readlines():
        lines.append(line.strip().split("|"))
    f.close()
    # Build a list of all the pages
    for line in lines:
        # Get the name of the page
        pageName = line[0]
        # See if this page has been created yet
        if not pageName in pages:
            # If not, make a dictionary in the pages list with it
            pages[pageName] = {}
            # Set the page number so we can access the list
            pagenum = len(pageorder)
            # Add the page to the pageorder list, in a tuple with a list inside
            pageorder.append((pageName,[]))
            
        # Get the name of the frame
        frameName = line[1]
        # Create a key with the frame name and a value that is a list (of buttons)
        if not frameName in pages[pageName]:
            pages[pageName][frameName] = []
            framenum = len(pageorder[pagenum][1])
            pageorder[pagenum][1].append((frameName,[]))
            
        # Clear out whitespace before/after, just in case the file has extra spaces
        buttonName = line[2].strip()
        buttonSrc = line[3].strip().split(",")
        # Assume that we won't be looping the file, unless the loop flag is found
        buttonLoop = False
        if len(line) > 4:
            if line[4].strip() == "LOOP":
                buttonLoop = True
        # If the button name is not already in the frame, add it!
        if not buttonName in pages[pageName][frameName]:
                pages[pageName][frameName].append((buttonName,buttonSrc,buttonLoop))
                pageorder[pagenum][1][framenum][1].append((buttonName,buttonSrc,buttonLoop))
        
    # Return this clusterfuck of nested lists and tuples
    return pageorder
    
# This function loads a hotkeys file and builds an array of event/button combinations
def loadHotkeys(docroot="",file="Hotkeys.txt"):
    # Store a dictionary of hotkeys
    hotkeys = {}
    # Open the hotkeys file from the project folder
    f = open(docroot+file)
    # Read each line, yes
    for line in f.readlines():
        # Strip whitespace and split into a key event and a button name
        key = line.strip().split("|")
        # Store a dictionary entry with the event as key and the button as value
        hotkeys[int(key[0])] = key[1]
    # Close the hotkey file
    f.close()
    # Return the dictionary
    return hotkeys
    
if __name__ == "__main__":
    print "Whatchoo want?!"