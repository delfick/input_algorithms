import six

class Meta(object):
    """Holds information about some value"""
    everything = None
    format_options = None

    def __init__(self, everything, path, format_options=None):
        self._path = path
        if isinstance(self._path, six.string_types):
            self._path = [(self._path, "")]

        self.everything = everything
        self.format_options = format_options

    def indexed_at(self, index):
        return self.new_path([("", "[{0}]".format(index))])

    def at(self, val):
        return self.new_path([(val, "")])

    def new_path(self, part):
        """Return a new instance of this class with additional path part"""
        return self.__class__(self.everything, self._path + part)

    @property
    def second_last_key(self):
        """Return the value of the second last part of the path"""
        if len(self._path) > 1:
            return self._path[-2][0]

    @property
    def path(self):
        """Return the path as a string"""
        complete = []
        for part in self._path:
            if isinstance(part, six.string_types):
                name, extra = part, ""
            else:
                name, extra = part

            if name and complete:
                complete.append(".")
            if name or extra:
                complete.append("{0}{1}".format(name, extra))
        return "".join(complete)

    @property
    def source(self):
        """Return the source path of this value"""
        if not hasattr(self.everything, "source_for"):
            return "<unknown>"
        else:
            return self.everything.source_for(self._path)

    def delfick_error_format(self, key):
        """Format a string for display in a delfick error"""
        return "{{source={0}, path={1}}}".format(self.source, self.path)

