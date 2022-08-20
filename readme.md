# Comedy Bot Bot

This is a twitter bot that uploads screenshot(s) or a video from comedy bang bang every day. You can easily repurpose this for 
a different thing since the media is not included.

Create a folder in the screens directory with up to 4 images in it, and these will be posted together (make sure they are in the 
proper order alphabetically)

Or just add videos to the vids directory. MP4 only, limited to 140 seconds (I know right lol) and 15MB by the twitter API

twitter_dist.json should be renamed to twitter.json and you should put in your own API keys. That's pretty much it.

***Aug 20 2022*** - Now with Cohost support! Check it out! I figured out Selenium for something for work and figured it would be good to use here, since there's no offical public cohost API yet.
If you do not wish to use the cohost stuff it's like two lines in main.py to comment out, and if you do you'll need to configure chrome webdriver and all that jazz. 
take cohost_dist.json and rename it to cohost.json and update it accordingly.