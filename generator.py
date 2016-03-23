from __future__ import print_function

import logging
import re
import sys

logger = logging


def to_camel_case(text):
    """ Convert text to CamelCase (for class name)"""
    def replace_func(matched):
        word = matched.group(0).strip("_").lower()
        prefix = word[0].upper()
        return prefix+word[1:]

    return re.sub(r'(_?[a-zA-Z]+)', replace_func, text)


def decode_shape(shape_code):
    """ Decode the 'shape' attribute in the metadata schema

    Parameters
    ----------
    shape_code : str

    Returns
    -------
    tuple

    Examples
    --------
    >>> decode_shape("(1:)")
    ((1, None),)

    >>> decode_shape("(:, :10)")
    ((None, None), (None, 10))
    """
    matched = re.finditer(r'([0-9+]):([0-9]+)|([0-9]+):|:([0-9]+)|([0-9]+)|[^0-9](:)[^0-9]',
                         shape_code)
    shapes = []
    
    for code in matched:
        min_size = code.group(1) or code.group(3) or code.group(5)
        min_size = int(min_size) if min_size else min_size
        max_size = code.group(2) or code.group(4) or code.group(5)
        max_size = int(max_size) if max_size else max_size
        shapes.append((min_size, max_size))
    return tuple(shapes)


def check_shape(value, shape):
    """ Check if `value` is a sequence that comply with `shape`

    Parameters
    ----------
    shape : str

    Returns
    -------
    None

    Raises
    ------
    ValueError
        if the `value` does not comply with the required `shape`
    """
    decoded_shape = decode_shape(shape)

    if len(decoded_shape) == 1:
        min_size, max_size = decoded_shape[0]
        size = len(value)
        is_valid =  ((size >= int(min_size) if min_size else True) and
                     (size <= int(max_size) if max_size else True))
    else:
        # FIXME:
        raise NotImplemented("Not dealing with multidimension yet")

    error_message = "{value} does not comply with shape: '{shape}'"

    if not is_valid:
        raise ValueError(error_message.format(value=value, shape=shape))


class CodeGenerator(object):

    def __init__(self, name, **kwargs):
        self.name = to_camel_case(name)

        # This collects import statements
        self.imports = []

        # parent is for class inheritance so it is handled separately
        # self.parent = ""; kwargs.pop("parent")    # for testing
        self.parent = kwargs.pop("parent")

        if self.parent is None or self.parent == "":
            self.parent = "object"

        elif self.parent.startswith("CUBA."):
            parent_name = self.parent[5:].lower()
            self.parent = to_camel_case(parent_name)
            self.imports.append("from simphony.meta.{0} import {1}".format(
                parent_name, self.parent))
        else:
            message = "'parent' should be either empty or a CUBA value, got {}"
            raise ValueError(message.format(self.parent))

        
        # This collects required __init__ arguments
        self.required_user_defined = []

        # This collects optional __init__ arguments
        # (i.e. with default values)
        self.optional_user_defined = {}

        # All statements within __init__
        self.init_body = [""]

        # All codes for methods
        self.methods = []

        # All CUBA keys that the code depends on
        # FIXME: So far it is not used anywhere except for book-keeping
        self.cuba_dependencies = []

        for key, contents in kwargs.items():
            # FIXME: Is there anything special that we need to do if
            # a property is a CUBA key (e.g. CUBA.DESCRIPTION in CUDS_COMPONENT
            if key.startswith("CUBA."):
                self.cuba_dependencies.append(key)            
                key = key[5:].lower()

            # If special generator method is defined, call it instead
            # e.g. for key == uuid: get_uuid() method is defined,
            # so we call that one
            auto_func_name = "gen_"+key
            if hasattr(self, auto_func_name):
                getattr(self, auto_func_name)(contents)
            else:
                self.gen_attribute(key, contents)

    def gen_attribute(self, key, contents):
        """ Dispatcher for populating code"""

        if not isinstance(contents, dict):
            # FIXME: the key has a single value, so is it read-only?
            if isinstance(contents, str) and " " in contents:
                # then it is likely to be a sentence
                contents = '"{}"'.format(contents)

            self.print_getter(key, value=contents)

        elif contents.get("default", ""):
            # the contents is a dict and has a default value
            # it is a property which user definition is optional
            value = contents["default"]

            # FIXME: if default value is a CUBA key, do we keep it as is?
            if isinstance(value, str) and value.startswith("CUBA."):
                self.imports.append("from simphony.core.cuba import CUBA")

            # append it so that the __init__ signature contains the key
            self.optional_user_defined.update({key: value})

            # __init__ body
            self.init_body.append("self.{key} = {key}".format(key=key))

            # property getter
            self.print_getter(key)

            # property setter
            if isinstance(contents, dict) and "shape" in contents:
                shape = contents["shape"]
                # FIXME: will need to import the check_shape function from somewhere!
                check_statements = "check_shape(value, '{shape}')".format(shape=shape)
                self.print_setter(key, check_statements)
            else:
                self.print_setter(key)

        else:
            # the property definition in the yaml is a dict and it has
            # no default value.  Unless the scope is CUBA.SYSTEM,
            # it should require user definition
            self.required_user_defined.append(key)

            # __init__ body
            self.init_body.append("self.{key} = {key}".format(key=key))

            # property getter
            self.print_getter(key)

            # property setter
            if isinstance(contents, dict) and "shape" in contents:
                shape = contents["shape"]
                check_statements = "check_shape(value, '{shape}')".format(shape=shape)
                self.print_setter(key, check_statements)
            else:
                self.print_setter(key)

    def gen_uuid(self, contents):
        """Populate code for CUBA.UUID"""
        self.imports.append("import uuid")

        self.methods.append('''
    @property
    def uuid(self):
        return uuid.uuid4()''')

    def print_getter(self, key, value=None):
        # default property getter
        if value is None:
            value = "self._{key}".format(key=key)

        self.methods.append('''
    @property
    def {key}(self):
        return {value}'''.format(key=key, value=value))

    def print_setter(self, key, check_statements=""):
        # default property setter
        self.methods.append('''
    @{key}.setter
    def {key}(self, value):
        {check_statements}
        self._{key} = value'''.format(key=key,
                                      check_statements=check_statements))

    def gen_data(self, contents):
        """Populate code for CUBA.DATA"""
        if contents:
            # FIXME: contents is not being used, what should we expect there?
            message = "provided value for DATA is currently ignored. given: {}"
            logger.warning(message.format(contents))

        self.imports.append(
            "from simphony.core.data_container import DataContainer")

        self.init_body.append("self._data = DataContainer()")

        self.methods.append('''
    @property
    def data(self):
        return DataContainer(self._data)''')

        self.methods.append('''
    @data.setter
    def data(self, new_data):
        self._data = DataContainer(new_data)''')

    def generate(self, file=sys.stdout):
        """ This is the main function for generating the code """
        # import statements
        print(*set(self.imports), sep="\n", file=file)

        # class header
        print('''

class {name}({parent}):'''.format(name=self.name,
                                  parent=self.parent),
              file=file)

        # __init__ signature
        kwargs = ["{key}={value}".format(key=key, value=value)
                  for key, value in self.optional_user_defined.items()]

        signature = ["self"] + self.required_user_defined + kwargs
        print('''
    def __init__({signature}):'''.format(
                signature=", ".join(signature)), file=file)

        # __init__ body
        if self.init_body == [""]:
            self.init_body.append("pass")
        print(*self.init_body, sep="\n        ", file=file)

        # methods (including descriptors)
        print(*self.methods, sep="\n", file=file)



if __name__ == "__main__":
    import yaml
    import os

    with open("simphony_metadata.yml", "rb") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)


    # create a "generated" directory if it does not already exist
    dirname = "generated"
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    for key, value in yaml_data["CUDS_KEYS"].items():
        # for each CUDS_KEYS, the code is written to `dirname`/
        # e.g. "generated/atomistic.py"
        filename = os.path.join(dirname, "{}.py".format(key.lower()))

        with open(filename, "wb") as output_file:
            try:
                gen = CodeGenerator(key, **value)
                gen.generate(file=output_file)
            except:
                # FIXME: Testing.  Excuse for this ugliness
                print(key, value)
                raise
