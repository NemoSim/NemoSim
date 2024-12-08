from abc import ABC, abstractmethod


class BaseModel(ABC):  # Inherit from ABC and use PascalCase for class names
    @abstractmethod
    def run(self):
        """Abstract method for running the model"""
        pass

    @abstractmethod
    def get_voltage(self):
        """Abstract method for getting voltage"""
        pass

    @abstractmethod
    def get_current(self):
        """Abstract method for getting current"""
        pass