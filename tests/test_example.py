import pytest

from selenium.webdriver.common.by import By

# To run: py.test -s --driver Chrome --driver-path ./driver/chromedriver
# Current issue: getting an access denied on chrome

# from https://pytest-flask.readthedocs.io/en/latest/features.html#start-live-server-start-live-server-automatically-default
@pytest.mark.usefixtures('live_server')
def test_homepage(selenium):
    selenium.get('http://127.0.0.1:5000/')
    print('\n---------------------------------------------------------------')
    print(selenium.title)
    print('---------------------------------------------------------------')
    geneBtn = selenium.find_element(By.ID, 'geneBtn')
    return True