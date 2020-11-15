import os


def get_file_extension(path: str) -> str:
    components = os.path.splitext(path)

    try:
        extension = components[-1]
        while extension[0] == '.':
            extension = extension[1:]
        return extension
    except IndexError:
        return ''
