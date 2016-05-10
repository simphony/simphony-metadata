from __future__ import print_function

import inspect
import os
import re
import shutil
import tempfile
import warnings
from collections import OrderedDict
from contextlib import contextmanager
from itertools import chain, count

import click
import yaml


# May be 'simphony.meta', we can make this as a command-line attribute
PATH_TO_CLASSES = ''

IMPORT_PATHS = {
    'CUBA': 'from simphony.core.cuba import CUBA',
    'DataContainer': 'from simphony.core.data_container import DataContainer',
    'KEYWORDS': 'from simphony.core.keywords import KEYWORDS',
    'validation': 'from . import validation'
    }

# These are keys that are read-only
# (see wiki page on simphony metadata schema)
READ_ONLY_KEYS = ('definition', 'models', 'variables', 'uuid')

# Directory where this file is
THIS_DIR = os.path.split(inspect.getfile(inspect.currentframe()))[0]

# Other files to be copied
FILES_TO_COPY = (os.path.join(THIS_DIR, 'validation.py'),)

# keywords that are excludes from DataContainers
CUBA_DATA_CONTAINER_EXCLUDE = ['Id', 'Position']


@contextmanager
def make_temporary_directory():
    ''' Context Manager for creating a temporary directory
    and remove the tree on exit

    Yields
    ------
    temp_dir : str
        absolute path to temporary directory
    '''
    try:
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


def to_camel_case(text, special={'cuds': 'CUDS'}):
    """ Convert text to CamelCase (for class name)

    Parameters
    ----------
    text : str
        The text to be converted

    special : dict
        If any substring of text (lower case) matches a key of `special`,
        the substring is replaced by the value
    """

    def replace_func(matched):
        # word should be lower case already
        word = matched.group(0).strip("_")
        if word in special:
            # Handle special case
            return special[word]
        else:
            # Capitalise the first character
            return word[0].upper()+word[1:]

    return re.sub(r'(_?[a-zA-Z]+)', replace_func, text.lower())


def transform_cuba_string(code):
    ''' Tranform any \'CUBA.SOMETHING\' in a string to CUBA.SOMETHING

    Parameters
    ----------
    code : str
    '''
    code = repr(code)
    return re.sub('\'(CUBA.\w+)\'', lambda x: x.group(0).strip("'"), code)


def is_system_managed(key, contents):
    ''' Return True is `key` is a system-managed attribute

    Criteria:
    (1) It is defined in `READ_ONLY_KEYS`  OR
    (2) contents['scope'] is CUBA.SYSTEM

    Parameters
    ----------
    key : str
    '''
    # If attribute is read-only, it is system-defined
    if key.replace('CUBA.', '').lower() in READ_ONLY_KEYS:
        return True

    # If the scope of the attribute is 'CUBA.SYSTEM', it is
    # also system-defined
    if isinstance(contents, dict) and contents.get('scope') == 'CUBA.SYSTEM':
        return True

    return False


class CodeGenerator(object):

    def __init__(self, key, class_data):

        # We keep a record of the original key
        self.original_key = key

        # We keep a record of the whole class data
        self.class_data = class_data

        # This collects import statements
        self.imports = [IMPORT_PATHS['CUBA'],
                        IMPORT_PATHS['validation']]

        # parent is for class inheritance so it is handled separately
        # self.parent = ""; class_data.pop("parent")    # for testing
        self.parent = class_data.pop('parent', None)

        if self.parent and not self.parent.startswith('CUBA.'):
            message = "'parent' should be either empty or a CUBA value, got {}"
            raise ValueError(message.format(self.parent))

        if self.parent:
            self.parent = self.parent.replace('CUBA.', '')

            self.imports.append("from {0}.{1} import {2}".format(
                PATH_TO_CLASSES, self.parent.lower(),
                to_camel_case(self.parent)))

        else:
            self.parent = "object"

        # This collects required __init__ arguments that are defined
        # by the corresponding metadata (not inherited)
        self.required_user_defined = OrderedDict()

        # This collects the required __init__ arguments that are
        # inherited
        self.inherited_required = OrderedDict()

        # This collects optional __init__ arguments (not inherited)
        # (i.e. with default values)
        self.optional_user_defined = OrderedDict()

        # This collects optional __init__ arguments that are inherited
        self.inherited_optional = OrderedDict()

        # Readonly variables managed by the system
        self.system_variables = {}

        # All statements within __init__
        self.init_body = [""]

        # All codes for methods
        self.methods = []

        # Method Resolution Order as defined by the simphony metadata
        # Note: assumed no multi-inheritance
        self.mro = []

        # Flag for whether the MRO is completed
        self.mro_completed = False

        for key, contents in class_data.items():
            key = key.lower().replace('cuba.', '')

            if is_system_managed(key, contents):
                self.system_variables[key] = contents

            elif isinstance(contents, dict) and 'default' in contents:
                if contents['default'] == []:
                    contents['default'] = None

                self.optional_user_defined[key] = contents

            else:
                self.required_user_defined[key] = contents

    def populate_system_code(self):
        """ Populate code for system-managed (and read-only) attributes"""

        for key, contents in self.system_variables.items():
            # We first search for CodeGenerator.populate_`key`
            # If the method is defined, that is used and then move on
            if hasattr(self, 'populate_'+key):
                getattr(self, 'populate_'+key)(contents)
                continue

            # Populates self.methods with getter
            self.populate_getter(key)

            if isinstance(contents, dict):
                # Populate self.methods with setter
                self.populate_setter_with_validation(key, contents)

                # We will defined private variable so that the system
                # can modify it but the user is not supposed to
                self.init_body.extend([
                    "",
                    '# This is a system-managed, read-only attribute',
                    'self._{0} = None'.format(key)])

            else:
                # This should be rare and would only apply to keys in `READ_ONLY`,
                # as most system-managed attributes are defined by
                # `scope : CUBA.SYSTEM` and hence `contents` would
                # be a dict.  But keys in `READ_ONLY` are read-only because
                # we hold it so, not because we could tell from the yaml file
                self.init_body.extend([
                    "",
                    '# This is a system-managed, read-only attribute',
                    'self._{0} = {1}'.format(key, transform_cuba_string(contents))])

        # Add a cuba_key property
        self.populate_getter('cuba_key', value='CUBA.{}'.format(self.original_key))

        # Add a parents property
        self.populate_getter('parents',
                             value=transform_cuba_string(
                                 tuple('CUBA.{}'.format(parent)
                                       for parent in self.mro)))

    def populate_user_variable_code(self):
        """ Populate code for user-defined attributes """

        for key, contents in chain(self.inherited_required.items(),
                                   self.required_user_defined.items(),
                                   self.inherited_optional.items(),
                                   self.optional_user_defined.items()):
            if hasattr(self, 'populate_'+key):
                getattr(self, 'populate_'+key)(contents)
                continue

            if (isinstance(contents, dict) and
                    isinstance(contents.get('default'), str) and
                contents['default'].startswith('CUBA.')):

                self.populate_init_body_with_cuba_default(key, contents['default'])
            else:
                # __init__ body
                self.init_body.append('self.{key} = {key}'.format(key=key))

            # The attributes is not inherited, we need to write the getter,
            # setter and the validation code
            if (key in self.optional_user_defined or
                    key in self.required_user_defined):
                # Getter
                self.populate_getter(key)

                # Setter
                self.populate_setter_with_validation(key, contents)

    def populate_getter(self, key, value=None):
        # default property getter
        if value is None:
            value = "self._{key}".format(key=key)

        self.methods.append('''
    @property
    def {key}(self):
        return {value}'''.format(key=key, value=value))

    def populate_setter(self, key, check_statements=()):
        # Get the indentation right
        validation_code = '''
            '''.join(check_statements)

        # default property setter
        self.methods.append('''
    @{key}.setter
    def {key}(self, value):
        if value is not None:
            {validation_code}
        self._{key} = value'''.format(key=key, validation_code=validation_code))

    def populate_setter_with_validation(self, key, contents):
        # Validation code for the setter
        check_statements = []

        if isinstance(contents, dict) and "shape" in contents:
            # If `shape` is defined, the value is supposed to be a sequence
            # We check the shape of the sequence
            # Then validate each item in the sequence
            statement = "validation.check_shape(value, {!r})"
            check_statements.append(statement.format(contents['shape']))

            check_statements.append('\n    '.join(
                ['for item in value:'
                 'validation.validate_cuba_keyword(item, {!r})'.format(key)]))
        else:
            statement = 'validation.validate_cuba_keyword(value, {!r})'
            check_statements.append(statement.format(key))

        # Populate setter
        self.populate_setter(key, check_statements)

    def populate_init_body_with_cuba_default(self, key, default):
        default_key = default.lower().replace('cuba.', '')
        class_name = to_camel_case(default_key)
        # __init__ body
        self.init_body.append('''
        if {key}:
            self.{key} = {key}
        else:
            self.{key} = {class_name}()'''.format(key=key,
                                                  class_name=class_name))

        self.imports.append("from {0}.{1} import {2}".format(
            PATH_TO_CLASSES, default_key,
            to_camel_case(default_key)))

    def populate_uuid(self, contents):
        """Populate code for CUBA.UUID"""
        self.imports.append("import uuid")

        self.methods.append('''
    @property
    def uuid(self):
        if not hasattr(self, "_uuid") or self._uuid is None:
            self._uuid = uuid.uuid4()
        return self._uuid''')

    def populate_data(self, contents):
        """Populate code for CUBA.DATA"""
        if contents:
            # FIXME: contents is not being used, what should we expect there?
            message = "provided value for DATA is currently ignored. given: {}"
            warnings.warn(message.format(contents))

        self.imports.append(IMPORT_PATHS['DataContainer'])

        self.init_body.append('''if data:
            self.data = data
        else:
            self._data = DataContainer()''')

        self.methods.append('''
    @property
    def data(self):
        return DataContainer(self._data)''')

        self.methods.append('''
    @data.setter
    def data(self, new_data):
        self._data = DataContainer(new_data)''')

    def collect_parents_to_mro(self, generators):
        ''' recursively collect all the inherited into CodeGenerator.mro
        Assume single inheritence, i.e. no multiple parents
        '''
        # If its mro is already completed, return
        if self.mro_completed:
            return

        if self.parent == 'object':
            self.mro_completed = True
            return

        # Collect all the grandparents
        parent_generator = generators[self.parent]

        # Populate MRO
        parent_generator.collect_parents_to_mro(generators)
        self.mro.append(parent_generator.original_key)
        self.mro.extend(parent_generator.mro)

        # Mark MRO as completed
        self.mro_completed = True

    def collect_user_defined_from_parents(self, generators):
        ''' Given the MRO is populated, collect all the user defined
        attributes inherited from the parents and thus populate
        `inherited_required` and `inherited_optional`

        See Also
        --------
        collect_parents_to_mro
        '''
        if not self.mro_completed:
            raise RuntimeError(
                'MRO is not yet populated for {}.'.format(self.original_key))

        if not self.mro:
            return

        # Go from the greatest grandparent (i.e. root node)
        root = self.mro[-1]

        # Collect user defined attributes
        # with the younger parent's attributes overwriting the older's ones
        self.inherited_optional = generators[root].optional_user_defined.copy()
        self.inherited_required = generators[root].required_user_defined.copy()

        for parent in self.mro[-2::-1]:
            parent_generator = generators[parent]
            become_required = set(self.inherited_optional) & set(parent_generator.required_user_defined)
            for key in become_required:
                self.inherited_optional.pop(key)

            become_optional = set(self.inherited_required) & set(parent_generator.optional_user_defined)
            for key in become_optional:
                self.inherited_required.pop(key)

            self.inherited_optional.update(parent_generator.optional_user_defined)
            self.inherited_required.update(parent_generator.required_user_defined)

        for key in self.inherited_optional:
            if key in self.optional_user_defined or key in self.required_user_defined:
                self.inherited_optional.pop(key)

        for key in self.inherited_required:
            if key in self.optional_user_defined or key in self.required_user_defined:
                self.inherited_required.pop(key)

    def generate_class_import(self, file_out):
        # import statements
        print(*sorted(set(self.imports), reverse=True), sep="\n", file=file_out)

    def generate_class_header(self, file_out):
        # class header
        if self.parent != 'object':
            parent_class_name = to_camel_case(self.parent)
        else:
            parent_class_name = self.parent

        print('\n\nclass {name}({parent}):'.format(
            name=to_camel_case(self.original_key), parent=parent_class_name),
              file=file_out)

    def generate_class_docstring(self, file_out):
        ''' Generates the description block of the generated class.

        This block does not include individual attribute documentation

        Parameters
        ----------
        file_out : File object
        '''

        definition = self.class_data.get('definition', 'Missing definition')

        print('''
    \'\'\'{DOC_DESCRIPTION}

    Attributes
    ----------
    \'\'\''''.format(DOC_DESCRIPTION=definition), file=file_out)

    def generate_class_attributes_docstring(self, file_out):
        ''' Generates the description block of the generated class.

        This block does not include individual attribute documentation

        Parameters
        ----------
        file_out : File object
        '''
        pass

    def generate_initializer(self, file_out):
        # __init__ keyword arguments
        kwargs = []
        for key, content in chain(self.inherited_optional.items(),
                                  self.optional_user_defined.items()):
            # Since it is optional, it must have a default entry
            # However if the default value is a CUBA key, we set it to None in the init
            if isinstance(content['default'], str) and content['default'].startswith('CUBA.'):
                kwargs.append('{key}=None'.format(key=key))
            else:
                kwargs.append('{key}={value}'.format(key=key, value=content['default']))

        # __init__ signature
        signature = ["self"]
        signature.extend(self.inherited_required.keys())
        signature.extend(self.required_user_defined.keys())
        signature.extend(kwargs)

        # Print __init__ definition and signature
        print('''
    def __init__({signature}):'''.format(signature=", ".join(signature)),
              file=file_out)

        # __init__ body
        if self.init_body == [""]:
            self.init_body.append("pass")

        print(*self.init_body, sep="\n        ", file=file_out)

    def generate(self, file_out):
        """ This is the main function for generating the code """
        self.generate_class_import(file_out)
        self.generate_class_header(file_out)
        self.generate_class_docstring(file_out)
        self.generate_class_attributes_docstring(file_out)
        self.generate_initializer(file_out)

        # methods (including descriptors)
        print(*self.methods, sep="\n", file=file_out)



@click.group()
def cli():
    """ Auto-generate code from simphony-metadata yaml description. """


@cli.command()
@click.argument('yaml_file', type=click.File('rb'))
@click.argument('out_path', type=click.Path())
@click.option('--api/--no-api', 'create_api', default=True,
              help='Create an api.py that collects all classes')
@click.option('-O', '--overwrite', is_flag=True, default=False)
def meta_class(yaml_file, out_path, create_api, overwrite):
    """ Create the Simphony Metadata classes
    """

    if os.path.exists(out_path):
        if overwrite:
            shutil.rmtree(out_path)
        else:
            raise OSError('Destination already exists: {!r}'.format(out_path))

    yml_descriptor = yaml.safe_load(yaml_file)

    all_generators = {}

    # Temporary directory that stores the output
    with make_temporary_directory() as temp_dir:

        for key, class_data in yml_descriptor['CUDS_KEYS'].items():
            if class_data['parent'] == 'CUBA.FORCE':
                warnings.warn(('{key} is SKIPPED because its parent is CUBA.FORCE, '
                               'which is not a CUDSItem').format(key=key))
                continue
            all_generators[key] = CodeGenerator(key, class_data)

        for key, gen in all_generators.items():
            gen.collect_parents_to_mro(all_generators)
            gen.collect_user_defined_from_parents(all_generators)
            gen.populate_user_variable_code()
            gen.populate_system_code()

            filename = os.path.join(temp_dir,
                                    "{}.py".format(gen.original_key.lower()))

            with open(filename, 'wb') as generated_file:
                gen.generate(file_out=generated_file)

            if create_api:
                # Print to the api.py
                with open(os.path.join(temp_dir, "api.py"), 'ab') as api_file:
                    print('from .{} import {}'.format(key.lower(),
                                                      to_camel_case(key)),
                          sep='\n', file=api_file)

        init_path = os.path.join(temp_dir, '__init__.py')
        open(init_path, 'a').close()

        for file_to_copy in FILES_TO_COPY:
            dst_path = os.path.join(temp_dir, os.path.split(file_to_copy)[-1])
            shutil.copyfile(file_to_copy, dst_path)

        # Copy everything to the output directory
        shutil.copytree(temp_dir, out_path)



@cli.command()
@click.argument('cuba_input', type=click.File('rb'))
@click.argument('cuds_input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def cuba_enum(cuba_input, cuds_input, output):
    """ Create the CUBA Enum
    """
    keywords = yaml.safe_load(cuba_input)
    metadata = yaml.safe_load(cuds_input)

    lines = [
        '# code auto-generated by the simphony-metadata/scripts/generate.py script.\n',
        '# cuba.yml VERSION: {}\n'.format(keywords['VERSION']),
        'from enum import IntEnum, unique\n',
        '\n',
        '\n',
        '@unique\n',
        'class CUBA(IntEnum):\n',
        '\n']
    template = "    {} = {}\n"

    counter = count(1)

    all_keys = set(keywords['CUBA_KEYS']) | set(metadata['CUDS_KEYS'])

    for keyword in all_keys:
        if keyword in CUBA_DATA_CONTAINER_EXCLUDE:
            continue
        lines.append(template.format(keyword, counter.next()))

    output.writelines(lines)


@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def keywords(input, output):
    """ Create a dictionary of CUDS keywords.
    """
    keywords = yaml.safe_load(input)

    lines = [
        '# code auto-generated by the simphony-metadata/scripts/generate.py script.\n',
        '# cuba.yml VERSION: {}\n'.format(keywords['VERSION']),
        'from collections import namedtuple\n',
        '\n',
        'import numpy\n',
        'import uuid\n',
        '\n',
        '\n',
        'ATTRIBUTES = [\n'
        '    "name", "definition", "key", "shape", "dtype"]\n'  # noqa
        'Keyword = namedtuple("Keyword", ATTRIBUTES)\n',
        '\n',
        '\n',
        'KEYWORDS = {\n']
    data_types = {
        'uuid': 'uuid.UUID',
        'string': 'numpy.str',
        'double': 'numpy.float64',
        'integer': 'numpy.int32'}
    template = (
        "    '{key}': Keyword(\n"
        "        name='{name}',\n"
        "        definition='{definition}',  # noqa\n"
        "        key='{key}',\n"
        "        shape={shape},\n"
        "        dtype={type}),\n")
    for keyword, content in keywords['CUBA_KEYS'].items():
        content['type'] = data_types[content['type']]
        content['name'] = to_camel_case(keyword)
        content['key'] = keyword
        lines.extend(template.format(**content))
    lines.append('}\n')

    output.writelines(lines)


if __name__ == '__main__':
    cli()
