Description of YAML format
==========================


This document describes the format of the metadata description.

 The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
 NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
 "OPTIONAL" in this document are to be interpreted as described in
 RFC 2119. [1]

Two files exist:

    - cuba.yml: describes basic data types that semantically enhance plain data.
      For example, a string that is used to represent a UUID. 

    - simphony_metadata.yml: Describes high level objects and their external links
      to other objects, either as inheritance (specialization, is-a) or relationship 
      (has-a).

cuba.yml
--------

The format MUST have the following root level keys:

    - version: string 
      Contains semantic version Major.minor in format M.m with M and m positive integers.
      minor MUST be incremented when extending (adding new entities). Major MUST be incremented when removing or
      altering existing entities, or changing the format overall.

    - namespace: string
        MUST contain the string CUBA.
        The namespace under which the declared entities will be added.

    - keys: sublist 
      contains a sublist describing the declared CUBA entries.
      Each element of the sublist is the name of a CUBA entity.
      MUST be all uppercase, with underscore as separation. Numbers are allowed but not in first position.
      Valid Examples: FACE, ANGULAR_ACCELERATION, POSITION_3D

The format MAY contain the following keys:

    - description: string. 
      For human consumption. Free format string to describe the contents of the file.

CUBA entries format
-------------------

Each CUBA entry MUST contain a sublist with the following keys:
    
    type: string
        The type of the CUBA. MUST be one of the following
        
            - string
            - integer
            - double

It MAY also contain the following:

    definition: string 
        For human consumption. Free form description of the semantic carried by the data type.

    shape: list
        The CUBA entity is an array, rather than a scalar. Defines the shape of this array. 
        MUST be a list of positive integers. 

    length: integer
        This entity MAY be present if the type is ``string``. It MUST NOT be present otherwise.
        If present, it constraints the length of the string to the specified amount.
        If not present, the string can have arbitrary length.

Parser behavior
---------------

An error MUST be reported, and parsing stopped when the following circumstances occur
    - non-compliance with the specified format.
    - Unrecognized keys by parsers
    - Duplicated keys

References
----------
[1]: https://www.ietf.org/rfc/rfc2119.txt
