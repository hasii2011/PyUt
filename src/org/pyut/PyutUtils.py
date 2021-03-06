
from typing import List
from typing import Tuple

from logging import Logger
from logging import getLogger

from dataclasses import dataclass

from os import sep as osSep
from os import path as osPath

from pkg_resources import resource_filename

from tempfile import gettempdir

from wx import DisplaySize
from wx import ScreenDC
from wx import Size
from wx import NewIdRef as wxNewIdRef

from org.pyut.preferences.PyutPreferences import PyutPreferences
from org.pyut.enums.ResourceTextType import ResourceTextType

from org.pyut.errorcontroller.ErrorManager import ErrorManager
from org.pyut.errorcontroller.ErrorManager import getErrorManager


@dataclass
class ScreenMetrics:
    screenWidth:  int = 0
    screenHeight: int = 0

    dpiX: int = 0
    dpiY: int = 0


class PyutUtils:
    """
    This static class is for frequently used pyut utilities.

    hasii
    Updated this to avoid a circular dependency this module and mediator;  This module
    retrieved the mediator singleton and asked it for its error manager.  Nothing special about that
    as the error manager is a singleton;  So I just ask the error manager directly for it
    """

    STRIP_SRC_PATH_SUFFIX:  str = f'{osSep}src'
    STRIP_TEST_PATH_SUFFIX: str = f'{osSep}test'

    RESOURCES_PACKAGE_NAME: str = 'org.pyut.resources'
    RESOURCES_PATH:         str = f'org{osSep}pyut{osSep}resources'

    RESOURCE_ENV_VAR:       str = 'RESOURCEPATH'

    _basePath: str = ''

    clsLogger: Logger = getLogger(__name__)

    def __init__(self):

        PyutUtils.logger = getLogger(__name__)

    @staticmethod
    def strFloatToInt(floatValue: str) -> int:
        """

        Args:
            floatValue:

        Returns:  An integer value

        """
        if floatValue is not None and floatValue != '':
            try:
                integerValue: int = int(float(floatValue))
            except ValueError:
                PyutUtils.clsLogger.warning(f'Bad float value: {floatValue}')
                integerValue: int = 0
        else:
            integerValue: int = 0

        return integerValue

    @staticmethod
    def extractFileName(fullPath: str) -> str:
        """
        Used to get just the file name for a full path.  Does NOT include the file extension

        Args:
            fullPath:   The fully qualified path

        Returns:
            A string that is just the file name without the file extension
        """
        comps: List[str] = fullPath.split('/')      # break up into path components
        pName: str       = comps[len(comps) - 1]    # The file name is the last one
        s:     str       = pName[:-4]               # strip the suffix and the dot ('.')

        return s

    @staticmethod
    def secureInteger(x: str):
        if x is not None and x != '':
            return int(x)
        else:
            return 0

    @staticmethod
    def secureBoolean(x: str):
        try:
            if x is not None:
                if x in [True, "True", "true", 1, "1"]:
                    return True
        except (ValueError, Exception) as e:
            PyutUtils.clsLogger.error(f'secureBoolean error: {e}')
        return False

    @staticmethod
    def secureFloat(possibleFloatStr: str) -> float:
        if possibleFloatStr is not None:
            return float(possibleFloatStr)
        return 0.0

    @staticmethod
    def secureSplineInt(splineX: str) -> int:
        if splineX is None:
            return 0
        elif splineX == "_DeprecatedNonBool: False" or splineX == "False":
            return 0
        elif splineX == "_DeprecatedNonBool: True" or splineX == "True":
            return 1
        else:
            return int(splineX)

    @staticmethod
    def displayInformation(msg, title=None, parent=None):
        """
        Display information
        """
        em: ErrorManager = getErrorManager()
        em.newInformation(msg, title, parent)

    @staticmethod
    def displayWarning(msg, title=None, parent=None):
        """
        Display a warning
        """
        em: ErrorManager = getErrorManager()
        em.newWarning(msg, title, parent)

    @staticmethod
    def displayError(msg, title=None, parent=None):
        """
        Display an error
        """
        errMsg: str = ErrorManager.getErrorInfo()
        try:
            em = getErrorManager()
            em.newFatalError(msg, title, parent)
        except (ValueError, Exception) as e:
            eLog: Logger = getLogger(__name__)
            # TODO  I don't this is correct anymore
            eLog.error("Error in PyutUtils/displayError")
            eLog.error(f"Original error message was: {e}")
            eLog.error(errMsg)
            eLog.error("")
            eLog.error("New error is : ")
            errMsg = ErrorManager.getErrorInfo()
            eLog.error(errMsg)

    @staticmethod
    def assignID(numberOfIds: int) -> List[wxNewIdRef]:
        """
        Assign and return numberOfIds

        Sample use        : [Unique_Id1, Unique_Id2, Unique_Id3] = assignID(3)

        Args:
            numberOfIds: number of unique IDs to return

        Returns:  List of numbers which contain <numberOfIds> unique IDs
        """
        retList: List[wxNewIdRef] = []
        x: int = 0
        while x < numberOfIds:
            retList.append(wxNewIdRef())
            x += 1
        return retList

    @staticmethod
    def getJustTheFileName(filename):
        """
        Return just the file name portion of the fully qualified path

        Args:
            filename:  file name to display

        Returns:
            A better file name
        """
        return osPath.split(filename)[1]

    @staticmethod
    def snapCoordinatesToGrid(x: float, y: float, gridInterval: int) -> Tuple[float, float]:

        xDiff: float = x % gridInterval
        yDiff: float = y % gridInterval

        snappedX: float = x - xDiff
        snappedY: float = y - yDiff

        return snappedX, snappedY

    @classmethod
    def getBasePath(cls) -> str:
        return cls._basePath

    @classmethod
    def setBasePath(cls, newValue: str):
        retPath: str = PyutUtils._stripSrcOrTest(newValue)
        cls._basePath = retPath

    @classmethod
    def _stripSrcOrTest(cls, originalPath: str) -> str:

        if originalPath.endswith(PyutUtils.STRIP_SRC_PATH_SUFFIX):
            retPath: str = originalPath.rstrip(PyutUtils.STRIP_SRC_PATH_SUFFIX)
            retPath = PyutUtils._stripSrcOrTest(retPath)
        elif originalPath.endswith(PyutUtils.STRIP_TEST_PATH_SUFFIX):
            retPath: str = originalPath.rstrip(PyutUtils.STRIP_TEST_PATH_SUFFIX)
            retPath = PyutUtils._stripSrcOrTest(retPath)
        else:
            retPath: str = originalPath

        return retPath

    @classmethod
    def retrieveResourceText(cls, textType: ResourceTextType) -> str:
        """
        Look up and retrieve the text associated with the resource type

        Args:
            textType:  The text type from the 'well known' list

        Returns:  A long string
        """
        # textFileName = resource_filename(PyutUtils.RESOURCES_PACKAGE_NAME, textType.value)
        textFileName: str = PyutUtils.retrieveResourcePath(textType.value)
        cls.clsLogger.debug(f'text filename: {textFileName}')

        objRead = open(textFileName, 'r')
        requestedText: str = objRead.read()
        objRead.close()

        return requestedText

    @classmethod
    def retrieveResourcePath(cls, bareFileName: str) -> str:

        # Use this method in Python 3.9
        # from importlib_resources import files
        # configFilePath: str  = files('org.pyut.resources').joinpath(Pyut.JSON_LOGGING_CONFIG_FILENAME)

        try:
            fqFileName: str = resource_filename(PyutUtils.RESOURCES_PACKAGE_NAME, bareFileName)
        except (ValueError, Exception):
            #
            # Maybe we are in an app
            #
            from os import environ
            pathToResources: str = environ.get(f'{PyutUtils.RESOURCE_ENV_VAR}')
            fqFileName:      str = f'{pathToResources}/{PyutUtils.RESOURCES_PATH}/{bareFileName}'

        return fqFileName

    @classmethod
    def getResourcePath(cls, packageName: str, fileName: str):

        try:
            fqFileName: str = resource_filename(packageName, fileName)
        except (ValueError, Exception):
            #
            # Maybe we are in an app
            #
            from os import environ
            pathToResources: str = environ.get(f'{PyutUtils.RESOURCE_ENV_VAR}')
            fqFileName:      str = f'{pathToResources}/{packageName}/{fileName}'

        return fqFileName

    @classmethod
    def getTempFilePath(cls, fileName: str) -> str:

        if PyutPreferences().useDebugTempFileLocation is True:
            fqFileName: str = f'{PyutUtils.getBasePath()}{osSep}{fileName}'
        else:
            tempDir: str = gettempdir()
            fqFileName: str = f'{tempDir}{osSep}{fileName}'

        return fqFileName

    @classmethod
    def getScreenMetrics(cls) -> ScreenMetrics:

        scrResolution: Size              = ScreenDC().GetPPI()
        displaySize:   Tuple[int, int]   = DisplaySize()

        screenMetrics: ScreenMetrics = ScreenMetrics()

        screenMetrics.screenWidth  = displaySize[0]
        screenMetrics.screenHeight = displaySize[1]

        screenMetrics.dpiX = scrResolution.GetWidth()
        screenMetrics.dpiY = scrResolution.GetHeight()

        return screenMetrics
