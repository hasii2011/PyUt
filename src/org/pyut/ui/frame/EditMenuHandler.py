
from typing import List
from typing import cast

from logging import Logger
from logging import getLogger

from copy import copy

from wx import ClientDC
from wx import CommandEvent
from wx import Menu

from org.pyut.general.Mediator import Mediator

from org.pyut.miniogl.Diagram import Diagram

from org.pyut.model.PyutActor import PyutActor
from org.pyut.model.PyutClass import PyutClass
from org.pyut.model.PyutNote import PyutNote
from org.pyut.model.PyutObject import PyutObject
from org.pyut.model.PyutUseCase import PyutUseCase

from org.pyut.ogl.OglActor import OglActor
from org.pyut.ogl.OglClass import OglClass
from org.pyut.ogl.OglNote import OglNote
from org.pyut.ogl.OglObject import OglObject
from org.pyut.ogl.OglUseCase import OglUseCase
from org.pyut.ui.TreeNotebookHandler import TreeNotebookHandler

from org.pyut.ui.UmlClassDiagramsFrame import UmlClassDiagramsFrame

from org.pyut.PyutUtils import PyutUtils

from org.pyut.general.Globals import _


class EditMenuHandler:

    def __init__(self, editMenu: Menu):

        self.logger:    Logger   = getLogger(__name__)
        self._editMenu: Menu     = editMenu
        self._mediator: Mediator = Mediator()

        self._treeNotebookHandler: TreeNotebookHandler = self._mediator.getFileHandling()

        self._clipboard: List[PyutObject] = []

    # noinspection PyUnusedLocal
    def onCut(self, event: CommandEvent):
        """

        Args:
            event:
        """
        selected = self._mediator.getSelectedShapes()
        if len(selected) > 0:
            self._clipboard = []
        else:
            self.logger.warning(f'No selected objects')
            return

        canvas = selected[0].GetDiagram().GetPanel()

        # put the PyutObjects in the clipboard and remove their graphical representation from the diagram
        for obj in selected:
            obj.Detach()
            self._clipboard.append(obj.getPyutObject())

        # for obj in selected:
        #     self._clipboard.append(obj.getPyutObject())

        self.logger.info(f'Cut {len(self._clipboard)} objects')

        self._treeNotebookHandler.setModified(True)
        self._mediator.updateTitle()
        canvas.Refresh()

    # noinspection PyUnusedLocal
    def onCopy(self, event: CommandEvent):
        """
        TODO : adapt for OglLinks

        Args:
            event:
        """
        selected = self._mediator.getSelectedShapes()
        if len(selected) > 0:
            self._clipboard = []
        else:
            return

        # put a copy of the PyutObjects in the clipboard
        for obj in selected:
            obj = copy(obj.getPyutObject())
            obj.setLinks([])   # we don't want to copy the links
            self._clipboard.append(obj)

        self.logger.info(f'Copied {len(self._clipboard)} objects')

    # noinspection PyUnboundLocalVariable
    # noinspection PyUnusedLocal
    def onPaste(self, event: CommandEvent):
        """

        Args:
            event:
        """
        if len(self._clipboard) == 0:
            return

        self.logger.info(f'Pasting {len(self._clipboard)} objects')
        frame = self._mediator.getUmlFrame()
        if frame == -1:
            PyutUtils.displayError(_("No frame to paste into"))
            return

        # put the objects in the clipboard and remove them from the diagram
        x, y = 100, 100
        for obj in self._clipboard:
            obj = copy(obj)  # this is a PyutObject
            if isinstance(obj, PyutClass):
                po = OglClass(obj)
            elif isinstance(obj, PyutNote):
                po = OglNote(obj)
            elif isinstance(obj, PyutActor):
                po = OglActor(obj)
            elif isinstance(obj, PyutUseCase):
                po = OglUseCase(obj)
            else:
                self.logger.error("Error when try to paste object")
                return
            self.logger.info(f'Pasting: {po=}')
            self._mediator.getUmlFrame().addShape(po, x, y)
            x += 20
            y += 20

        canvas = po.GetDiagram().GetPanel()
        # the frame that contains the shape
        # specify the canvas on which we will paint
        dc: ClientDC = ClientDC(canvas)
        canvas.PrepareDC(dc)

        self._treeNotebookHandler.setModified(True)
        self._mediator.updateTitle()
        canvas.Refresh()

    # noinspection PyUnusedLocal
    def onSelectAll(self, event: CommandEvent):
        """

        Args:
            event:
        """
        frame: UmlClassDiagramsFrame = self._mediator.getUmlFrame()

        if frame is None:
            PyutUtils.displayError(_("No frame found !"))
            return
        diagram: Diagram         = frame.GetDiagram()
        shapes:  List[OglObject] = diagram.GetShapes()
        for shape in shapes:
            shape: OglObject = cast(OglObject, shape)
            shape.SetSelected(True)

        frame.Refresh()
