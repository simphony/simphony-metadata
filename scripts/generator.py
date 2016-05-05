import click
import yaml
from tabulate import tabulate
from collections import namedtuple

# TODO: I will have to change this
# from simphony.core.keywords import KEYWORDS


# TODO: This will have to change
def getGeneratedClassesRoute():
    ''' Fetches the route for the generated classes

    Return
    ------

    A string containing the route where the generated classes are stored.

    '''

    return 'simphony.generated'


def getKeyWordName(str, firstLower=False):
    ''' Generated a valid keyword for python in cammelCase form.

    Input
    -----

    str: string
        a string containing the source

    firstLower: boolean (default value: False)
        a boolean that controls if the first letter will be lower or not

    Return
    ------

    A string containing the route where the generated classes are stored.

    '''

    s = str.title().replace('_', '')
    if firstLower:
        return s[0].lower() + s[1:]
    else:
        return s


def getCubaKeyWordName(str, firstLower=False):
    ''' Generated a valid keyword for python in cammelCase form.

    Input
    -----

    str: string
        a string containing the source in the form of 'CUBA.FOO'

    firstLower: boolean (default value: False)
        a boolean that controls if the first letter will be lower or not

    Return
    ------

    A string containing the route where the generated classes are stored.

    '''

    return getKeyWordName(str.split('.')[1], firstLower)


def getAtrributeKeys(classData):
    ''' Return a list of attribute keys from a yalm descriptor.

    The list of attribute keys are all those entries that start by 'CUBA.'

    Input
    -----

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY


    Return
    ------

    A list of attribute keys matching the rules in the description.

    '''

    cubaAttributeKeys = dict((cak, classData[cak]) for cak in classData if cak and cak.split('.') and cak.split('.')[0] == 'CUBA')
    return cubaAttributeKeys


# TODO: It appears that I don't fully understand the behavior of the level class atrributes.
# Excluded now
def getProtectedAtrributes(classData):
    ''' Return a list of protected attributes from a yalm descriptor.

    The list of protected attributes (metadata level attribute) are all those entries that are not capitalized
    excluding the ones in 'excludeKeys'.

    Input
    -----

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY


    Return
    ------

    A list of attribute keys matching the rules in the description.

    '''

    excludeKeys = ['models', 'parent', 'variables', 'physics_equation']
    protectedAttributes = dict((cak, classData[cak]) for cak in classData if cak not in excludeKeys and cak.split('.') and cak.split('.')[0] != 'CUBA')
    return protectedAttributes


def generate_class_import(className, classData, allowPythonInheritance=True):
    ''' Generates the import block of the generated class

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    allowPythonInheritance: boolean
        enables or disables python-based inheritance of the classes
        descrived in the yalm file.

    Return
    ------

    A list with the lines of the import block for the generated class.

    '''

    lines = [
        '# code auto-generated by the simphony-metadata generator.py\n',
        'from simphony.core.cuba import CUBA\n',
        'from simphony.core.data_container import DataContainer\n',
    ]

    # If this happens, we have to include our parent!
    if 'parent' in classData.keys() and classData['parent'] and allowPythonInheritance:
        lines += [
            'from '+getGeneratedClassesRoute()+'.'+getCubaKeyWordName(classData['parent'], firstLower=True)+' import '+getCubaKeyWordName(classData['parent'])+'\n',
        ]

    lines += [
        '\n',
        '\n'
    ]

    return lines


def generate_class_header(className, classData, allowPythonInheritance=True):
    ''' Generates the header block of the generated class

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    allowPythonInheritance: boolean
        enables or disables python-based inheritance of the classes
        descrived in the yalm file.

    Return
    ------

    A list with the lines of the header block for the generated class.

    '''

    inheritance = 'object'

    if 'parent' in classData.keys() and classData['parent'] and allowPythonInheritance:
        inheritance = getCubaKeyWordName(classData['parent'])

    return [
        "class {NAME}({INHERIT}):\n".format(
            NAME=className,
            INHERIT=inheritance
        ),
        "\n"
    ]


def generate_description_block(className, classData):
    ''' Generates the description block of the generated class.

    This block does not include individual attribute documentation

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    Return
    ------

    A list with the lines of the description block for the generated class.

    '''

    definition = 'Missing definition'
    if 'definition' in classData.keys():
        definition = classData['definition']

    lines = [
        "\t\"\"\" A {NAME} class\n".format(
            NAME=className
        ),
        "\tThis class has been automatically generated."
        "\n",
        "\t{DOC_DESCRIPTION}\n\n".format(
            DOC_DESCRIPTION=definition
        ),
        "\tAttributes\n",
        "\t----------\n",
    ]

    return lines


def generate_attributes_description(className, classData):
    ''' Generates the description block for inidividual attributes of the class

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    allowPythonInheritance: boolean
        enables or disables python-based inheritance of the classes
        descrived in the yalm file.

    Return
    ------

    A list with the lines of the descriotion block of the individual attribues
    for the generated class.

    '''

    cubaAttributeKeys = getAtrributeKeys(classData)

    lines = []

    for cak in cubaAttributeKeys:
        lines += [
            "\t" + getCubaKeyWordName(cak) + ': instance of ' + cak + '\n',
            "\t\tnot sure yet what to put here, maybe the definition of the object\n",
            "\n",
        ]

    lines += [
        '\t"""\n',
        '\n'
    ]

    return lines


def generate_initializer(className, classData, allowPythonInheritance=True):
    ''' Generates the initialize block of the generated class

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    allowPythonInheritance: boolean
        enables or disables python-based inheritance of the classes
        descrived in the yalm file.

    Return
    ------

    A list with the lines of the initialize block for the generated class.

    '''

    cubaAttributeKeys = getAtrributeKeys(classData)
    protectedAttribute = getProtectedAtrributes(classData)

    lines = []
    body_lines = []

    lines += [
        '\tdef __init__(\n',
        '\t\tself',
    ]

    # TODO: Is this still valid?
    # if 'parent' in classData.keys() and classData['parent'] and classData['parent'] == 'CUBA.CUDS_COMPONENT':
    #     lines += [
    #         ',\n\t\tdescription' + '="' + description + '"',
    #         ',\n\t\tname' + '="' + name + '"',
    #     ]

    # for cak, val in cubaAttributeKeys.items():
    #     defaultVal = 'None'
    #     if val and 'default' in val:
    #         defaultVal = val['default']
    #
    #     lines += [
    #         ',\n\t\t' + getCubaKeyWordName(cak, firstLower=True) + '=' + str(defaultVal),
    #     ]

    lines += [
        "\n\t):\n",
    ]

    if 'parent' in classData.keys() and classData['parent'] and allowPythonInheritance:
        body_lines += [
            "\t\tsuper({NAME}, self).__init__()\n".format(
                NAME=className
            ),
        ]

    for p, val in protectedAttribute.items():
        # TODO: Probably this will depend on the value. Stored as a string for now.
        body_lines += [
            '\n\t\tself._' + p + ' = "' + val + '"',
        ]

    # Add 'system' attribute keys
    for cak, val in cubaAttributeKeys.items():
        defaultVal = 'None'
        if val and 'default' in val:
            defaultVal = val['default']

        if val and (('scope' in val.keys() and val['scope'] == 'CUBA.USER') or ('scope' not in val.keys())):
            body_lines += [
                '\n\t\tself.' + getCubaKeyWordName(cak, firstLower=True) + ' = ' + str(defaultVal) + '',
            ]

    if len(body_lines):
        body_lines += ['\n']
        lines += body_lines
    else:
        lines += [
            '\t\tpass\n'
        ]

    return lines


def generate_property_get_set(className, classData):
    ''' Generates the properties block of the generated class

    Input
    -----

    className: string
        name of the generated class

    classData: dictionary
        a dictionaty with the contents of a simphony-metadata KEY

    allowPythonInheritance: boolean
        enables or disables python-based inheritance of the classes
        descrived in the yalm file.

    Return
    ------

    A list with the lines of the properties block for the generated class.

    '''

    cubaAttributeKeys = getAtrributeKeys(classData)
    protectedAttribute = getProtectedAtrributes(classData)

    getter = (
        "\t@property\n"
        "\tdef {PROP_NAME}(self):\n"
        "\t\treturn self._parameters[{CUBA_KEY}]\n"
    )

    setter = (
        "\t@{PROP_NAME}.setter\n"
        "\tdef {PROP_NAME}(self, value):\n"
        "\t\tself._parameters[{CUBA_KEY}] = value\n"
    )

    prop = (
        "\t@property\n"
        "\tdef {NAME}(self):\n"
        "\t\treturn self._{VALUE}\n"
    )

    get_set_block = getter + "\n" + setter

    lines = []

    # Add 'system' attribute keys
    for cak, value in cubaAttributeKeys.items():
        if value and 'scope' in value.keys() and value['scope'] == 'CUBA.SYSTEM':
            lines.append("\n")
            lines.extend(get_set_block.format(
                PROP_NAME=getCubaKeyWordName(cak, firstLower=True),
                CUBA_KEY=cak
            ))

    # Add protected attributes (read only)
    for p, value in protectedAttribute.items():
        lines.append("\n")
        lines.extend(prop.format(
            NAME=getKeyWordName(p, firstLower=True),
            VALUE=p
        ))

    return lines


# TODO: This is not yet implemented for simphony_metadata
def generate_test_import(className, classData):
    lines = [
        "import unittest\n",
        "import uuid\n",
        "\n",
        "from simphony.cuds.material_relations.{} import (\n".format(
            classData['key'].lower()),
        "\t{})\n".format(classData['class_name']),
        "from simphony.testing.abc_check_material_relation import (\n",
        "\tCheckMaterialRelation)\n",
        "\n",
        "\n"
    ]

    return lines


# TODO: This is not yet implemented for simphony_metadata
def generate_test_header(className, classData):
    lines = [
        "class Test{MR_NAME}MaterialRelation(\n".format(
            MR_NAME=classData['class_name']
        ),
        "\tCheckMaterialRelation,\n",
        "\tunittest.TestCase\n",
        "):\n",
        "\tdef container_factory(\n",
        "\t\tself,\n",
        "\t\t\tname=\"{MR_NAME}\",\n".format(
            MR_NAME=classData['class_name']
        ),
        "\t\t\tmaterials=[uuid.uuid4() for _ in xrange({MR_NUM_MATS})]".format(
            MR_NUM_MATS=classData['allowed_number_materials'][0]
        ),
        "):\n",
        "\t\treturn {MR_NAME}(\n".format(
            MR_NAME=classData['class_name']
        ),
        "\t\t\tname=name,\n",
        "\t\t\tmaterials=materials\n",
        "\t\t)\n"
    ]

    return lines


# TODO: This is not yet implemented for simphony_metadata
def generate_test_parameters(className, classData):

    test_att_template = (
        "\tdef test_{ATT_NAME}(self):\n"
        "\t\trelation = self.container_factory('foo_relation')\n"
        "\n"
        "\t\tself.assertEqual(relation.{ATT_NAME}, {ATT_DEFAULT})\n"
    )

    test_update_att_template = (
        "\tdef test_{ATT_NAME}_update(self):\n"
        "\t\trelation = self.container_factory('foo_relation')\n"
        "\n"
        "\t\toriginal = relation.{ATT_NAME}\n"
        "\t\trelation.{ATT_NAME} = original + 1\n"
        "\n"
        "\t\tself.assertEqual(relation.{ATT_NAME}, original + 1)\n"
    )

    lines = []

    for param in classData['supported_parameters']:
        lines.append("\n")
        lines.extend(test_att_template.format(
            ATT_NAME=param['cuba'].split('.')[1].lower(),
            ATT_DEFAULT=param['default']
        ))
        lines.append("\n")
        lines.extend(test_update_att_template.format(
            ATT_NAME=param['cuba'].split('.')[1].lower(),
            ATT_DEFAULT=param['default']
        ))

    return lines


# TODO: This is not yet implemented for simphony_metadata
def generate_test_main():
    lines = [
        "\n",
        "if __name__ == '__main__':\n",
        "\tunittest.main()\n"
    ]

    return lines


@click.group()
def cli():
    """ Auto-generate code from simphony-metadata yaml description. """


@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('outpath', type=click.Path(exists=True))
def python(input, outpath):
    """ Create the material-relation classes.
    """
    yml_descriptior = yaml.safe_load(input)

    for key, classData in yml_descriptior['CUDS_KEYS'].items():

        className = getKeyWordName(key)
        fileName = getKeyWordName(key, firstLower=True)
        # print className

        with open(outpath+fileName+'.py', 'w+') as generatedFile:
            lines = []

            lines += generate_class_import(className, classData)
            lines += generate_class_header(className, classData)
            lines += generate_description_block(className, classData)
            lines += generate_attributes_description(className, classData)
            lines += generate_initializer(className, classData, yml_descriptior)
            lines += generate_property_get_set(className, classData)

            generatedFile.writelines([i.replace('\t', '    ') for i in lines])


# TODO: This is not yet implemented for simphony_metadata
@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('outpath', type=click.Path(exists=True))
def test(input, outpath):
    """ Create the generated test classes.
    """
    material_relations = yaml.safe_load(input)

    for classData in material_relations:
        class_name_l = classData['key'].lower()
        with open(outpath+"test_"+class_name_l+'.py', 'w+') as mrFile:
            lines = []
            lines += generate_test_import(classData)
            lines += generate_test_header(classData)
            lines += generate_test_parameters(classData)
            lines += generate_test_main()

            mrFile.writelines([i.replace('\t', '    ') for i in lines])

# TODO: This probably is not needed for generated classes. Anyway.
# @cli.command()
# @click.argument('input', type=click.File('rb'))
# @click.argument('output', type=click.File('wb'))
# def create_enum(input, output):
#     """ Create the CUDSGenerated Enum.
#     """
#     keywords = yaml.safe_load(input)
#
#     lines = [
#         '# auto-generated by the material_relations_generate.py script.\n',
#         'from enum import IntEnum, unique\n',
#         '\n',
#         '\n',
#         '@unique\n',
#         'class CUDSMaterialRelation(IntEnum):\n',
#         '\n']
#     template = "    {} = {}\n"
#     for keyword in keywords:
#         lines.append(template.format(keyword['key'], keyword['number']))
#     output.writelines(lines)


# TODO: This is not yet implemented for simphony_metadata
@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def material_relations_definitions_py(input, output):
    """ Create a dictionary describing the generated classes.
    """
    keywords = yaml.safe_load(input)

    lines = [
        '# code auto-generated by the material_relations_generate.py script.\n',  # noqa
        'from collections import namedtuple\n',
        '\n',
        'from simphony.core.cuba import CUBA\n',
        'from simphony.core.cuds_material_relation import CUDSMaterialRelation\n'  # noqa
        '\n',
        '\n',
        'ATTRIBUTES = [\n'
        '    "number", "class_name", "allowed_number_materials",\n'
        '    "doc_description", "supported_parameters"]\n'
        'Material_Relation_Definition = namedtuple("Material_Relation_Definition",\n',  # noqa
        '                                          ATTRIBUTES)\n',  # noqa
        '\n',
        'Parameter = namedtuple("Parameter", ["cuba_key", "default_value"])\n',
        '\n',
        '\n',
        'MATERIAL_RELATION_DEFINITIONS = {\n']
    template = (
        "    CUDSMaterialRelation.{key}: Material_Relation_Definition(\n"
        "        class_name='{class_name}',\n"
        "        number={number},\n"
        "        allowed_number_materials={allowed_number_materials},\n"
        "        doc_description='{doc_description}',  # noqa\n"
        "        supported_parameters=[{supported_parameters} ]\n"
        "     ),\n")
    parameter_template = (
        "\n"
        "             Parameter(cuba_key={CUBA},\n"
        "                       default_value={DEFAULT}),")

    for keyword in keywords:
        parameters_list = ''
        for parameter in keyword['supported_parameters']:
            parameters_list += parameter_template.format(
                CUBA=parameter['cuba'],
                DEFAULT=parameter['default'])
        keyword['supported_parameters'] = parameters_list
        lines.extend(template.format(**keyword))
    lines.append('}\n')

    output.writelines(lines)


# TODO: This is not yet implemented for simphony_metadata
@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def create_api(input, output):
    """ Create an rst document to describe api of generated classes.

    """
    keywords = yaml.safe_load(input)

    lines = [
        '.. auto-generated by material_relations_generate.py script.\n'
        '.. rubric:: Material relations\n\n',
        '.. currentmodule:: simphony.cuds.material_relations\n\n',
        '.. autosummary::\n\n']
    template = "   ~{}.{}\n"
    for keyword in keywords:
        lines.append(template.format(keyword['key'].lower(),
                                     keyword['class_name']))
    lines += '\n.. rubric:: Implementation\n\n'
    template = ("\n.. automodule:: simphony.cuds.material_relations.{}\n"
                "   :members:\n"
                "   :undoc-members:\n"
                "   :show-inheritance:\n")
    for keyword in keywords:
        lines.append(template.format(keyword['key'].lower()))
    output.writelines(lines)

_Column = namedtuple('_Column', ["key", "header", "formatter"])


# TODO: This is not yet implemented for simphony_metadata
@cli.command()
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def table_rst(input, output):
    """ Create an rst document with table of different generated classes.
    """
    keywords = yaml.safe_load(input)

    def format_supported_parameters(parameters):
        return ', '.join(["{}".format(param['cuba']) for param in parameters])

    columns = [_Column("key", "Key", lambda x: "{}".format(x)),
               _Column("class_name", "Class",
                       lambda x: ":class:`~.{}`".format(x)),
               _Column("domain", "Domain", lambda x: ", ".join(x)),
               _Column("doc_description", "Description",
                       lambda x: "{}".format(x)),
               _Column("allowed_number_materials",
                       "Allowed lengths of materials",
                       lambda x: "{}".format(x)),
               _Column("supported_parameters",
                       "Supported parameters",
                       format_supported_parameters)]

    table_header = [col.header for col in columns]
    table_header.append("Supported parameters")

    table_data = []

    for keyword in keywords:
        row = [col.formatter(keyword[col.key]) for col in columns]
        table_data.append(row)

    rst = tabulate(table_data, table_header, tablefmt="rst")
    output.write(
        ".. auto-generated by material_relations_generate.py script.\n\n")
    output.write(rst)


if __name__ == '__main__':
    cli()
