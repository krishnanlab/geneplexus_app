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

@pytest.mark.dependency(name='modal_show')
def test_modal(driver):
    driver.get('http://127.0.0.1:5000/')
    geneBtn = try_get_element(driver, By.ID, 'geneBtn')
    assert geneBtn is not None, 'Gene insert/upload button not found'
    geneBtn.click()
    geneModal = try_get_element(driver, By.ID, 'geneModal')
    assert geneModal is not None, 'Gene modal not found'
    sleep(1) # This is required so that Bootstrap can update the classes to add "show"
    modalClasses = geneModal.get_attribute('class').split(' ')
    assert 'show' in modalClasses, 'Modal not showing'

exampleGenes = ['CCNO','CENPF','LRRC56','ODAD3','DNAAF1','DNAAF6','DNAAF4','DNAH5','DNAH9','CFAP221','RSPH9',
    'FOXJ1','LRRC6','GAS2L2','DNAH1','GAS8','DNAI1','STK36','MCIDAS','RSPH4A','DNAAF3','DNAJB13','CCDC103','NME8',
    'ZMYND10','HYDIN','DNAAF5','CCDC40','ODAD2','DNAAF2','IFT122','INPP5E','CFAP298','DNAI2','SPAG1','SPEF2','ODAD4',
    'DNAL1','RSPH3','OFD1','CFAP300','CCDC65','DNAH11','RSPH1','DRC1','ODAD1']
@pytest.mark.dependency(name='sample_insert', depends=['modal_show'])
def test_sample_button(driver):
    driver.get('http://127.0.0.1:5000/')
    try_get_element(driver, By.ID, 'geneBtn').click()
    sleep(1)
    addExampleBtn = try_get_element(driver, By.ID, 'exampleGeneBtn')
    assert addExampleBtn is not None, 'Add example geneset button not found'
    addExampleBtn.click()
    inputGeneArea = try_get_element(driver, By.ID, 'enterGenes')
    assert inputGeneArea is not None, 'Sample gene area not found'
    inputGeneText = inputGeneArea.get_attribute('value').split('\n')
    assert inputGeneText == exampleGenes, 'Example gene list button did not product expected results'