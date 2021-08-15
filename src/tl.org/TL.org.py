#!/usr/bin/python3

'''
TL.org!ACHIEVEMENTS - helps you earn "Achievements" provided by TL.org
'''

from datetime import datetime
from hashlib import md5
from inspect import stack
from os import getcwd, listdir, path
from os.path import abspath, dirname, join
from random import choice, randint
from subprocess import call, check_output
from sys import argv, exit
from time import sleep
from urllib import request
# pip3 install python3-rapidjson
from rapidjson import dump, dumps, load
# pip3 install selenium
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.keys import Keys

# Global immutable Constants (don't touch!)
__UNITS__ = {'KiB': 1024**1, 'MiB': 1024**2, 'GiB': 1024**3, 'TiB': 1024**4}
# Link to the latest Google Chrome version (AMD64)
__CHROME__ = 'https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb'
# List of "Achievements" and their categories
# Thank the uploader 1000 times
__SHARE_THE_LOVE__ = {'enabled': True} # enabled by default
# Comment on 1000 torrents
__I_REALLY_LOVE_TALKING__ = {'enabled': False}
# Downloaded 1000 movies
__MOVIE_MANIAC__ = {'ids': [8,9,11,37,43,14,12,29,36], 'enabled': False}
# Downloaded 500 boxsets
__THE_COLLECTOR__ = {'ids': [15,27], 'enabled': False}
# Downloaded 1000 TV episodes
__TV_FREAK__ = {'ids': [26,32,44], 'enabled': False}
# Downloaded 1000 game releases
__GAME_MASTER__ = {'ids': [17,42,18,19,40,20,21,39,49,22,28,30,48], 'enabled': False}

class TLorg:

    def __init__(self, args: list = []):

        self.__PROJECT__ = 'TL.org!ACHIEVEMENTS'

        self.path = abspath(dirname(__file__))

        self.__VERSION__ = '1.1 (build 20210812)' # Check "CHANGELOG" for more information
        self.__GUI__ = '--gui' in args
        self.__DEBUG__ = True if '-d' in args else False

        self.print(f'{self.__PROJECT__} v{self.__VERSION__}')
        self.print('Checking Dependencies')
        try:
            chrome_version = check_output([
                'google-chrome-stable', '--version'
                ], encoding='UTF-8')
            self.print(f'Found: {chrome_version.strip()}')
            chrome_ver_major = chrome_version.split()[2].split('.')[0]
        except Exception as e:
            self.print(
                f'Google Chrome was no found on your system. Get the latest:\n'
                f'>>> wget {__CHROME__}')
            exit()
        driver = join('/'.join(self.path.split('/')[:-2]), 'drivers/chromedriver')
        try:
            driver_version = check_output([
                driver, '--version'
                ], encoding='UTF-8')
            self.print(f'Found: {driver_version.strip()}')
            driver_ver_major = driver_version.split()[1].split('.')[0]
        except:
            self.print(
                f'No ChromeDriver found. Get the latest:\n'
                f'>>> wget {self.get_latest_driver(chrome_ver_major)}')
            exit()
        if chrome_ver_major != driver_ver_major:
            self.print(
                f'ChromeDriver is out of date. Get the latest: {self.get_latest_driver(chrome_ver_major)}')
            exit()

        with open(join(self.path, 'settings.json'), 'r') as f:

            self.settings = load(f)

        self.hash = md5(dumps(self.settings, ensure_ascii=False).encode('utf8')).hexdigest()

        options = ChromeOptions()

        for opt in self.settings['driver']['weboptions']:
            if self.__GUI__ and opt == 'headless':
                continue
            options.add_argument(opt)
        try:
            self.driver = Chrome(driver, options=options)
        except Exception as e:
            print(f'{e}', end=''); exit() # Catch all exceptions, print the message and quit the app

    def __del__(self):

        '''
        This method closes the WebDriver connection
        '''

        if hasattr(self, 'driver'): self.driver.quit()

    def get_latest_driver(self, version):

        '''
        This method gets the latest ChromeDriver version
        '''

        r = request.urlopen(
            f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}')
        return f'https://chromedriver.storage.googleapis.com/{r.read().decode("utf-8")}/chromedriver_linux64.zip'

    def signin(self):

        '''
        This method signs into the TorrentLeech.org account
        '''

        self.print(f'Account: {self.settings["username"]}')

        self.driver.get(self.settings['domain'])

        uname = self.driver.find_element_by_name('username')
        uname.send_keys(self.settings['username'])
        pword = self.driver.find_element_by_name('password')

        pword.send_keys(self.settings['password'], Keys.ENTER); sleep(2)

    def fetch(self, categories):

        n = randint(2, 5 if categories[0] == 15 else 9) # How many torrents we'd grab
        self.print(
            f'Grab the next {n} .torrent files')
        torrents = []
        self.navigate(f'torrents/browse/index/categories/{chr(44).join(str(x) for x in categories)}')
        # Grab tthe next <b>n</b> .torrent threads from the search
        for t in self.driver.find_elements_by_class_name('torrent'):
            if n <= 0:
                break
            seeders = t.find_element_by_class_name('seeders').text
            tid = t.get_attribute('data-tid')
            v, u = t.find_element_by_class_name('size').text.split()
            size = float(v) * __UNITS__.get(u, 1)
            name = t.find_element_by_css_selector('.td-name .name a').text
            if tid in self.settings['torrents'] or int(seeders) < 2 or int(size) < 500 * 1024**2:
                continue
            n -= 1; torrents.append({'tid': tid, 'name': name, 'size': f'{v} {u}'})
        # Go through each .torrent release and perform enabled achievements
        for torrent in torrents:
            self.navigate(join('torrent', torrent['tid']))
            index = torrents.index(torrent)
            self.print(
                '({}) {} ({})'.format(
                    index, join(self.settings['domain'], join('torrent', torrent['tid'])), torrent['size']))
            sleep(3)
            self.driver.find_element_by_id(
                'detailsDownloadButton').click() # Download .torrent file
            if __SHARE_THE_LOVE__['enabled']:
                self.driver.find_element_by_class_name('thankYouButton').click()
            greetings = [
                'Thank You', 'Thanks!',
                'Always appreciated!',
                'Thanks so much!',
                'Thanks a million!',
                'You made my day!',
                'Thank you for the upload ;)',
                'Thank you for sharing!',
                'Thanks for the upload, i really appreciate it. Keep up the good work!',
                'Thank for great upload!',
                'You\'re awesome!', 'Thx for uploads!'
            ]
            sleep(3)
            #greetings = ['Guys! Guys! Guys!\n\nDon\'t be so stupid. If you just want to say Thanks, there\'s a button for that, use it or you will be muzzled when you get catched!\n\nRead It: https://forums.torrentleech.org/t/unable-to-make-comments-am-i-squelched/76151']
            if __I_REALLY_LOVE_TALKING__['enabled']:
                comment = self.driver.find_element_by_name('comments')
                comment.send_keys(choice(greetings)); sleep(2)
                self.driver.find_element_by_class_name('add-comment').click()
            tfiles = sorted(
                filter(lambda x: x.endswith('.torrent'), listdir(getcwd())), key=path.getmtime
            )
            if not len(tfiles): # No .torrent files -> Exception!
                self.print(f'Content: {listdir(getcwd())}')
            else:
                call(['mv', tfiles[-1], join(self.settings['lookup-dir'], tfiles[-1].replace('.torrent', '.gs'))])

        self.settings['torrents'].extend(x['tid'] for x in torrents)

    def navigate(self, url: str):

        self.driver.get(join(self.settings['domain'], url)); sleep(2)

    def run(self):

        '''
        This method starts the execution of all implemented and activated features
        '''

        self.signin() # Sign into the users's account
        # Get account statistics
        stats = self.driver.find_elements_by_css_selector('.menu-info span')
        self.print(
            f'Up: {stats[0].text}; Down: {stats[1].text}; TL-Points: {stats[5].text}')
        # Perform all Tasks
        for achievement in [__GAME_MASTER__, __MOVIE_MANIAC__, __TV_FREAK__, __THE_COLLECTOR__]:
            if not achievement['enabled']:
                continue
            try:
                self.fetch(achievement['ids'])
            except Exception as e:
                self.print(f'Got an exception: {e}')
                self.driver.save_screenshot(
                    f'tl.org-ex-{datetime.now().strftime("%H-%M-%S")}.png')
        # Visit the Forums, too! (Devotee)
        self.driver.get('https://forums.torrentleech.org/')
        # Save configuration
        if self.hash != md5(dumps(self.settings, ensure_ascii=False).encode('utf8')).hexdigest():

            if self.__DEBUG__:
                return

            with open(join(self.path, 'settings.json'), 'w') as f:

                dump(self.settings, f)

            self.print('Save settings to the file') # And exit, we're done!

    def print(self, message: str):

        '''
        This method customizes the build-in print function
        '''

        print(f'{datetime.now().strftime("%H:%M:%S")} [{stack()[1][3].replace("__", "")}] {message}')

def main():

    TLorg(argv[1:]).run()

if __name__ == "__main__": main() # TL.org!ACHIEVEMENTS v1.1 (build 20210812) | https://github.com/nschepsen
