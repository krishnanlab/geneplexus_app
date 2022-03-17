from time import sleep

import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By

# Browsers can sometimes load elements into the page slowly because of Javascript so this is a way to be tolerant of that
def try_get_element(driver, element_type: By, element_name: str, max_attempts: int = 3, wait_interval: float = 1.0):
    for _ in range(max_attempts):
        try:
            element = driver.find_element(element_type, element_name)
        except Exception as e:
            sleep(wait_interval)
            continue
        return element
    return None

def test_show_modal(driver):
    driver.get('http://127.0.0.1:5000/')
    geneBtn = try_get_element(driver, By.ID, 'geneBtn')
    assert geneBtn is not None, 'Gene insert/upload button not found'
    geneBtn.click()
    geneModal = try_get_element(driver, By.ID, 'geneModal')
    assert geneModal is not None, 'Gene modal not found'
    sleep(1) # This is required so that Bootstrap can update the classes to add "show"
    modalClasses = geneModal.get_attribute('class').split(' ')
    assert 'show' in modalClasses, 'Modal not showing'