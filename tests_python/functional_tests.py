import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class TestAdmin:

    def element_is_on_page(self, element_id):
        try:
            self.browser.find_element(By.ID, element_id)
            return True
        except NoSuchElementException:
            return False

    def setup_method(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        chrome_driver_manager = ChromeDriverManager().install()
        self.browser = webdriver.Chrome(service=ChromeService(chrome_driver_manager), options=options)

    def teardown_method(self):
        self.browser.quit()

    def test_admin_needs_login(self):

        # access the admin page
        self.browser.get("http://localhost:5001/admin/")

        # get presented with the login page
        assert self.element_is_on_page('email') is True
        assert self.element_is_on_page('password') is True
        assert self.element_is_on_page('submit') is True

        # login
        username = 'test1@example.co.uk'
        password = 'xyzxyz123'
        self.browser.find_element(By.ID, "email").send_keys(username)
        self.browser.find_element(By.ID, "password").send_keys(password)
        self.browser.find_element(By.ID, "submit").click()

        # get the admin dashboard
        assert "Admin Dashboard" in self.browser.page_source
