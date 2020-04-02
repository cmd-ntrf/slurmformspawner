from traitlets import Dict

class LockableWidget(Dict):
    def validate(self, obj, value):
        value = super().validate(obj, value)
        if 'lock' in value:
            if isinstance(value['lock'], bool):
                pass
            elif isinstance(value['lock'], str):
                try:
                    value['lock'] = bool(value['lock'].lower())
                except TypeError:
                    self.error(obj, value)
            else:
                self.error(obj, value)
        else:
            value['lock'] = False
        return value

class NumericRangeWidget(LockableWidget):
    def validate(self, obj, value):
        value = super().validate(obj, value)
        expected_numeric_keys = {'def', 'min', 'max', 'step'}
        for k, v in value.items():
            if k == 'lock':
                continue
            if not k in expected_numeric_keys:
                self.error(obj, value)
            if not (isinstance(v, (int, float)) or callable(v)):
                self.error(obj, value)
        default = self.default_args[0]
        return {**default, **value}

class SelectWidget(LockableWidget):
    def validate(self, obj, value):
        value = super().validate(obj, value)
        if 'choices' in value:
            if not (isinstance(value['choices'], (list, dict)) or callable(value['choices'])):
                self.error(obj, value)
        default = self.default_args[0]
        return {**default, **value}