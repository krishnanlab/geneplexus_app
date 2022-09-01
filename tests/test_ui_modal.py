from time import sleep

import pytest
from os import path, environ

from selenium import webdriver
from selenium.webdriver.common.by import By
import requests

exampleGenes = ['CCNO','CENPF','LRRC56','ODAD3','DNAAF1','DNAAF6','DNAAF4','DNAH5','DNAH9','CFAP221','RSPH9',
    'FOXJ1','LRRC6','GAS2L2','DNAH1','GAS8','DNAI1','STK36','MCIDAS','RSPH4A','DNAAF3','DNAJB13','CCDC103','NME8',
    'ZMYND10','HYDIN','DNAAF5','CCDC40','ODAD2','DNAAF2','IFT122','INPP5E','CFAP298','DNAI2','SPAG1','SPEF2','ODAD4',
    'DNAL1','RSPH3','OFD1','CFAP300','CCDC65','DNAH11','RSPH1','DRC1','ODAD1']

@pytest.fixture(scope='module')
def example_gene_file():
    ### NOTE: there must be a file in the tests folder called "example_genes_file.txt" which MUST have the 
    ### last item end with a newline and no extra new lines.  otherwise test will fail

    import shlex

    example_genefile_name = 'example_gene_file.txt' 
    example_genefile_path = path.join( path.dirname(path.realpath(__file__)), example_genefile_name )

    #just check that the example gene file is here and has stuff in it
    if not path.exists(example_genefile_path):
        pytest.fail(f"can't find example gene file {example_genefile_path}")

    with open(example_genefile_path) as f:
        genes = shlex.split(f.read())
    if len(genes) == 0:
        pytest.fail(" no genes in example genefile")
    
    yield example_genefile_path
    

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
@pytest.mark.ui
def test_ui_modal(driver):
    driver.get('http://127.0.0.1:5000/')
    geneBtn = try_get_element(driver, By.ID, 'geneBtn')
    assert geneBtn is not None, 'Gene insert/upload button not found'
    geneBtn.click()
    geneModal = try_get_element(driver, By.ID, 'geneModal')
    assert geneModal is not None, 'Gene modal not found'
    sleep(1) # This is required so that Bootstrap can update the classes to add "show"
    modalClasses = geneModal.get_attribute('class').split(' ')
    assert 'show' in modalClasses, 'Modal not showing'

@pytest.mark.dependency(name='sample_insert', depends=['modal_show'])
@pytest.mark.ui
def test_ui_sample_button(driver):
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

@pytest.mark.dependency(name='upload_file', depends=['modal_show'])
@pytest.mark.ui
def test_ui_modal_upload(driver, example_gene_file):
    """ test opening model, clicking load buttons, pasting text and uploading from a file"""

    # driver.get('http://127.0.0.1:5000/')

    # manually clear any existing input
    clearBtn = try_get_element(driver, By.ID, 'clearButton')
    assert clearBtn is not None, "Clear button not found, can't test upload"
    clearBtn.click()
    sleep(1)
    
    uploadInput = try_get_element(driver, By.ID, "insertGenesInput")
    assert uploadInput is not None, 'Could not find the upload button'

    #uploadInput is not a button and not click-able, just send the file path
    uploadInput.send_keys(example_gene_file)
    sleep(1) # give time to read the file
    inputGeneArea = try_get_element(driver, By.ID, 'enterGenes')
    
    print(inputGeneArea)

    inputGeneText = inputGeneArea.get_attribute('value').split('\n')

    assert inputGeneText == exampleGenes

@pytest.mark.dependency(name='enter_genes', depends=['modal_show'])
@pytest.mark.ui
def test_ui_modal_entry(driver):
    driver.get('http://127.0.0.1:5000/')
    inputGeneBtn = try_get_element(driver, By.ID, 'geneBtn').click()
    sleep(1)
    inputGeneArea = try_get_element(driver, By.ID, 'enterGenes')
    assert inputGeneArea is not None, 'Sample gene area not found'
    addExampleBtn = try_get_element(driver, By.ID, 'exampleGeneBtn')
    addExampleBtn.click()

    inputGeneText = inputGeneArea.get_attribute('value').split('\n')
    assert inputGeneText == exampleGenes, 'Example gene list button did not product expected results'


@pytest.mark.dependency(name='download_file', depends=['modal_show'])
@pytest.mark.ui
def test_ui_modal_download(driver):
    driver.get('http://127.0.0.1:5000/')
    inputGeneBtn = try_get_element(driver, By.ID, 'geneBtn').click()
    sleep(1)
    downloadBtn = try_get_element(driver, By.ID, 'sampleBtn')
    assert downloadBtn is not None, 'Link to download a sample list cannot be found'
    payload = requests.get(downloadBtn.get_attribute('href'))
    assert payload.status_code == 200, 'Sample download link returned a bad request status code: {}'.format(payload.status_code)

@pytest.mark.dependency(name='test_clear', depends=['modal_show', 'sample_insert'])
@pytest.mark.ui
def test_ui_clear_input(driver):
    driver.get('http://127.0.0.1:5000/')
    try_get_element(driver, By.ID, 'geneBtn').click()
    sleep(1)
    addExampleBtn = try_get_element(driver, By.ID, 'exampleGeneBtn')
    addExampleBtn.click()
    clearBtn = try_get_element(driver, By.ID, 'clearButton')
    assert clearBtn is not None, 'Clear button not found'
    clearBtn.click()
    inputGeneArea = try_get_element(driver, By.ID, 'enterGenes')
    inputGeneText = inputGeneArea.get_attribute('value')
    assert inputGeneText == '', 'Clear button did not clear out all text'