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
    """
    matched = re.finditer(r'([0-9+]):([0-9]+)|([0-9]+):|:([0-9]+)|([0-9]+)',
                         shape_code)
    shapes = []
    
    for code in matched:
        min_size = code.group(1) or code.group(3) or code.group(5)
        max_size = code.group(2) or code.group(4) or code.group(5)
        shapes.append((min_size, max_size))
    return shapes


def check_shape(value, shape):
    """ Check if `value` is a sequence that comply with shape """
    # FIXME: this docstring please ^^^
    if len(shape) == 1:
        min_size, max_size = shape[0]
        return ((size >= int(min_size) if min_size else True) and
                (size <= int(max_size) if max_size else True))
    else:
        # FIXME:
        raise NotImplemented("Not dealing with multidimension yet")


class CodeGenerator(object):

    def __init__(self, name, **kwargs):
        self.name = to_camel_case(name)

        # parent is for class inheritance so it is handled separately
        self.parent = kwargs.pop("parent")

        if self.parent is None or self.parent == "":
            self.parent = "object"

        elif self.parent.startswith("CUBA."):
            self.parent = to_camel_case(self.parent[5:])

        else:
            message = "'parent' should be either empty or a CUBA value, got {}"
            raise ValueError(message.format(self.parent))

        # This collects import statements
        self.imports = []

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
        self.cuba_dependencies = []

        for key, contents in kwargs.items():
            # Book keeping what CUBA key the class depends on
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
        # If there is default value, those attributes are optional,
        # otherwise, they are required
        if isinstance(contents, dict) and contents.get("default", ""):
            self.optional_user_defined.update({key: contents["default"]})
            value = contents["default"]
        else:
            self.required_user_defined.append(key)
            value = key

        if isinstance(value, str) and " " in value:
            # then it is likely to be a sentence
            value = '"{}"'.format(value)

        # __init__ body
        # FIXME: do all attributes require descriptor methods?
        self.init_body.append("self._{key} = {value}".format(key=key,
                                                             value=value))
        # property getter
        self.methods.append('''
    @property
    def {key}(self):
        return self._key'''.format(key=key))

        # property setter
        if isinstance(contents, dict) and "shape" in contents:
            shape = contents["shape"]
            self.methods.append('''
    @data.setter
    def {key}(self, value):
            check_shape(value, {shape})
        self._{key} = value'''.format(shape=decode_shape(str(shape)), key=key))
        else:
            self.methods.append('''
    @data.setter
    def {key}(self, value):
        self._{key} = value'''.format(key=key))

    def gen_uuid(self, contents):
        """Populate code for CUBA.UUID"""
        self.imports.append("import uuid")

        self.methods.append('''
    @property
    def uuid(self):
        return uuid.uuid4()''')

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
        print(*self.init_body, sep="\n        ", file=file)

        # methods (including descriptors)
        print(*self.methods, sep="\n", file=file)



if __name__ == "__main__":
    import yaml
    with open("simphony_metadata.yml", "rb") as yaml_file:
        yaml_data = yaml.safe_load(yaml_file)

    all_import_statements = []

    for key, value in yaml_data["CUDS_KEYS"].items():
        try:
            gen = CodeGenerator(key, **value)
            gen.generate()
        except:
            print(key, value)
            raise
        all_import_statements.extend(gen.imports)
