
from typing import cast

from logging import Logger
from logging import getLogger

from os import sep as osSeparator

from sys import argv
from sys import exc_info
from traceback import extract_tb

from wx import Bitmap
from wx.adv import SplashScreen
from wx.adv import SPLASH_CENTRE_ON_PARENT
from wx.adv import SPLASH_TIMEOUT

from wx import OK
from wx import ICON_ERROR
from wx import ID_ANY

from wx import HelpProvider
from wx import SimpleHelpProvider
from wx import ScreenDC
from wx import MessageDialog
from wx import DefaultPosition as wxDefaultPosition
from wx import DefaultSize as wxDefaultSize

from wx import App as wxApp
from wx import Yield as wxYield

from org.pyut.preferences.PyutPreferences import PyutPreferences

from org.pyut.errorcontroller.ErrorManager import ErrorManager

from org.pyut.general.Globals import _

from org.pyut.ui.frame.PyutApplicationFrame import PyutApplicationFrame

from org.pyut.resources.img.splash.Splash6 import embeddedImage as splashImage


class PyutApp(wxApp):
    """
    PyutApp : main pyut application class.

    PyutApp is the main pyut application, a wxApp.

    """
    SPLASH_TIMEOUT_MSECS: int = 3000

    def __init__(self, redirect: bool, showSplash: bool = True, showMainFrame: bool = True):

        self.logger: Logger = getLogger(__name__)

        self._showSplash:    bool = showSplash
        self._showMainFrame: bool = showMainFrame

        super().__init__(redirect)

    def OnInit(self):
        """
        """
        provider: SimpleHelpProvider = SimpleHelpProvider()

        HelpProvider.Set(provider)
        try:
            # Create the SplashScreen
            if self._showSplash:

                bmp: Bitmap = splashImage.GetBitmap()
                self.splash = SplashScreen(bmp, SPLASH_CENTRE_ON_PARENT | SPLASH_TIMEOUT, PyutApp.SPLASH_TIMEOUT_MSECS, parent=None,
                                           pos=wxDefaultPosition, size=wxDefaultSize)

                self.logger.debug(f'Showing splash screen')
                self.splash.Show(True)
                wxYield()

            self._frame: PyutApplicationFrame = PyutApplicationFrame(cast(PyutApplicationFrame, None), ID_ANY, "Pyut")
            self.SetTopWindow(self._frame)
            self._AfterSplash()

            return True
        except (ValueError, Exception) as e:
            self.logger.error(f'{e}')
            dlg = MessageDialog(None, _(f"The following error occurred: {exc_info()[1]}"), _("An error occurred..."), OK | ICON_ERROR)
            errMessage: str = ErrorManager.getErrorInfo()
            self.logger.debug(errMessage)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def _AfterSplash(self):
        """
        AfterSplash : Occurs after the splash screen is launched; launch the application
        """
        try:
            # Handle application file names on the command line
            prefs: PyutPreferences = PyutPreferences()
            self._handleCommandLineFileNames(prefs)

            if self._frame is None:
                self.logger.error("Exiting due to previous errors")
                return False

            if self._showMainFrame is True:
                self._frame.Show(True)

            # Show full screen ?
            if prefs.fullScreen is True:
                dc = ScreenDC()
                self._frame.SetSize(dc.GetSize())
                self._frame.CentreOnScreen()

            return True

        except (ValueError, Exception) as e:
            dlg = MessageDialog(None, _(f"The following error occurred : {exc_info()[1]}"), _("An error occurred..."), OK | ICON_ERROR)
            self.logger.error(f'Exception: {e}')
            self.logger.error(f'Error: {exc_info()[0]}')
            self.logger.error('Msg: {exc_info()[1]}')
            self.logger.error('Trace:')
            for el in extract_tb(exc_info()[2]):
                self.logger.error(el)
            dlg.ShowModal()
            dlg.Destroy()
            return False

    def _handleCommandLineFileNames(self, prefs: PyutPreferences):

        if prefs.userDirectory is not None and len(prefs.userDirectory) != 0:
            loadDirectory: str = prefs.userDirectory
        else:
            loadDirectory: str = prefs.orgDirectory

        loadedAFile: bool     = False
        appFrame:    PyutApplicationFrame = self._frame
        for filename in [el for el in argv[1:] if el[0] != '-']:
            self.logger.info('Load file on command line')
            appFrame.loadByFilename(f'{loadDirectory}{osSeparator}{filename}')
            loadedAFile = True

        if loadedAFile is True:
            appFrame.removeEmptyProject()

    def OnExit(self):
        """
        """
        self.__do    = None
        self._frame  = None
        self.splash  = None
        # Seemed to be removed in latest versions of wxPython ???
        try:
            return wxApp.OnExit(self)
        except (ValueError, Exception) as e:
            self.logger.error(f'OnExit: {e}')
