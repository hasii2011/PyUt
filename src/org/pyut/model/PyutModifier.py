

class PyutModifier:
    """
    Modifier for a method or param.
    These are words like:

    * "abstract"
    * "virtual"
    *"const"...

    """
    def __init__(self, modifierTypeName: str = ""):
        """

        Args:
            modifierTypeName:   for the type
        """
        self.__name: str = modifierTypeName

    @property
    def name(self) -> str:
        return self.__name

    def getName(self) -> str:
        """

        Returns:  The modifier name

        """
        return self.__name

    def __str__(self):
        """
        Returns:
            String representation.
        """
        return self.getName()
