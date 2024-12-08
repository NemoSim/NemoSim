from baseModel import BaseModel


class DTPConfiguration:
    def __init__(self,config_path):
        self.config_path = config_path
        self.pulse_width = 500

    def get_pulse_width(self):
        return self.pulse_width


class DTP(BaseModel):
    def __init__(self):
        ...

    def run(self):
        pass

    def get_voltage(self):
        pass

    def get_current(self):
        pass
