import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)
 
class ConfigLoader(ABC):
    """
    Represents an abstract base class for configuration loaders.

    Serves as a blueprint for creating subclasses that are responsible for
    loading server configurations. This class enforces implementation of
    specific behavior for loading configurations through its abstract method.

    Attributes:
    registry: Class attribute that maintains a list of ConfigLoader subclasses.
    """
    registry: list[type["ConfigLoader"]] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        ConfigLoader.registry.append(cls)

    @abstractmethod
    def load(self) -> Optional[Dict[str, Any]]:
        """
        An abstract method that should be implemented by subclasses to handle the
        loading of data. This method should define the logic for retrieving and
        returning the necessary data in the form of a dictionary. If no data is
        retrieved, it should return None.

        Raises:
            NotImplementedError: If the method is not implemented by the subclass.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing the loaded data if
            data retrieval is successful, otherwise None.
        """
        ...
