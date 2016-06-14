class ProjectRelationshipError(Exception):
    """Exception raised for illegal project on relationships.
    """
    def __init__(self, msg):
        super().__init__(msg)
