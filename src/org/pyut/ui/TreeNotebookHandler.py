
from typing import List
from typing import TypeVar
from typing import cast

from logging import Logger
from logging import getLogger

from os import path as osPath

from wx import EVT_MENU
from wx import EVT_TREE_ITEM_RIGHT_CLICK
from wx import FD_SAVE
from wx import FD_OVERWRITE_PROMPT
from wx import EVT_NOTEBOOK_PAGE_CHANGED
from wx import EVT_TREE_SEL_CHANGED
from wx import ID_ANY
from wx import ID_OK
from wx import ID_YES
from wx import ITEM_NORMAL
from wx import OK
from wx import YES_NO
from wx import ICON_ERROR
from wx import ICON_QUESTION
from wx import TR_HIDE_ROOT
from wx import TR_HAS_BUTTONS
from wx import CLIP_CHILDREN

from wx import TreeEvent
from wx import CommandEvent

from wx import TreeItemId
from wx import FileDialog
from wx import SplitterWindow
from wx import TreeCtrl
from wx import Notebook
from wx import MessageDialog
from wx import Menu

from wx import Yield as wxYield

from org.pyut.ui.CurrentDirectoryHandler import CurrentDirectoryHandler
from org.pyut.ui.PyutDocument import PyutDocument
from org.pyut.ui.PyutProject import PyutProject
from org.pyut.ui.UmlDiagramsFrame import UmlDiagramsFrame

from org.pyut.PyutUtils import PyutUtils
from org.pyut.PyutConstants import PyutConstants

from org.pyut.enums.DiagramType import DiagramType

from org.pyut.dialogs.DlgEditDocument import DlgEditDocument

from org.pyut.general.Globals import _

TreeDataType = TypeVar('TreeDataType', PyutProject, UmlDiagramsFrame)
DialogType   = TypeVar('DialogType', FileDialog, MessageDialog)


class TreeNotebookHandler:
    """
    The main portion of the User Interface.
    Used by the main application frame (PyutApplicationFrame) to host all UML frames,
    the notebook and the project tree.

    Handles the the project files, projects, documents and
    their relationship to the various UI Tree elements and the
    notebook tabs in the UI

    All actions called from PyutApplicationFrame are executed on the current frame
    """
    MAX_NOTEBOOK_PAGE_NAME_LENGTH: int = 12

    def __init__(self, parent):
        """

        Args:
            parent:     An PyutApplicationFrame
        """
        self.logger: Logger = getLogger(__name__)

        from org.pyut.ui.frame.PyutApplicationFrame import PyutApplicationFrame   # Prevent recursion import problem
        from org.pyut.ui.Mediator import Mediator
        self.__parent:  PyutApplicationFrame = parent
        self._mediator: Mediator = Mediator()

        self._projects:       List[PyutProject] = []
        self._currentProject: PyutProject       = cast(PyutProject, None)
        self._currentFrame:   UmlDiagramsFrame  = cast(UmlDiagramsFrame, None)

        if not self._mediator.isInScriptMode():

            self.__splitter:          SplitterWindow = cast(SplitterWindow, None)
            self.__projectTree:       TreeCtrl       = cast(TreeCtrl, None)
            self.__projectTreeRoot:   TreeItemId     = cast(TreeItemId, None)
            self.__notebook:          Notebook       = cast(Notebook, None)
            self.__projectPopupMenu:  Menu = cast(Menu, None)
            self.__documentPopupMenu: Menu = cast(Menu, None)

            self._initializeUIElements()

    @property
    def currentProject(self) -> PyutProject:
        return self._currentProject

    @currentProject.setter
    def currentProject(self, newProject: PyutProject):
        self.logger.info(f'{self.__notebook.GetRowCount()=}')
        self._currentProject = newProject

        self.__notebookCurrentPage = self.__notebook.GetPageCount() - 1
        self.__notebook.SetSelection(self.__notebookCurrentPage)

        self.logger.info(f'{self.__notebookCurrentPage=}')

    def registerUmlFrame(self, frame):
        """
        Register the current UML Frame

        Args:
            frame:
        """
        self._currentFrame = frame
        self._currentProject = self.getProjectFromFrame(frame)

    def showFrame(self, frame):
        self._frame = frame
        frame.Show()

    @property
    def currentFrame(self) -> UmlDiagramsFrame:
        return self._currentFrame

    @currentFrame.setter
    def currentFrame(self, newFrame: UmlDiagramsFrame):
        self._currentFrame = newFrame

    def getCurrentFrame(self):
        """
        Deprecated use the properties
        Returns:
            Get the current frame
        """
        return self._currentFrame

    def getProjects(self):
        """

        Returns:
            Return all projects
        """
        return self._projects

    def getProject(self, fileName: str):

        foundProject: PyutProject = cast(PyutProject, None)
        for currentProject in self._projects:
            if currentProject.getFilename() == fileName:
                foundProject = currentProject
                break

        return foundProject

    def isProjectLoaded(self, filename) -> bool:
        """

        Args:
            filename:

        Returns:
            `True` if the project is already loaded
        """
        for project in self._projects:
            if project.getFilename == filename:
                return True
        return False

    def isDefaultFilename(self, filename: str) -> bool:
        """

        Args:
            filename:

        Returns:
            `True` if the filename is the default filename
        """
        return filename == PyutConstants.DefaultFilename

    def openFile(self, filename, project=None) -> bool:
        """
        Open a file

        Args:
            filename:
            project:

        Returns:
            `True` if operation succeeded
        """
        self.logger.info(f'{filename=} {project=}')
        # Exit if the file is already loaded
        if not self.isDefaultFilename(filename) and self.isProjectLoaded(filename):
            PyutUtils.displayError(_("The selected file is already loaded !"))
            return False

        # Create a new project ?
        if project is None:
            project = PyutProject(PyutConstants.DefaultFilename, self.__notebook, self.__projectTree, self.__projectTreeRoot)

        # Load the project and add it
        try:
            if not project.loadFromFilename(filename):
                PyutUtils.displayError(_("The specified file can't be loaded !"))
                return False
            self._projects.append(project)
            #  self._ctrl.registerCurrentProject(project)
            self._currentProject = project
        except (ValueError, Exception) as e:
            PyutUtils.displayError(_(f"An error occurred while loading the project ! {e}"))
            return False

        try:
            if not self._mediator.isInScriptMode():
                for document in project.getDocuments():
                    diagramTitle: str = document.title
                    shortName:    str = self.shortenNotebookPageFileName(diagramTitle)
                    self.__notebook.AddPage(document.getFrame(), shortName)

                self.__notebookCurrentPage = self.__notebook.GetPageCount()-1
                self.__notebook.SetSelection(self.__notebookCurrentPage)

            if len(project.getDocuments()) > 0:
                self._currentFrame = project.getDocuments()[0].getFrame()

        except (ValueError, Exception) as e:
            PyutUtils.displayError(_(f"An error occurred while adding the project to the notebook {e}"))
            return False
        return True

    def insertFile(self, filename):
        """
        Insert a file in the current project

        Args:
            filename: filename of the project to insert

        """
        # Get current project
        project = self._currentProject

        # Save number of initial documents
        nbInitialDocuments = len(project.getDocuments())

        # Load data...
        if not project.insertProject(filename):
            PyutUtils.displayError(_("The specified file can't be loaded !"))
            return False

        # ...
        if not self._mediator.isInScriptMode():
            try:
                for document in project.getDocuments()[nbInitialDocuments:]:
                    self.__notebook.AddPage(document.getFrame(), document.getFullyQualifiedName())

                self.__notebookCurrentPage = self.__notebook.GetPageCount()-1
                self.__notebook.SetSelection(self.__notebookCurrentPage)
            except (ValueError, Exception) as e:
                PyutUtils.displayError(_(f"An error occurred while adding the project to the notebook {e}"))
                return False

        # Select first frame as current frame
        if len(project.getDocuments()) > nbInitialDocuments:
            self._frame = project.getDocuments()[nbInitialDocuments].getFrame()

    def saveFile(self) -> bool:
        """
        save to the current filename

        Returns:
            `True` if the save succeeds else `False`
        """
        currentProject = self._currentProject
        if currentProject is None:
            PyutUtils.displayError(_("No diagram to save !"), _("Error"))
            return False

        if currentProject.getFilename() is None or currentProject.getFilename() == PyutConstants.DefaultFilename:
            return self.saveFileAs()
        else:
            return currentProject.saveXmlPyut()

    def saveFileAs(self):
        """
        Ask for a filename and save the diagram data

        Returns:
            `True` if the save succeeds else `False`
        """
        if self._mediator.isInScriptMode():
            PyutUtils.displayError(_("Save File As is not accessible in script mode !"))
            return

        # Test if no diagram exists
        if self._mediator.getDiagram() is None:
            PyutUtils.displayError(_("No diagram to save !"), _("Error"))
            return

        currentDirectoryHandler: CurrentDirectoryHandler = CurrentDirectoryHandler()

        # Ask for filename
        filenameOK = False
        # TODO revisit this to figure out how to get rid of Pycharm warning 'dlg referenced before assignment'
        # Bad thing is dlg can be either a FileDialog or a MessageDialog
        dlg: DialogType = cast(DialogType, None)
        while not filenameOK:
            dlg = FileDialog(self.__parent,
                             defaultDir=currentDirectoryHandler.currentDirectory,
                             wildcard=_("Pyut file (*.put)|*.put"),
                             style=FD_SAVE | FD_OVERWRITE_PROMPT)

            # Return False if canceled
            if dlg.ShowModal() != ID_OK:
                dlg.Destroy()
                return False

            # Find if a specified filename is already opened
            filename = dlg.GetPath()

            if len([project for project in self._projects if project.getFilename() == filename]) > 0:
                dlg = MessageDialog(self.__parent,
                                    _("Error ! The filename '%s" + "' correspond to a project which is currently opened !" +
                                      " Please choose another filename !") % str(filename),
                                    _("Save change, filename error"), OK | ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
                return
            filenameOK = True

        project = self._currentProject
        project.setFilename(dlg.GetPath())
        project.saveXmlPyut()

        # Modify notebook text
        for i in range(self.__notebook.GetPageCount()):
            frame = self.__notebook.GetPage(i)
            document = [document for document in project.getDocuments() if document.getFrame() is frame]
            if len(document) > 0:
                document = document[0]
                if frame in project.getFrames():
                    diagramTitle: str = document.title
                    shortName:    str = self.shortenNotebookPageFileName(diagramTitle)

                    self.__notebook.SetPageText(i, shortName)
            else:
                self.logger.info("Not updating notebook in FileHandling")

        currentDirectoryHandler.currentDirectory = dlg.GetPath()

        project.setModified(False)
        dlg.Destroy()
        return True

    def newProject(self):
        """
        Begin a new project
        """
        project = PyutProject(PyutConstants.DefaultFilename, self.__notebook, self.__projectTree, self.__projectTreeRoot)
        self._projects.append(project)
        self._currentProject = project
        self._currentFrame = None

    def newDocument(self, docType: DiagramType):
        """
        Begin a new document

        Args:
            docType:  Type of document
        """
        project = self._currentProject
        if project is None:
            self.newProject()
            project = self.getCurrentProject()
        frame = project.newDocument(docType).getFrame()
        self._currentFrame  = frame
        self._currentProject = project

        if not self._mediator.isInScriptMode():
            shortName: str = self.shortenNotebookPageFileName(project.getFilename())
            self.__notebook.AddPage(frame, shortName)
            wxYield()
            self.__notebookCurrentPage  = self.__notebook.GetPageCount() - 1
            self.logger.info(f'Current notebook page: {self.__notebookCurrentPage}')
            self.__notebook.SetSelection(self.__notebookCurrentPage)

    def getCurrentProject(self) -> PyutProject:
        """
        Get the current working project

        Returns:
            the current project or None if not found
        """
        return self._currentProject

    def getProjectFromFrame(self, frame: UmlDiagramsFrame) -> PyutProject:
        """
        Return the project that owns a given frame

        Args:
            frame:  the frame to get This project

        Returns:
            PyutProject or None if not found
        """
        for project in self._projects:
            if frame in project.getFrames():
                return project
        return cast(PyutProject, None)

    def getCurrentDocument(self) -> PyutDocument:
        """
        Get the current document.

        Returns:
            the current document or None if not found
        """
        project = self.getCurrentProject()
        if project is None:
            return cast(PyutDocument, None)
        for document in project.getDocuments():
            if document.getFrame() is self._currentFrame:
                return document
        return cast(PyutDocument, None)

    def onClose(self) -> bool:
        """
        Close all files

        Returns:
            True if everything is ok
        """
        # Display warning if we are in scripting mode
        if self._mediator.isInScriptMode():
            print("WARNING : in script mode, the non-saved projects are closed without warning")

        # Close projects and ask for unsaved but modified projects
        if not self._mediator.isInScriptMode():
            for project in self._projects:
                if project.getModified() is True:
                    frames = project.getFrames()
                    if len(frames) > 0:
                        frame = frames[0]
                        frame.SetFocus()
                        wxYield()
                        # if self._ctrl is not None:
                            # self._ctrl.registerUMLFrame(frame)
                        self.showFrame(frame)
                    dlg = MessageDialog(self.__parent,
                                        _("Your diagram has not been saved! Would you like to save it ?"),
                                        _("Save changes ?"), YES_NO | ICON_QUESTION)
                    if dlg.ShowModal() == ID_YES:
                        # save
                        if self.saveFile() is False:
                            return False
                    dlg.Destroy()

        # dereference all
        self.__parent = None
        self._mediator = None
        self.__splitter = None
        self.__projectTree = None
        self.__notebook.DeleteAllPages()
        self.__notebook = None
        self.__splitter = None
        self._projects = None
        self._currentProject = None
        self._currentFrame = None

    def setModified(self, theNewValue: bool = True):
        """
        Set the Modified flag of the currently opened diagram

        Args:
            theNewValue:

        """
        if self._currentProject is not None:
            self._currentProject.setModified(theNewValue)
        self._mediator.updateTitle()

    def closeCurrentProject(self):
        """
        Close the current project

        Returns:
            True if everything is ok
        """
        if self._currentProject is None and self._currentFrame is not None:
            self._currentProject = self.getProjectFromFrame(self._currentFrame)
        if self._currentProject is None:
            PyutUtils.displayError(_("No frame to close !"), _("Error..."))
            return False

        # Display warning if we are in scripting mode
        if self._mediator.isInScriptMode():
            self.logger.warning("WARNING : in script mode, the non-saved projects are closed without warning")

        # Close the file
        if self._currentProject.getModified() is True and not self._mediator.isInScriptMode():
            frame = self._currentProject.getFrames()[0]
            frame.SetFocus()
            self.showFrame(frame)

            dlg = MessageDialog(self.__parent, _("Your project has not been saved. " 
                                                 "Would you like to save it ?"), _("Save changes ?"), YES_NO | ICON_QUESTION)
            if dlg.ShowModal() == ID_YES:
                if self.saveFile() is False:
                    return False

        # Remove the frame in the notebook
        if not self._mediator.isInScriptMode():
            pages = list(range(self.__notebook.GetPageCount()))
            pages.reverse()
            for i in pages:
                pageFrame = self.__notebook.GetPage(i)
                if pageFrame in self._currentProject.getFrames():
                    self.__notebook.DeletePage(i)

        self._currentProject.removeFromTree()
        self._projects.remove(self._currentProject)

        self._currentProject = None
        self._currentFrame = None

        return True

    def removeAllReferencesToUmlFrame(self, umlFrame):
        """
        Remove all my references to a given uml frame

        Args:
            umlFrame:

        """
        # Current frame ?
        if self._currentFrame is umlFrame:
            self._currentFrame = None

        # Exit if we are in scripting mode
        if self._mediator.isInScriptMode():
            return

        for i in range(self.__notebook.GetPageCount()):
            pageFrame = self.__notebook.GetPage(i)
            if pageFrame is umlFrame:
                self.__notebook.DeletePage(i)
                break

    def getProjectFromOglObjects(self, oglObjects) -> PyutProject:
        """
        Get a project that owns oglObjects

        Args:
            oglObjects: Objects to find their parents

        Returns:
            PyutProject if found, None else
        """
        for project in self._projects:
            for frame in project.getFrames():
                diagram = frame.getDiagram()
                shapes = diagram.GetShapes()
                for obj in oglObjects:
                    if obj in shapes:
                        self.logger.info(f'obj: {obj} is part of project: {project}')
                        return project

        self.logger.warning(f'The oglObjects: {oglObjects} appear to not belong to any project')
        return cast(PyutProject, None)

    def _initializeUIElements(self):
        """
        Instantiate all the UI elements
        """
        self.__splitter        = SplitterWindow(self.__parent, ID_ANY)
        self.__projectTree     = TreeCtrl(self.__splitter, ID_ANY, style=TR_HIDE_ROOT + TR_HAS_BUTTONS)
        self.__projectTreeRoot = self.__projectTree.AddRoot(_("Root"))

        #  self.__projectTree.SetPyData(self.__projectTreeRoot, None)
        # Expand root, since wx.TR_HIDE_ROOT is not supported under windows
        # Not supported for hidden tree since wx.Python 2.3.3.1 ?
        #  self.__projectTree.Expand(self.__projectTreeRoot)

        # diagram container
        self.__notebook = Notebook(self.__splitter, ID_ANY, style=CLIP_CHILDREN)

        # Set splitter
        self.__splitter.SetMinimumPaneSize(20)
        self.__splitter.SplitVertically(self.__projectTree, self.__notebook, 160)

        self.__notebookCurrentPage = -1

        # Callbacks
        self.__parent.Bind(EVT_NOTEBOOK_PAGE_CHANGED, self._onNotebookPageChanged)
        self.__parent.Bind(EVT_TREE_SEL_CHANGED, self._onProjectTreeSelChanged)
        self.__projectTree.Bind(EVT_TREE_ITEM_RIGHT_CLICK, self.__onProjectTreeRightClick)

    # noinspection PyUnusedLocal
    def _onNotebookPageChanged(self, event):
        """
        Callback for notebook page changed

        Args:
            event:
        """
        self.__notebookCurrentPage = self.__notebook.GetSelection()
        self.logger.info(f'{self.__notebookCurrentPage=}')
        if self._mediator is not None:      # hasii maybe I got this right from the old pre PEP-8 code
            #  self._ctrl.registerUMLFrame(self._getCurrentFrame())
            self._currentFrame = self._getCurrentFrameFromNotebook()

            self._mediator.updateTitle()
        self.__getTreeItemFromFrame(self._currentFrame)
        # self.__projectTree.SelectItem(getID(self.getCurrentFrame()))
        # TODO : how can I do getID ???

        # Register the current project
        self._currentProject = self.getProjectFromFrame(self._currentFrame)

    def _onProjectTreeSelChanged(self, event: TreeEvent):
        """
        Callback for notebook page changed

        Args:
            event:
        """
        itm:      TreeItemId = event.GetItem()
        pyutData: TreeDataType = self.__projectTree.GetItemData(itm)
        self.logger.info(f'Clicked on: {itm=} `{pyutData=}`')
        # Use our own base type
        if isinstance(pyutData, UmlDiagramsFrame):
            frame: UmlDiagramsFrame = pyutData
            self._currentFrame = frame
            self._currentProject = self.getProjectFromFrame(frame)

            # Select the frame in the notebook
            for i in range(self.__notebook.GetPageCount()):
                pageFrame = self.__notebook.GetPage(i)
                if pageFrame is frame:
                    self.__notebook.SetSelection(i)
                    return
        elif isinstance(pyutData, PyutProject):
            self._currentProject = pyutData

    def _getCurrentFrameFromNotebook(self):
        """
        Get the current frame in the notebook

        Returns:
        """
        # Return None if we are in scripting mode
        if self._mediator.isInScriptMode():
            return None

        noPage = self.__notebookCurrentPage
        self.logger.info(f'{noPage=}')
        if noPage == -1:
            return None
        frame = self.__notebook.GetPage(noPage)
        return frame

    def __onProjectTreeRightClick(self, treeEvent: TreeEvent):

        itemId: TreeItemId = treeEvent.GetItem()
        data = self.__projectTree.GetItemData(item=itemId)
        self.logger.info(f'Item Data: `{data}`')
        if isinstance(data, PyutProject):
            self.__popupProjectMenu()
        elif isinstance(data, UmlDiagramsFrame):
            self.__popupProjectDocumentMenu()

    def __popupProjectMenu(self):

        self._mediator.resetStatusText()

        if self.__projectPopupMenu is None:
            self.logger.info(f'Create the project popup menu')
            [closeProjectMenuID] = PyutUtils.assignID(1)
            popupMenu: Menu = Menu('Actions')
            popupMenu.AppendSeparator()
            popupMenu.Append(closeProjectMenuID, 'Close Project', 'Remove project from tree', ITEM_NORMAL)
            popupMenu.Bind(EVT_MENU, self.__onCloseProject, id=closeProjectMenuID)
            self.__projectPopupMenu = popupMenu

        self.logger.info(f'currentProject: `{self._currentProject}`')
        self.__parent.PopupMenu(self.__projectPopupMenu)

    def __popupProjectDocumentMenu(self):

        if self.__documentPopupMenu is None:

            self.logger.info(f'Create the document popup menu')

            [editDocumentNameMenuID, removeDocumentMenuID] = PyutUtils.assignID(2)

            popupMenu: Menu = Menu('Actions')
            popupMenu.AppendSeparator()
            popupMenu.Append(editDocumentNameMenuID, 'Edit Document Name', 'Change document name', ITEM_NORMAL)
            popupMenu.Append(removeDocumentMenuID,   'Remove Document',    'Delete it',            ITEM_NORMAL)

            popupMenu.Bind(EVT_MENU, self.__onEditDocumentName, id=editDocumentNameMenuID)
            popupMenu.Bind(EVT_MENU, self.__onRemoveDocument,   id=removeDocumentMenuID)

            self.__documentPopupMenu = popupMenu

        self.logger.info(f'Current Document: `{self.getCurrentDocument()}`')
        self.__parent.PopupMenu(self.__documentPopupMenu)

    # noinspection PyUnusedLocal
    def __onCloseProject(self, event: CommandEvent):
        self.closeCurrentProject()

    # noinspection PyUnusedLocal
    def __onEditDocumentName(self, event: CommandEvent):

        self.logger.info(f'self.__notebookCurrentPage: {self.__notebookCurrentPage} nb Selection: {self.__notebook.GetSelection()}')
        if self.__notebookCurrentPage == -1:
            self.__notebookCurrentPage = self.__notebook.GetSelection()    # must be default empty project

        currentDocument: PyutDocument = self.getCurrentDocument()
        dlgEditDocument: DlgEditDocument = DlgEditDocument(parent=self.getCurrentFrame(),
                                                           dialogIdentifier=ID_ANY,
                                                           document=currentDocument)
        dlgEditDocument.Destroy()

        #
        # TODO can cause
        #     self.__notebook.SetPageText(page=self.__notebookCurrentPage, text=currentDocument.title)
        # wx._core.wxAssertionError: C++ assertion ""((nPage) < GetPageCount())""
        # failed at dist-osx-py38/build/ext/wxWidgets/src/osx/notebook_osx.cpp(120)
        # in SetPageText(): SetPageText: invalid notebook page
        #
        self.__notebook.SetPageText(page=self.__notebookCurrentPage, text=currentDocument.title)
        currentDocument.updateTreeText()

    # noinspection PyUnusedLocal
    def __onRemoveDocument(self, event: CommandEvent):
        """
        Invoked from the popup menu in the tree

        Args:
            event:
        """
        project:         PyutProject  = self.getCurrentProject()
        currentDocument: PyutDocument = self.getCurrentDocument()
        project.removeDocument(currentDocument)

    def __getTreeItemFromFrame(self, frame: UmlDiagramsFrame) -> TreeItemId:

        projectTree: TreeCtrl = self.__projectTree

        treeRootItemId: TreeItemId   = projectTree.GetRootItem()
        pyutData:       TreeDataType = projectTree.GetItemData(treeRootItemId)

        self.logger.info(f'{treeRootItemId=} {pyutData=} {frame=}')

        self.logger.info(f'{projectTree.GetCount()=}')
        return treeRootItemId

    def shortenNotebookPageFileName(self, filename: str) -> str:
        """
        Return a shorter filename to display; For file names longer
        than `MAX_NOTEBOOK_PAGE_NAME_LENGTH` this method takes the first
        four characters and the last eight as the shortened file name

        Args:
            filename:  The file name to display

        Returns:
            A better file name
        """
        justFileName: str = osPath.split(filename)[1]
        if len(justFileName) > TreeNotebookHandler.MAX_NOTEBOOK_PAGE_NAME_LENGTH:
            firstFour: str = justFileName[:4]
            lastEight: str = justFileName[-8:]
            return f'{firstFour}{lastEight}'
        else:
            return justFileName
