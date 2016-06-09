# simphony-metadata

This repository contains the metadata schema defnition of the SimPhoNy project  casted in YAML Syntax.


Repository
----------

Simphony-metadata is hosted on github: https://github.com/simphony/simphony-metadata


Directories
-----------
 - simphony_metadata/
  - scripts/ : Contain the code generator for metadata class, CUBA Enum and KEYWORDS
    - tests/ : Unit test cases for the generated code
    - generate.py : Code generator
 - yaml_files/ : Contain the YAML files that define the metadata schema and basic attributes
 - dev_requirements.txt : Python packages required for running tests
 - setup.py : For installing simphony_metadata python package

Guide to generating metadata classes
------------------------------------

- Install the code generator

  ```
$ python setup.py install
$ simphony-meta-generate
 Usage: simphony-meta-generate [OPTIONS] COMMAND [ARGS]...

  Auto-generate code from simphony-metadata yaml description.

Options:
  --help  Show this message and exit.

Commands:
  cuba_enum   Create the CUBA Enum CUBA_INPUT - Path to the...
  keywords    Create a dictionary of CUDS keywords.
  meta_class  Create the Simphony Metadata classes...
  ```

- Generate Medata classes

  You need to supply the yaml file that define the metadata schema, and the
  path to the directory where the generated classes should be placed.
  ```
simphony-meta-generate meta_class yaml_files/simphony_metadata.yml $PATH_TO_DIRECTORY
  ```

- Generate CUBA module

  ```
simphony-meta-generate cuba_enum yaml_files/cuba.yml yaml_files/simphony_metadata.yml $PATH_TO_CUBA_PY
  ```

- Generate CUBA keywords module

  ```
simphony-meta-generate keywords yaml_files/cuba.yml $PATH_TO_KEYWORD_PY
  ```

- Make generated class comply with PEP 8
 
  The generated code do not automatically comply with PEP 8.  Auto formatters are available on PyPI.
  Examples are [`yapf`](https://pypi.python.org/pypi/yapf) and [`authpep8`](https://pypi.python.org/pypi/autopep8)
