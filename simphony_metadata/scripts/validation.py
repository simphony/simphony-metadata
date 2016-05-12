import warnings
import re

import numpy


def to_camel_case(text, special={'cuds': 'CUDS'}):
    """ Convert text to CamelCase (for class name)

    Parameters
    ----------
    text : str
        The text to be converted

    special : dict
        If any substring of text (lower case) matches a key of `special`,
        the substring is replaced by the value

    Returns
    -------
    result : str
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
    matched = re.finditer(
        r'([0-9+]):([0-9]+)|([0-9]+):|:([0-9]+)|([0-9]+)|[^0-9](:)[^0-9]',
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

    if len(decoded_shape) == 0:
        # Any shape is allowed
        return

    def check_valid(min_size, max_size, size):
        return ((size >= int(min_size) if min_size else True) and
                (size <= int(max_size) if max_size else True))

    try:
        value_shape = value.shape
    except AttributeError:
        value_shape = numpy.array(value).shape

    error_message = ("value has a shape of {value_shape}, "
                     "which does not comply with shape: {shape}")

    for (min_size, max_size), size in zip(decoded_shape, value_shape):
        if not check_valid(min_size, max_size, size):
            raise ValueError(error_message.format(value_shape=value_shape,
                                                  shape=shape))            


def validate_cuba_keyword(value, key):
    ''' Validate the given `value` against `key`

    Parameters
    ----------
    value : object
       any value

    key : str
       CUBA key, can be stripped of 'CUBA.'

    Returns
    -------
    None

    Raises
    ------
    TypeError
        - if key is a CUBA keyword with shape and the value's shape
          or type does not match
        - if key corresponds to a class defined by the meta data and
          the value is not an instance of that class
    '''
    from . import api

    # Sanitising, although generated code already did
    key = key.replace('CUBA.', '')

    # Class name, e.g. cuds_item -> CUDSItem
    class_name = to_camel_case(key)

    # The corresponding class in the metadata
    api_class = getattr(api, class_name, None)

    # Keyword name in KEYWORDS
    keyword_name = key.upper()

    if keyword_name in KEYWORDS:
        keyword = KEYWORDS[keyword_name]

        # Convert to numpy array
        value = numpy.array(value)

        # Check shape, keyword.shape needs to be converted to our shape syntax
        check_shape(value, repr(tuple(keyword.shape)))

        # Check type
        if not numpy.issubdtype(value.dtype, keyword.dtype):
            message = 'value has dtype {dtype1} while {key} needs to be a {dtype2}'
            raise TypeError(message.format(dtype1=value.dtype,
                                           key=key,
                                           dtype2=keyword.dtype))
    elif api_class:
        if not isinstance(value, api_class):
            message = '{0!r} is not an instance of {1}'
            raise TypeError(message.format(value, api_class))
    else:
        message = '{} is not defined in CUBA keyword or meta data'
        warnings.warn(message.format(key.upper()))

    
