"""
Overrides JSONEncoder to serialize customize class
"""

from json import JSONEncoder

class Encoder(JSONEncoder):
    """Class Encoder to override JSONEncoder"""
    def default(self, o):
        """Overrides the default method of json to serialize customize class with their __dict__"""
        return o.__dict__
