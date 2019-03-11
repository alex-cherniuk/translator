def required(*args):
    for value in args:
        if value is None:
            raise ValueError('One of the values is missing')
