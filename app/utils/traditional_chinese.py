from opencc import OpenCC

converter = OpenCC("s2twp")


def to_traditional_text(value):
    if not isinstance(value, str):
        return value
    return converter.convert(value)


def to_traditional_data(value):
    if isinstance(value, str):
        return to_traditional_text(value)

    if isinstance(value, list):
        return [to_traditional_data(item) for item in value]

    if isinstance(value, dict):
        return {key: to_traditional_data(item) for key, item in value.items()}

    return value
