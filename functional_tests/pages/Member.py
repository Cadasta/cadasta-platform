from .base import Page


class MemberPage(Page):
    def __init__(self, test):
        super().__init__(test)
        self.url = self.base_url + '/organizations/{}/members/testuser/'

    def go_to(self, org):
        self.browser.get(self.url.format(org))
        self.test.wait_for(self.get_form)
        return self

    def get_form(self):
        return self.test.form('org-member-edit')

    def get_form_field(self, xpath):
        return self.test.form_field(
            'org-member-edit', xpath)

    def get_button(self, f):
        return self.test.button(f)

    def get_link(self, f):
        return self.test.link(f)

    def get_table_body(self, xpath):
        return self.test.table_body('DataTables_Table_0', xpath)

    def get_member_info(self):
        return self.get_form_field("div[contains(@class, 'member-info')]")

    def get_member_role_select(self, xpath):
        return self.get_form_field(
            "select[contains(@id, 'id_org_role')]" + xpath)

    def get_member_option(self):
        return self.get_member_role_select("//option[contains(@value, 'M')]")

    def get_admin_option(self):
        return self.get_member_role_select("//option[contains(@value, 'A')]")

    def get_selected_option(self):
        return self.get_member_role_select(
            "//option[contains(@selected, 'selected')]")

    def get_role_options(self):
        return {
            "member": self.get_member_option(),
            "admin": self.get_admin_option(),
            "selected": self.get_selected_option()
        }

    def get_members_row(self, member):
        return self.get_table_body("//tr" + member)

    def get_projects_table(self, xpath):
        return self.test.table_body("projects-permissions", xpath)

    def get_project_permission(self, xpath):
        return self.get_projects_table("//select" + xpath)

    def get_project_user(self):
        return self.get_project_permission("//option[contains(@value, 'PU')]")

    def get_data_collector(self):
        return self.get_project_permission("//option[contains(@value, 'DC')]")

    def get_project_manager(self):
        return self.get_project_permission("//option[contains(@value, 'PM')]")

    def get_public_user(self):
        return self.get_project_permission("//option[contains(@value, 'Pb')]")

    def get_selected_permission(self):
        return self.get_project_permission(
            "//option[contains(@selected, 'selected')]")

    def get_permission_options(self):
        return {
            'pu':       self.get_project_user(),
            'dc':       self.get_data_collector(),
            'pm':       self.get_project_manager(),
            'pb':       self.get_public_user(),
            'selected': self.get_selected_permission()
        }
