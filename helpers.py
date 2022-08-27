import json
import requests
import os
from requests_oauthlib import OAuth1
import sys
import time
import mimetypes
#import selenium
from selenium import webdriver
#import webdriver_manager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options


class TwitterAPI:

    def __init__(self):
        # constructor
        print("Let's say hello to our good friend, Reggie Watts...")
        credfile = open("config/twitter.json", "rt")
        creds = json.load(credfile)
        credfile.close()
        self.media_endpoint_url = "https://upload.twitter.com/1.1/media/upload.json"
        self.tweet_endpoint_url = "https://api.twitter.com/1.1/statuses/update.json"
        self.oauth = OAuth1(
            creds["twitter"]["api_key"],
            client_secret=creds["twitter"]["api_secret"],
            resource_owner_key=creds["twitter"]["access_token"],
            resource_owner_secret=creds["twitter"]["access_secret"]
        )

    def check_status(self, media_id, processing_info):
        # checks video processing status. from the large twitter video example linked in the twitter api docs
        if processing_info is None:
            return

        state = processing_info['state']

        print('Media processing status is %s ' % state)

        if state == u'succeeded':
            return

        if state == u'failed':
            sys.exit(0)

        check_after_secs = processing_info['check_after_secs']

        print('Checking after %s seconds' % str(check_after_secs))
        time.sleep(check_after_secs)

        print('STATUS')

        request_params = {
            'command': 'STATUS',
            'media_id': media_id
        }

        req = requests.get(url=self.media_endpoint_url, params=request_params, auth=self.oauth)
        processing_info = req.json().get('processing_info', None)
        self.check_status(media_id, processing_info)

    def postImages(self, filenames):
        media_id_array = []
        chunk_size = 4194304
        for f in filenames:
            img = open(f, "rb")
            imagetype = mimetypes.guess_type(f)
            if imagetype[0] is None:
                print("Couldnt determine the image type")
                sys.exit(77)
            file_size_total = os.path.getsize(f)
            file_size_processing = 0
            segment_count = 0
            initdata = {
                'command': 'INIT',
                'media_type': imagetype[0],
                'total_bytes': file_size_total
            }
            initreq = requests.post(self.media_endpoint_url, data=initdata, auth=self.oauth)
            if initreq.status_code > 299 or initreq.status_code < 200:
                print("Something went wrong initializing.")
                print("status code: " + str(initreq.status_code))
                sys.exit(99)
            initreq_json = initreq.json()
            media_id = initreq_json["media_id"]
            print('Media ID: %s' % str(media_id))
            # append chunks
            while file_size_processing < file_size_total:
                chunk = img.read(chunk_size)
                appenddata = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_count
                }
                chunkdata = {"media": chunk}
                chunkreq = requests.post(url=self.media_endpoint_url, data=appenddata, files=chunkdata, auth=self.oauth)
                if chunkreq.status_code > 299 or chunkreq.status_code < 200:
                    print("Something went wrong in the chunking/append process")
                    print("Status code: " + str(chunkreq.status_code))
                    print(chunkreq.text)
                    sys.exit(88)
                segment_count = segment_count + 1
                file_size_processing = img.tell()
                pctg = (file_size_processing / file_size_total) * 100
                print("Progress: " + f"{pctg:3.2f}" + " - Sent " + str(file_size_processing)
                      + " bytes out of " + str(file_size_total))
            # finalize
            print("Finalizing...")
            img.close()
            finalizedata = {
                "command": "FINALIZE",
                "media_id": media_id
            }
            finalizereq = requests.post(url=self.media_endpoint_url, data=finalizedata, auth=self.oauth)
            processing_info = finalizereq.json().get('processing_info', None)
            self.check_status(media_id, processing_info)
            media_id_array.append(str(media_id))
        # ok we did upload some files let's try and attach them to a tweet?
        media_ids = ",".join(media_id_array)
        # slam it down
        tweetdata = {
            "status": "",
            "media_ids": media_ids
        }
        twreq = requests.post(url=self.tweet_endpoint_url, data=tweetdata, auth=self.oauth)
        print("Done!!!!!!!!")
        pass

    def postVideo(self, filename):
        video_file = open(filename, "rb")
        file_size_total = os.path.getsize(filename)
        file_size_processing = 0
        segment_count = 0
        media_id = None
        processing_info = None
        chunk_size = 4194304  # 4MB
        # twitter videos (and images) use a 4-part upload process
        # step 1: initialize
        # step 2: loop over and upload chunks with an append function until done (less relevant for images)
        # step 3: finalize
        # step 4: take those media id(s) and add it to a tweet.
        # initialize:
        initdata = {
            'command': 'INIT',
            'media_type': 'video/mp4',
            'total_bytes': file_size_total,
            'media_category': 'tweet_video'
        }
        initreq = requests.post(self.media_endpoint_url, data=initdata, auth=self.oauth)
        if initreq.status_code > 299 or initreq.status_code < 200:
            print("Something went wrong initializing.")
            print("status code: " + str(initreq.status_code))
            sys.exit(99)
        initreq_json = initreq.json()
        media_id = initreq_json["media_id"]
        print('Media ID: %s' % str(media_id))
        # append chunks
        while file_size_processing < file_size_total:
            chunk = video_file.read(chunk_size)
            appenddata = {
                "command": "APPEND",
                "media_id": media_id,
                "segment_index": segment_count
            }
            chunkdata = {"media": chunk}
            chunkreq = requests.post(url=self.media_endpoint_url, data=appenddata, files=chunkdata, auth=self.oauth)
            if chunkreq.status_code > 299 or chunkreq.status_code < 200:
                print("Something went wrong in the chunking/append process")
                print("Status code: " + str(chunkreq.status_code))
                print(chunkreq.text)
                sys.exit(88)
            segment_count = segment_count + 1
            file_size_processing = video_file.tell()
            pctg = (file_size_processing / file_size_total) * 100
            print("Progress: " + f"{pctg:3.2f}" + " - Sent " + str(file_size_processing)
                  + " bytes out of " + str(file_size_total))
        # finalize
        print("Finalizing...")
        video_file.close()
        finalizedata = {
            "command": "FINALIZE",
            "media_id": media_id
        }
        finalizereq = requests.post(url=self.media_endpoint_url, data=finalizedata, auth=self.oauth)
        processing_info = finalizereq.json().get('processing_info', None)
        self.check_status(media_id, processing_info)

        # slam it down
        tweetdata = {
            "status": "",
            "media_ids": media_id
        }
        twreq = requests.post(url=self.tweet_endpoint_url, data=tweetdata, auth=self.oauth)
        print("Done!!!!!!!!")


class CohostAPI:
    def __init__(self):
        conf_file = open('config/cohost.json', "rt+")
        conf=json.load(conf_file)
        conf_file.close()
        self.url_base = conf["cohost"]["base_url"]
        self.username=conf["cohost"]["username"]
        self.account=conf["cohost"]["account"]
        self.password=conf["cohost"]["password"]
        pass

    def postImages(self, images_array):
        html_string = ''
        for i in images_array:
            url_of_image = self.url_base + i
            html_temp = "<img src='" + url_of_image + "' style='margin-top:1px; margin-bottom:1px'> "
            html_string = html_string + html_temp
        return html_string

    def postVideo(self, videofile):
        videos_url = '\n'+self.url_base + videofile+'\n'
        return videos_url

    def postToCohostSelenium(self, post_text):
        starting_line = 'https://cohost.org'
        login_button_main_page_xpath = '//*[@id="app"]/div/header/div/nav/a[1]'
        email_login_field = '//*[@id="login-form"]/div[1]/div/input'
        password_login_field = '//*[@id="login-form"]/div[2]/div/input'
        login_button = '//*[@id="login-form"]/button'
        email_addr = self.username
        ass_blaster = self.password
        post_button = '//*[@id="app"]/div/header/div/nav/a'
        account_dropdown = '/html/body/div[1]/div/div/header/div/nav/form[1]/select'
        account_dropdown_value = self.account
        post_textfield = '/html/body/div[1]/div/div/div/div[2]/div/div/div[2]/article/div/div/div/div[2]/div[2]/textarea'
        submit_post_button = '/html/body/div[1]/div/div/div/div[2]/div/div/div[2]/article/footer/div/div[3]/button[1]'
        #sample_text = 'https://micolithe.us/comedy-bang-bang-ooc/media/vids/silly-little-birds-muxed.mp4'
        log_out = '/html/body/div[1]/div/div/header/div/nav/form[2]/button'
        chromedriver_location = '/home/media/chrome-linux/chromedriver'
        chrome_opt=Options()
        chrome_opt.add_argument("--headless")
        chrome_opt.add_argument("--disable-gpu")
        chrome_opt.add_argument("--window-size=1920,1080")
        chrome_opt.add_argument("--start-maximized")
        drv = webdriver.Chrome(chromedriver_location,options=chrome_opt)
        drv.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36'})
        drv.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })

        drv.get(starting_line)
        time.sleep(10)
        # print(drv.page_source.encode('utf-8'))
        go_to_login = drv.find_element_by_xpath(login_button_main_page_xpath)
        go_to_login.click()
        time.sleep(10)
        login_textbox_uname = drv.find_element_by_xpath(email_login_field)
        time.sleep(1)
        login_textbox_uname.send_keys(email_addr)
        time.sleep(1)
        login_textbox_passwd = drv.find_element_by_xpath(password_login_field)
        login_textbox_passwd.send_keys(ass_blaster)
        time.sleep(5)
        login_button_element = drv.find_element_by_xpath(login_button)
        login_button_element.click()
        time.sleep(5)
        dropdown_sel = Select(drv.find_element_by_xpath(account_dropdown))
        dropdown_sel.select_by_visible_text(account_dropdown_value)
        time.sleep(5)
        make_a_poast_button = drv.find_element_by_xpath(post_button)
        make_a_poast_button.click()
        time.sleep(5)
        poasting_hole = drv.find_element_by_xpath(post_textfield)
        poasting_hole.send_keys(post_text)
        poasting_power = drv.find_element_by_xpath(submit_post_button)
        poasting_power.click()
        time.sleep(5)
        logout_button = drv.find_element_by_xpath(log_out)
        logout_button.click()
        time.sleep(1)
        drv.close()
