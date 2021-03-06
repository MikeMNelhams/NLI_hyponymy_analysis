class ModelAlreadyTrainedError(Exception):
    def __init__(self, file_path: str):
        super().__init__(f'Model cannot train, since it already has been trained and saved to: {file_path}. '
                         f'Try calling self.unlock() first!')


class ModelIsNotValidatingError(Exception):
    def __init__(self):
        super().__init__('Model is not validating.')


class ModelNotTrainedWarning(Warning):
    def __init__(self):
        self.message = 'WARNING: The model is not trained yet!'

    def __str__(self):
        return repr(self.message)
