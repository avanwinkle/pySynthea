# A connector for Synthea playback via VLC

import vlc

def test():


	testtrack = "/Users/Anthony/Desktop/50cal_shoot.wav"

	# Create an instance of the VLC
	i = vlc.Instance()


	# Open a new MediaPlayer instance
	p = vlc.MediaPlayer(i)

	# Set the media
	p.set_mrl(testtrack)
	p.play()

	print "done"



if __name__ == "__main__":
	test()