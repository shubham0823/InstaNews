from django.forms import FileInput

class MultipleFileInput(FileInput):
    allow_multiple_selected = True

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs['multiple'] = True

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            upload = files.getlist(name)
            return upload if upload else None
        return files.get(name) 