import json

class JsonConfig:
    def __init__(self, file_path):
        self.load_config(file_path)

    def load_config(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.__dict__.update(data)