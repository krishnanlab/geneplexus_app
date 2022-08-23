from time import sleep

from bs4 import BeautifulSoup

import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
import requests

@pytest.mark.dependency(name='test_index')
def test_cookies(client):
    response = client.get('/')
    assert response.status_code == 200, 'Index page returned a status code other than 200 ({})'.format(response.status_code)
    parsed = BeautifulSoup(response.data, 'html.parser')
    found_id = parsed.find('div', {'id': 'cookie-consent-container'})
    assert found_id is not None, 'Cookie container not found'
