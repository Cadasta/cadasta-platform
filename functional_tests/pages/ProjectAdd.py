import re

from .base import Page
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class ProjectAddPage(Page):

    SUBPAGE_TYPES = ('geometry', 'details', 'permissions')
    TIMEOUT = 10
    path = '/projects/new/'

    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + self.path

        self.BY_CLASS = test.browser.find_element_by_class_name
        self.BY_CSS = test.browser.find_element_by_css_selector
        self.BYS_CSS = test.browser.find_elements_by_css_selector
        self.BY_ID = test.browser.find_element_by_id
        self.BY_TAG = test.browser.find_element_by_tag_name
        self.BY_XPATH = test.browser.find_element_by_xpath

    def is_on_page(self):
        """Returns True if user is on this page."""
        return self.test.get_url_path() == self.path

    def go_to(self):
        self.browser.get(self.url)
        return self

    def get_subpage_type(self):
        """Attempts tp determine the current subpage type
        ('geometry', 'details', or 'permissions') and returns it.
        Throws an exception if the type cannot be identified."""

        def get_class(item):
            return item.get_attribute('class')

        steps = self.BYS_CSS('.wizard .steps li')
        assert len(steps) == 3
        steps_class = list(map(get_class, steps))
        title = self.BY_TAG('h3').text

        if (
            'active' in steps_class[0] and
            'enabled' in steps_class[0] and
            steps_class[1] == '' and
            steps_class[2] == '' and
            title == "Draw project on map".upper()
        ):
            return self.SUBPAGE_TYPES[0]
        elif (
            'complete' in steps_class[0] and
            'enabled' in steps_class[0] and
            'active' in steps_class[1] and
            'enabled' in steps_class[1] and
            steps_class[2] == '' and
            title == "1. GENERAL INFORMATION".upper()
        ):
            return self.SUBPAGE_TYPES[1]
        elif (
            'complete' in steps_class[0] and
            'enabled' in steps_class[0] and
            'complete' in steps_class[1] and
            'enabled' in steps_class[1] and
            'active' in steps_class[2] and
            'enabled' in steps_class[2] and
            title == "Assign permissions to members".upper()
        ):
            return self.SUBPAGE_TYPES[2]
        else:
            raise AssertionError("Subpage type cannot be determined")

    def is_on_subpage(self, subpage_type):
        assert subpage_type in self.SUBPAGE_TYPES
        return self.get_subpage_type() == subpage_type

    # ------------------------
    # Geometry subpage methods

    def get_available_countries(self):
        return ('AU', 'BR', 'CN', 'US',)

    def set_geometry(self, country):
        assert country in self.get_available_countries()
        if country == 'AU':
            self.draw_rectangle(520, 330, 20, 20)
        if country == 'BR':
            self.draw_rectangle(250, 300, 20, 20)
        if country == 'CN':
            self.draw_rectangle(480, 240, 20, 20)
        if country == 'US':
            self.draw_rectangle(170, 220, 20, 20)

    def search_for_place(self, placename):
        """Searches for the specified place name using the
        map search feature."""

        assert self.is_on_subpage('geometry')

        # Click on search button and wait for input box to appear
        search = self.BY_CLASS('leaflet-pelias-control')
        search_input_wait = (By.CLASS_NAME, 'leaflet-pelias-input')
        self.test.click_through(search, search_input_wait)

        # Type in specified placename and wait for results to appear
        ActionChains(self.browser).send_keys(placename).perform()
        first_word = re.split('\W', placename, maxsplit=1)[0]
        search_results_wait = (By.XPATH, (
            "//ul[@class='leaflet-pelias-list' and " +
            "    ./li[1][" +
            "        @class='leaflet-pelias-result' and " +
            "        contains(.//text(), '{}')".format(first_word) +
            "    ]" +
            "]"
        ))
        try:
            WebDriverWait(self.browser, 60).until(
                EC.presence_of_element_located(search_results_wait)
            )
        except TimeoutException:
            self.test.get_screenshot()
            raise

        # Click on first result that appears, then close the search box
        self.BY_CSS('ul.leaflet-pelias-list li').click()
        self.BY_CLASS('leaflet-pelias-close').click()

    def draw_rectangle(self, x_offset, y_offset, width, height):

        assert self.is_on_subpage('geometry')

        # Click on draw rectangle button
        self.BY_CLASS('leaflet-draw-draw-rectangle').click()

        # Draw rectangle
        map_div = self.BY_ID('id_extents_extent_map')
        actions = ActionChains(self.browser)
        actions.move_to_element_with_offset(map_div, x_offset, y_offset)
        actions.click_and_hold()
        actions.move_by_offset(width, height)
        actions.release()
        actions.perform()

    def submit_geometry(self):
        assert self.is_on_subpage('geometry')
        submit_button = self.BY_CLASS('btn-primary')
        add_details_wait = (By.ID, 'id_details-organization')
        self.test.click_through(submit_button, add_details_wait)
        assert self.is_on_subpage('details')

    # -----------------------
    # Details subpage methods

    def get_org(self):
        assert self.is_on_subpage('details')
        select = Select(self.BY_ID('id_details-organization'))
        return select.first_selected_option.get_attribute('value')

    def set_org(self, slug):
        assert self.is_on_subpage('details')
        select_elem = self.BY_ID('id_details-organization')
        select = Select(select_elem)
        select.select_by_value(slug)
        select_elem.location_once_scrolled_into_view

    def set_name(self, name):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-name')
        form_field.clear()
        form_field.send_keys(name)

    def get_name(self):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-name')
        return form_field.get_attribute('value') or ''

    def get_access_toggle_widget_and_states(self):
        widget = self.BY_XPATH(
            "//div[" +
            "    ./input[" +
            "        @type='checkbox' and " +
            "        @name='details-access' and " +
            "        @data-toggle='toggle'" +
            "    ]"
            "]"
        )
        input_elem = widget.find_element_by_name('details-access')
        public_state = input_elem.get_attribute('data-offstyle')
        private_state = input_elem.get_attribute('data-onstyle')
        return {
            'widget': widget,
            'public': public_state,
            'private': private_state,
        }

    def set_access(self, access):
        assert self.is_on_subpage('details')
        assert access in ('private', 'public')
        toggle_info = self.get_access_toggle_widget_and_states()
        widget_class = toggle_info['widget'].get_attribute('class')
        if toggle_info[access] not in widget_class:
            script = "window.scrollBy(0, -window.scrollY);"
            self.browser.execute_script(script)
            toggle_info['widget'].click()

        def is_access_set():
            widget_class = toggle_info['widget'].get_attribute('class')
            assert toggle_info[access] in widget_class

        self.test.wait_for(is_access_set)

    def get_access(self):
        assert self.is_on_subpage('details')
        toggle_info = self.get_access_toggle_widget_and_states()
        widget_class = toggle_info['widget'].get_attribute('class')
        return (
            'public' if toggle_info['public'] in widget_class else 'private'
        )

    def set_description(self, description):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-description')
        form_field.clear()
        form_field.send_keys(description)

    def get_description(self):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-description')
        return form_field.get_attribute('value') or ''

    def set_proj_url(self, url):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-url')
        form_field.clear()
        form_field.send_keys(url)

    def get_proj_url(self):
        assert self.is_on_subpage('details')
        form_field = self.BY_ID('id_details-url')
        return form_field.get_attribute('value') or ''

    def set_questionnaire(self, filename):
        assert self.is_on_subpage('details')

    def get_questionnaire(self):
        assert self.is_on_subpage('details')

    def check_details(self, details):
        """Checks whether the details form shows the expected data."""
        assert self.get_org() == details['org']
        assert self.get_name() == details['name']
        assert self.get_access() == details['access']
        assert self.get_description() == details['description']
        assert self.get_proj_url() == details['url']

    def click_submit_details(self):
        submit_button = self.BY_CLASS('btn-primary')
        submit_button.click()

    def click_previous_details(self):
        previous_button = self.BY_CLASS('btn-details-previous')
        self.test.click_through(previous_button,
                                (By.CLASS_NAME, 'project-extent-map'))

    def try_submit_details(self):
        """This method should be called when the details form has at
        least one error. The method will attempt to submit the already
        set details and verify that an error is issued."""
        assert self.is_on_subpage('details')
        submit_button = self.BY_CLASS('btn-primary')
        error_wait = (By.CLASS_NAME, 'error-block')
        self.test.click_through(submit_button, error_wait)
        assert self.is_on_subpage('details')

    def get_error_list(self, id, message, field='input'):
        field = self.browser.find_element_by_xpath(
            "//div[contains(@class, 'has-error')]/" +
            "{field}[@id='{id}']".format(field=field, id=id))
        error = field.find_element_by_xpath(
            "..//div[contains(@class, 'error-block')]")
        if error.text == '':
            error = field.find_element_by_xpath(
                "..//ul[contains(@class, 'parsley-errors-list')]")
        print("<error.text> " + error.text + " != <message> " + message)
        assert error.text == message

    def check_missing_org_error(self):
        # Assert that there is a missing org error message
        assert self.is_on_subpage('details')
        self.get_error_list(
            id='id_details-organization',
            message='This field is required.',
            field='select')

    def check_no_missing_org_error(self):
        # Assert that there is NO missing org error message
        try:
            self.check_missing_org_error()
            raise AssertionError(
                "There should be no missing org error message.")
        except NoSuchElementException:
            pass

    def check_missing_name_error(self):
        # Assert that there is a missing project name error message
        assert self.is_on_subpage('details')
        self.get_error_list(
            id='id_details-name',
            message='This field is required.')

    def check_no_missing_name_error(self):
        # Assert that there is NO missing project name error message
        try:
            self.check_missing_name_error()
            raise AssertionError(
                "There should be no missing project name error message.")
        except (NoSuchElementException, AssertionError):
            pass

    def check_duplicate_name_error(self):
        # Assert that there is a duplicate project name error message
        assert self.is_on_subpage('details')
        message = "Project with this name already exists in this organization."
        self.get_error_list(
            id='id_details-name',
            message=message)

    def check_no_duplicate_name_error(self):
        # Assert that there is NO duplicate project name error message
        try:
            self.check_duplicate_name_error()
            raise AssertionError(
                "There should be no duplicate project name error message.")
        except (NoSuchElementException, AssertionError):
            pass

    def check_invalid_url_error(self):
        # Assert that there is an invalid URL error message
        assert self.is_on_subpage('details')
        self.get_error_list(
            id='id_details-url',
            message="This value should be a valid url.")

    def check_no_invalid_url_error(self):
        # Assert that there is NO invalid URL error message
        try:
            self.check_invalid_url_error()
            raise AssertionError(
                "There should be no invalid URL error message.")
        except NoSuchElementException:
            pass

    def submit_details(self):
        assert self.is_on_subpage('details')
        submit_button = self.BY_CLASS('btn-primary')
        next_header = "Assign permissions to members"
        xpath = "//h3[text()='{}']".format(next_header)
        set_perms_wait = (By.XPATH, xpath)
        self.test.click_through(submit_button, set_perms_wait)
        assert self.is_on_subpage('permissions')

    # ---------------------------
    # Permissions subpage methods

    def submit_permissions(self):
        assert self.is_on_subpage('permissions')

        # TODO: temporary workaround for #206
        script = (
            'document.getElementsByTagName("footer")' +
            '[0].style.display = "none"'
        )
        self.browser.execute_script(script)

        submit_button = self.BY_CLASS('btn-primary')
        next_header = "Project Overview"
        xpath = "//h2[text()='{}' and not(*[2])]".format(next_header)
        proj_overview_wait = (By.XPATH, xpath)
        self.test.click_through(submit_button, proj_overview_wait)
        assert not self.is_on_page()
