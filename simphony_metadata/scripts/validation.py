import warnings
import re
import numpy


def to_camel_case(text, special={'cuds': 'CUDS'}):
    """ Convert text to CamelCase (for class name)
    """
    def replace_func(matched):
        word = matched.group(0).strip("_").lower()
        if word in special:
            return special[word]
        else:
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

    value_arr = numpy.array(value)
    error_message = ("value has a shape of {value_shape}, "
                     "which does not comply with shape: {shape}")

    for (min_size, max_size), size in zip(decoded_shape, value_arr.shape):
        if not check_valid(min_size, max_size, size):
            raise ValueError(error_message.format(value_shape=value_arr.shape,
                                                  shape=shape))            


def validate_cuba_keyword(value, key):
    ''' Draft validation code '''
    from . import api

    class_name = to_camel_case(key)
    keyword_name = key.upper()
    api_class = getattr(api, class_name, None)

    if keyword_name in KEYWORDS:
        keyword = KEYWORDS[key.upper()]
        value = numpy.array(value)
        check_shape(value, repr(tuple(keyword.shape)))
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

    
