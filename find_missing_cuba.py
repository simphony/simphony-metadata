import yaml
import re

meta_cuba = set()

def find_cuba(text):
    return re.findall(r'CUBA.([a-zA-Z_]+)', text)


with open("simphony_metadata.yml") as yaml_file:
    for metadata in yaml_file.readlines():
        meta_cuba.update(find_cuba(metadata))


with open("cuba.yml") as yaml_file:
    cuba_def = set(yaml.safe_load(yaml_file)["CUBA_KEYS"].keys())


missing_cuba = meta_cuba - (meta_cuba & cuba_def)
print sorted(missing_cuba)
