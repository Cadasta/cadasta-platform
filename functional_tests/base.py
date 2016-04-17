from django.contrib.staticfiles.testing import StaticLiveServerTestCase

import time
import re
import os
import os.path
import shutil
import base64

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException, TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FunctionalTest(StaticLiveServerTestCase):
    DEFAULT_WAIT = 5

    BY_ALERT = (By.CLASS_NAME, 'alert')
    BY_MODAL = (By.CLASS_NAME, 'modal-content')
    BY_MODAL_FADE = (By.CSS_SELECTOR, "div.modal.fade.in")
    BY_ORG_MEMBERS = (By.CLASS_NAME, 'members-org-name')
    BY_MEMBER_PAGE = (By.CLASS_NAME, 'org-member-edit')
    BY_ORG_DASH = (By.CLASS_NAME, 'dashboard-org-name')
    BY_NEW_PROJ = (By.CLASS_NAME, 'new-project-page')

    @classmethod
    def setUpClass(cls):
        super(FunctionalTest, cls).setUpClass()

        # IMPORTANT: Make sure the window size is big enough to see
        # everything (e.g. links in the nav bar).  Otherwise tests
        # will fail mysteriously because PhantomJS will clip the
        # viewport.
        cls.browser = webdriver.Firefox()
        cls.browser.set_window_size(1024, 768)

        cls.screenshot_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'screenshots'
        )
        if os.path.exists(cls.screenshot_dir):
            shutil.rmtree(cls.screenshot_dir)
        os.makedirs(cls.screenshot_dir, exist_ok=True)
        cls.screenshot_index = 1

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super(FunctionalTest, cls).tearDownClass()

    def container(self, field):
        """Find container"""
        return self.browser.find_element_by_xpath(
            "//div[contains(@class, 'container')]" + field)

    def form(self, f):
        """Find a form of a given class."""
        return self.browser.find_element_by_xpath(
            "//form[contains(@class,'{}')]".format(f)
        )

    def form_field(self, f, field):
        """Find a field in a form of a given class."""
        return self.form(f).find_element_by_xpath("//" + field)

    def table(self, f):
        """Find a table of a given class."""
        return self.browser.find_element_by_xpath(
            "//table[contains(@id, '{}')]".format(f)
        )

    def table_head(self, f, field):
        """Find the head in a table."""
        return self.table(f).find_element_by_xpath("//thead" + field)

    def table_body(self, f, field):
        """Find the body in a table."""
        return self.table(f).find_element_by_xpath("//tbody" + field)

    def search_box(self, f):
        """Find the search box connected to table"""
        return self.browser.find_element_by_xpath(
            "//div[contains(@id, '{}_filter')]//input".format(f))

    def link(self, f):
        """Find a link with a specific class"""
        return self.browser.find_element_by_xpath(
            "//a[contains(@class, '{}')]".format(f))

    def button(self, f):
        """Find a button with a specific name"""
        return self.browser.find_element_by_xpath(
            "//button[@name='{}']".format(f))

    def button_class(self, f):
        """Find a button with a specific class"""
        return self.browser.find_element_by_xpath(
            "//button[contains(@class, '{}')]".format(f))

    def modal(self):
        """Find a modal with a specific title"""
        return self.browser.find_element_by_xpath(
            "//div[contains(@class, 'modal-content')]"
            )

    def organization_name(self, f):
        """Find organization name in dashboard"""
        return self.browser.find_element_by_xpath(
         "//h1[contains(@class, '{}')]".format(f))

    def wait_for(self, function_with_assertion, timeout=DEFAULT_WAIT):
        """Wait for an assertion to become true."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                return function_with_assertion()
            except (AssertionError, WebDriverException):
                time.sleep(0.1)
        return function_with_assertion()

    def click_through(self, button, wait, screenshot=None):
        """Click a button or link and wait for something to appear."""
        button.click()
        if screenshot is not None:
            self.screenshot(screenshot)
        try:
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(wait)
            )
        except TimeoutException as exc:
            with open('exception.png', 'wb') as f:
                f.write(base64.b64decode(exc.screen))
            raise

    def click_through_close(self, button, wait, screenshot=None):
        """Click a button or link and wait for something to appear."""
        button.click()
        if screenshot is not None:
            self.screenshot(screenshot)
        try:
            WebDriverWait(self.browser, 10).until_not(
                EC.presence_of_element_located(wait)
            )
        except TimeoutException as exc:
            with open('exception.png', 'wb') as f:
                f.write(base64.b64decode(exc.screen))
            raise

    def wait_for_no_alerts(self):
        """Wait for all alerts to be cleared by a page reload."""
        WebDriverWait(self.browser, 10).until_not(
            EC.presence_of_element_located((By.CLASS_NAME, 'alert'))
        )

    # if all forms are going to have has-error, this won't be necessary.
    def assert_has_error_list(self):
        """Check for the presence of an error list containing given text."""
        assert self.browser.find_element_by_xpath(
            "//ul[contains(@class, 'errorlist')]"
        )

    def assert_has_message(self, msg_type, msg):
        """Check for the presence of a message of a particular type containing
        given text.

        """
        msgs = self.browser.find_element_by_xpath("//div[@id='messages']")
        try:
            msgs.find_element_by_xpath(
                ("div[contains(@class,'{}') and contains(.,'{}')]").
                format(msg_type, msg)
            )
        except NoSuchElementException as e:
            # Debugging help.
            print("Messages: " + msgs.text)
            raise e

    def assert_field_has_error(self, field):
        """Check whether a form field has an error marker: this will be a
        ``has_error`` class on the field's immediate parent.

        """
        cls = field.find_element_by_xpath('..').get_attribute('class')
        assert re.search(r'\bhas-error\b', cls)

    def assert_field_has_no_error(self, field):
        """Check that a form field has no error marker: this will be a
        ``has_error`` class on the field's immediate parent.

        """
        cls = field.find_element_by_xpath('..').get_attribute('class')
        assert not re.search(r'\bhas-error\b', cls)

    def screenshot(self, title=None):
        if title is not None:
            f, _ = unique_file(self.screenshot_dir, title, 1)
        else:
            f, self.screenshot_index = unique_file(self.screenshot_dir,
                                                   'screenshot',
                                                   self.screenshot_index)
        self.browser.save_screenshot(f)

    def xpath(self, tag, contents):
        return "//{}[normalize-space(.)='{}']".format(tag, contents)


def unique_file(dir, base, startidx):
    f = os.path.join(dir, base + '.png')
    idx = startidx
    if os.path.exists(f):
        f = os.path.join(dir, base + '-{:04d}.png'.format(idx))
        while os.path.exists(f):
            idx = idx + 1
            f = os.path.join(dir, base + '-{:04d}.png'.format(idx))
    return f, idx
