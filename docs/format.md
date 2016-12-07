Description of YAML format
==========================

Specification version: 1.0

This document describes the format of the metadata description.
It is not meant to describe the concept of CUBA and CUDS and what they
represent. Merely to describe how their logic is represented in the
file at the YML level.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119. [1]

Changelog
---------

- Removed CUBA/CUDS keys from root mapping for both files. use namespace instead.
- non-CUBA/CUDS mapping keys MUST now be lowercase.
- Replaced Purpose key with description in simphony_metadata.yml. 
- Removed Resources key from simphony_metadata.yml root mapping.
- ``definition`` is now replaced by ``description`` in all entries.
- ``cuba_keys`` and ``cuds_keys`` have been renamed to ``keys``

Format description
------------------

Two files exist:

    - cuba.yml: describes basic data types that semantically enhance plain data.
      For example, a string that is used to represent a UUID. 

    - simphony_metadata.yml: Describes high level objects and their external links
      to other objects, either as inheritance (specialization, is-a) or relationship 
      (has-a).

cuba.yml
--------

The format MUST have a root mapping with the following keys:

    - ``version``: string 
      Contains semantic version Major.minor in format M.m with M and m positive integers.
      minor MUST be incremented when extending (adding new entities). Major MUST be incremented when removing or
      altering existing entities, or changing the format overall.
      NOTE: This value can change even if the yaml schema described in this document is unchanged.

    - ``namespace``: string
        MUST contain the string CUBA.
        The namespace under which the declared entities will be added.

    - ``keys``: mapping 
      contains a mapping describing the declared **CUBA entries**.
      Each key of the mapping is the name of a CUBA entry.  The Key MUST be all
      uppercase, with underscore as separation. Numbers are allowed but not in first
      position. Valid Examples: ``FACE``, ``ANGULAR_ACCELERATION``, ``POSITION_3D``
      Each value of the mapping is a mapping whose format is detailed in the
      "CUBA entries format" section.

The root mapping MAY contain the following keys:

    - ``description``: string
      For human consumption. Free format string to describe the contents of the file.

CUBA entries format
~~~~~~~~~~~~~~~~~~~

Each CUBA entry MUST contain a mapping with the following keys:
    
    type: string
        The type of the CUBA. MUST be one of the following
        
            - string
            - integer
            - double

It MAY also contain:

    description: string 
        For human consumption. Free form description of the semantic carried by the data type.

    shape: inline sequence
        The represented CUBA entity is an array, rather than a scalar. 
        `shape` defines the shape of this array. MUST be a list of positive integers. 

    length: integer
        This entity MAY be present if the type is ``string``. It MUST NOT be present otherwise.
        If present, it constraints the length of the string to the specified amount.
        If not present, the string can have arbitrary length.

simphony_metadata.yml
---------------------

The format MUST have a root level mapping with the following keys:

    - version: as in cuba.yml

    - namespace: As in cuba.yml, but MUST contain the string CUDS

    - keys: as in cuba.yml
        Contains individual declarations for CUDS entries. 

CUDS entries format
~~~~~~~~~~~~~~~~~~~

Each CUDS entry MUST contain a mapping with the following keys:
    
    parent: string
        The parent CUDS of a inheritance (is-a) hierarchy. MUST be either:

            - a string referring to another CUDS entry. In this case, it must be
              namespaced in the CUDS namespace. For example:

                parent: CUDS.PAIR_POTENTIAL

            - or, an empty string, for the start of the hierarchy (parentless).

        The file MUST contain one and only one parentless entry.

    models: sequence of strings.
        FIXME: apparently obsolete.

It MAY contain the following:

    description: string 
        For human consumption. Free form description of the carried semantics.

    variables:
        FIXME: apparently obsolete.
    
    properties: mapping 
        contains a mapping of **Property entries** that indicate properties of the CUDS entry.
        They describe relations between CUDS, or between CUDS and CUBA. 
        each key MUST be either:

            - a namespace qualified CUBA or CUDS name, or
            - a non-namespaced generic label. 
        
        Example::

                properties:
                    CUBA.TEMPERATURE:
                        <property entry>
                    CUDS.INTEGRATION_STEP:
                        <property entry>
                    data:
                        <property entry>

      Each value of the mapping is a mapping whose format is detailed in "Property entries format".

Property entries format
~~~~~~~~~~~~~~~~~~~~~~~

Each Property entry is a mapping that MAY have the following keys:

    - `scope`: string
        Controlled dictionary. Allowed strings:
            - `system`: Indicates that this property is not available for 
              setting at construction. its value is set by internal code.
            - `user`: Default if not specified. Indicates that this
              property is available for setting at construction. Its initial 
              value is the appropriate default.

    - `access`: string
        Controlled dictionary. Allowed strings:
            - `readonly`: Indicates that this property will not allow for
              a setter access function. Note that this does not imply the
              property cannot be set at construction (see `scope`)
            - `readwrite`: Default if not specified. Indicates that a
              setter will be provided for the property.
    - `default`: 
        Indicates the default value for the property once the CUDS has 
        been instantiated.
        The default MUST be type compatible with the property entry key.
        If the key refers to a CUBA, the data must match shape, type and length 
        requirements specified for the CUBA. If refers to a CUDS
        


Parser behavior
---------------

An error MUST be reported, and parsing stopped when the following circumstances occur
    - non-compliance with the specified format.
    - Unrecognized keys by parsers
    - Duplicated keys


References
----------
[1]: https://www.ietf.org/rfc/rfc2119.txt
