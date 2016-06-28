class SpatialRelationshipError(Exception):
    """Exception raised for illegal location relationship assignment.
    """
    def __init__(self, msg):
        super().__init__("illegal relationship: " + msg)
