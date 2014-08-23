import six

class Meta(object):
    """Holds information about some value"""
    def __init__(self, everything, path):
        self._path = path
        if isinstance(self._path, six.string_types):
            self._path = [(self._path, "")]

        self.everything = everything

    def indexed_at(self, index):
        return self.new_path([("", "[{0}]".format(index))])

    def at(self, val):
        return self.new_path([(val, "")])

    def new_path(self, part):
        """Return a new instance of this class with additional path part"""
        return self.__class__(self.everything, self._path + part)

    @property
    def path(self):
        """Return the path as a string"""
        complete = []
        for name, extra in self._path:
            if name and complete:
                complete.append(".")
            if name or extra:
                complete.append("{0}{1}".format(name, extra))
        return "".join(complete)

    @property
    def source(self):
        """Return the source path of this value"""
        if not hasattr(self.everything, "source_for"):
            return "<unknown>({0})".format(self.path)
        else:
            return self.everything.source_for(self._path)

    def delfick_error_format(self, key):
        """Format a string for display in a delfick error"""
        return "{{source={0}, path={1}}}".format(self.source, self.path)

