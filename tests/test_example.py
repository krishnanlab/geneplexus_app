from time import sleep

import pytest

from selenium.webdriver.common.by import By

# To run: py.test -s --driver Chrome --driver-path ./driver/chromedriver
# Current issue: getting an access denied on chrome

'''
Steps for setup (by browser):
    Safari:
        - Open Safari
        - If you have not yet, go to (in the menu) Safari -> Preferences -> Advanced -> Show Develop menu in menu bar
        - In the Develop menu make sure "Allow Remote Automation" is checked
        - Open a terminal and type "sudo safaridriver --enable" and enter your password if prompted
'''

# from https://pytest-flask.readthedocs.io/en/latest/features.html#start-live-server-start-live-server-automatically-default
@pytest.mark.usefixtures('live_server')
def test_homepage(selenium):
    print(selenium)
    selenium.get('http://127.0.0.1:5000/')
    sleep(10)
    print('\n---------------------------------------------------------------')
    print(selenium.title)
    print('---------------------------------------------------------------')
    geneBtn = selenium.find_element(By.ID, 'geneBtn')
    return True