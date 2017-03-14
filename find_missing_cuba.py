import yaml
import re

# All CUBA keys in the metadata yaml file
meta_cuba = set()

# CUBA keys already defined in the metadata file
cuba_def_in_meta = set()

def find_cuba(text):
    return re.findall(r'CUBA.([a-zA-Z_]+)', text)


# All occurrence of CUBA.*
with open("simphony_metadata.yml") as yaml_file:
    for metadata in yaml_file.readlines():
        meta_cuba.update(find_cuba(metadata))

# load the file again to get the CUDS_KEYS using yaml
# nevermind the efficiency
with open("simphony_metadata.yml") as yaml_file:
    cuba_def_in_meta = set(yaml.safe_load(yaml_file)["CUDS_KEYS"].keys())


# CUBA keys defined
with open("cuba.yml") as yaml_file:
    cuba_def = set(yaml.safe_load(yaml_file)["CUBA_KEYS"].keys())


# These are the CUBA keys not defined anywhere
missing_cuba = meta_cuba - (meta_cuba & cuba_def) - cuba_def_in_meta
print sorted(missing_cuba)
