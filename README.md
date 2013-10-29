SYNTHEA README
==============

Synthea, short for SYNthetic THEater Audio, is a realtime audio playback system designed for improvised theater. It was first written by Anthony van Winkle for the unscripted play FINAL TRANSMISSION in the summer of 2011.

This program relies on project subfolders stored in its \'Projects\' subdirectory; the Project Loader you are currently using reads these subfolders to offer a list of valid projects. Choose one to load that project's soundboard.

Each project file has a Config file that defines its name, type (dialog, sound effects, or music), and its optional playback modes. The types are distinguished by the following characteristics:

     DIALOG: Concurrent cues are queued and played back sequentially
     EFFECTS: Concurrent cues are played simultaneously
     MUSIC: New cues fade in as the previous cue is faded out

     Additionally, each project configuration file can declare multiple 'modes', which are subdirectories that contain mirrors of all the cue files. These modes allow on-the-fly switching between audio sets while maintaining the project's board layout.

Each project folder also contains a Layout file, which is a delimited text file that defines the hierarchy of pages, groups, effects buttons, and cue files for that soundboard. Multiple cue files can be assigned to the same button; in such cases, a random file will be selected each time the button is queued.

Finally, each project has an optional Hotkeys file, where global keyboard events can be programmed. These events will override the built-in hotkeys, and are a simple delimited list of keyboard event codes (triggers) and effect button names (actions).


For more information visit www.synthea.org
(C) 2011-2013 Anthony van Winkle
Additional help by Dan Posluns
