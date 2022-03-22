# GenePlexus Testing Documentation

## To run

From a command line, in the base folder of this project enter `py.test -s` (the `-s` is only if you want to see print statements in tests)

**PLEASE NOTE**

Selenium tests will only work locally. You need to start a Flask server in a separate terminal (via `flask run`) before running tests

## Steps for setup by browser
- Safari:
    1. Open Safari
    2. If you have not yet, go to (in the menu) Safari -> Preferences -> Advanced -> Show Develop menu in menu bar
    3. In the Develop menu make sure "Allow Remote Automation" is checked
    4. Open a terminal and type "sudo safaridriver --enable" and enter your password if prompted
- Chrome:
    1. No setup needed
- Firefox:
    1. No setup needed

## Writing tests

Two different fixtures have been written to help with testing. A fixture can be used in a test by including the fixture name in the arguments for the test

- `client`
    - This is an instance of the flask app (not physically running). This can be used to test routes (such as GET and POST return values) as well as some of the internal functionality of the app (such as unit testing functions). Examples of how to use it can be found [here](https://flask.palletsprojects.com/en/2.0.x/testing/)
- `driver`
    - This is an instance of a Selenium Webdriver object. This allows you to simulate and test actions a user can physically perform on a page (such as ensuring a modal will pop up when a specific button is pressed). You can read more about it [here](https://selenium-python.readthedocs.io/)

Tests should be in files named `test_*.py` within the tests folder (where `*` is whatever you want to name that test file). From there you just add tests to the file by naming the test function `test_*` (once again, where `*` is whatever you want to name the test itself). When you run `py.test` from the base folder of this project then it will automatically pick up each test and run them individually.

An example of a test might be:

```python
# A test that will use the Selenium to see if a modal will pop up
@pytest.mark.dependency(name='modal_show')
def test_modal(driver):
    driver.get(url_for('index'))
    geneBtn = try_get_element(driver, By.ID, 'geneBtn')
    assert geneBtn is not None, 'Gene insert/upload button not found'
    geneBtn.click()
    geneModal = try_get_element(driver, By.ID, 'geneModal')
    assert geneModal is not None, 'Gene modal not found'
    sleep(1) # This is required so that Bootstrap can update the classes to add "show"
    modalClasses = geneModal.get_attribute('class').split(' ')
    assert 'show' in modalClasses, 'Modal not showing'
```