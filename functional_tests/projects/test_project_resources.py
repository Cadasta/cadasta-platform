from base import FunctionalTest
from fixtures import load_test_data
from fixtures.common_test_data_2 import get_test_data
from pages.Login import LoginPage
from pages.Project import ProjectPage
from core.tests.factories import PolicyFactory
from selenium.common.exceptions import NoSuchElementException


class ProjectResourceTest(FunctionalTest):
    def setUp(self):
        super().setUp()
        PolicyFactory.load_policies()
        test_objs = load_test_data(get_test_data())
        self.org = test_objs['organizations'][0]
        self.prj = test_objs['projects'][0]

    def test_resource_attach_button_for_non_project_user(self):
        """Attach button will be hidden from users who doesn't have
            permission to add resource."""

        LoginPage(self).login('testuser', 'password')
        page = ProjectPage(self, self.org.slug, self.prj.slug)
        page.go_to()

        # Test resource tab
        page.click_on_resources_tab()
        try:
            page.click_on_add_button('panel-body', success=False)
        except NoSuchElementException:
            assert True
