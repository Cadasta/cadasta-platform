class Page:
    def __init__(self, test):
        self.test = test
        self.base_url = test.live_server_url
        self.browser = test.browser
