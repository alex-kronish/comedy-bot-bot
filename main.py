import helpers
import random
import os


def getRandomImageFiles():
    pass
    folders = sorted(os.listdir("media/screens"))
    folders.remove(".keep")  # file exists to preserve directory structure on github
    idx = random.randrange(0, len(folders))
    # print(folders)
    # print(str(idx))
    # print(folders[idx])
    screenshotdir = folders[idx]
    image_files_os = sorted(os.listdir("media/screens/" + screenshotdir))
    image_files = []
    for i in image_files_os:
        imgfile = "media/screens/" + screenshotdir + "/" + i
        image_files.append(imgfile)
    print(image_files)
    return image_files


def getRandomVideoFile():
    videos = sorted(os.listdir("media/vids"))
    videos.remove(".keep")  # file exists to preserve directory structure on github
    idx = random.randrange(0, len(videos))
    vfile = "media/vids/" + videos[idx]
    return vfile


def main():
    h = helpers.TwitterAPI()
    ch= helpers.CohostAPI()
    video_image_rando = random.randrange(0, 3)
    cohost_string=''
    if video_image_rando == 0:
        # images
        imagefiles = getRandomImageFiles()
        h.postImages(imagefiles)
        cohost_string=ch.postImages(imagefiles)
    else:
        # videos
        videofile = getRandomVideoFile()
        print(videofile)
        h.postVideo(videofile)
        cohost_string=ch.postVideo(videofile)
    print("TWITTER OK")
    ch.postToCohostSelenium(cohost_string)
    print("COHOST (SELENIUM) OK")


if __name__ == "__main__":
    main()
