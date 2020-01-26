
from typing import Tuple

from logging import Logger
from logging import getLogger

from math import sqrt

from wx import BLACK_PEN

from org.pyut.MiniOgl.LineShape import LineShape
from org.pyut.MiniOgl.ShapeEventHandler import ShapeEventHandler

from org.pyut.PyutLink import PyutLink

from org.pyut.enums.PyutAttachmentPoint import PyutAttachmentPoint
from org.pyut.ogl.IllegalOperationException import IllegalOperationException


def getOrient(srcX, srcY, destX, destY) -> PyutAttachmentPoint:
    """
    Giving a source and destination, returns where the destination
    is located according to the source.

    @param int srcX  : X pos of src point
    @param int srcY  : Y pos of src point
    @param int destX : X pos of dest point
    @param int destY : Y pos of dest point
    """
    deltaX = srcX - destX
    deltaY = srcY - destY
    if deltaX > 0:  # dest is not east
        if deltaX > abs(deltaY):    # dest is west
            return PyutAttachmentPoint.WEST
        elif deltaY > 0:
            return PyutAttachmentPoint.NORTH
        else:
            return PyutAttachmentPoint.SOUTH
    else:   # dest is not west
        if -deltaX > abs(deltaY):   # dest is east
            return PyutAttachmentPoint.EAST
        elif deltaY > 0:
            return PyutAttachmentPoint.NORTH
        else:
            return PyutAttachmentPoint.SOUTH


class OglLink(LineShape, ShapeEventHandler):
    """
    Abstract class for graphical link.
    This class should be the base class for every type of link. It implements
    the following functions :
        - Link between objects position management
        - Control points (2)
        - Data layer link association
        - Source and destination objects

    You can inherit from this class to implement your favorite type of links
    like `OglAssociation`.

    There is a link factory (See `OglLinkFactory`) you can use to build
    the different type of links that exist.

    """

    def __init__(self, srcShape, pyutLink, dstShape, srcPos=None, dstPos=None):
        """
        Constructor.

        @param  srcShape : Source shape
        @param  pyutLink : Conceptual links associated with the
                                   graphical links.
        @param  dstShape : Destination shape

        @author Philippe Waelti <pwaelti@eivd.ch>
        @modified Laurent Burgbacher <lb@alawa.ch>
            Support for miniogl
        @modified C.Dutoit 20021125 : Added srcPos and dstPos
        """

        # Associate src and dest shapes
        self._srcShape  = srcShape
        self._destShape = dstShape

        if srcPos is None and dstPos is None:
            srcX, srcY = self._srcShape.GetPosition()
            dstX, dstY = self._destShape.GetPosition()

            orient = getOrient(srcX,  srcY, dstX, dstY)

            sw, sh = self._srcShape.GetSize()
            dw, dh = self._destShape.GetSize()
            if orient == PyutAttachmentPoint.NORTH:
                srcX, srcY = sw/2, 0
                dstX, dstY = dw/2, dh
            elif orient == PyutAttachmentPoint.SOUTH:
                srcX, srcY = sw/2, sh
                dstX, dstY = dw/2, 0
            elif orient == PyutAttachmentPoint.EAST:
                srcX, srcY = sw, sh/2
                dstX, dstY = 0, dh/2
            elif orient == PyutAttachmentPoint.WEST:
                srcX, srcY = 0, sh/2
                dstX, dstY = dw, dh/2

            # ============== Avoid overlining; Added by C.Dutoit ================
            # lstAnchorsPoints = [anchor.GetRelativePosition()
            #    for anchor in srcShape.GetAnchors()]
            # while (srcX, srcY) in lstAnchorsPoints:
            #    if orient == PyutAttachmentPoint.NORTH or orient == PyutAttachmentPoint.SOUTH:
            #        srcX+=10
            #    else:
            #        srcY+=10

            # lstAnchorsPoints = [anchor.GetRelativePosition()
            #    for anchor in dstShape.GetAnchors()]
            # while (dstX, dstY) in lstAnchorsPoints:
            #    if orient == PyutAttachmentPoint.NORTH or orient == PyutAttachmentPoint.SOUTH:
            #        dstX+=10
            #    else:
            #        dstY+=10

            # =========== end avoid overlining-Added by C.Dutoit ================
        else:
            # Get given position
            (srcX, srcY) = srcPos
            (dstX, dstY) = dstPos

        src = self._srcShape.AddAnchor(srcX, srcY)
        dst = self._destShape.AddAnchor(dstX, dstY)
        src.SetPosition(srcX, srcY)
        dst.SetPosition(dstX, dstY)
        src.SetVisible(False)
        dst.SetVisible(False)

        src.SetDraggable(True)
        dst.SetDraggable(True)

        # Init
        LineShape.__init__(self, src, dst)
        self.logger: Logger = getLogger(__name__)

        # Set up painting colors
        self.SetPen(BLACK_PEN)

        # Keep reference to the PyutLink for mouse events, in order
        # to can find back the corresponding link
        if pyutLink is not None:
            self._link = pyutLink
        else:
            self._link = PyutLink()

    def getSourceShape(self):
        """
        Return the source shape for this link.

        @return OglObject
        @since 1.22
        @author Laurent Burgbacher <lb@alawa.ch>
        """
        return self._srcShape

    def getDestinationShape(self):
        """
        Return the destination shape for this link.

        @return OglObject
        @since 1.22
        @author Laurent Burgbacher <lb@alawa.ch>
        """
        return self._destShape

    def getPyutObject(self):
        """
        Returns the associatied PyutLink.

        @return PyutLink
        @since 1.0
        @author Philippe Waelti <pwaelti@eivd.ch>
        """
        return self._link

    def setPyutObject(self, pyutLink):
        """
        Sets the associatied PyutLink.

        @param PyutLink pyutLink : link to associate
        @since 1.0
        @author Philippe Waelti <pwaelti@eivd.ch>
        """
        self._link = pyutLink

    def Detach(self):
        """
        Detach the line and all its line points, including src and dst.

        @since 1.0
        @author Laurent Burgbacher <lb@alawa.ch>
        """
        if self._diagram is not None and not self._protected:
            LineShape.Detach(self)
            self._srcAnchor.SetProtected(False)
            self._dstAnchor.SetProtected(False)
            self._srcAnchor.Detach()
            self._dstAnchor.Detach()
            try:
                self.getSourceShape().getLinks().remove(self)
            except ValueError:
                pass
            try:
                self.getDestinationShape().getLinks().remove(self)
            except ValueError:
                pass
            try:
                self._link.getSource().getLinks().remove(self._link)
            except ValueError:
                pass

    def optimizeLine(self):
        """
        Optimize line, so that the line length is minimized
        """
        self.logger.info("OptimizeLine")
        # Get elements
        srcAnchor = self.GetSource()
        dstAnchor = self.GetDestination()

        srcX, srcY = self._srcShape.GetPosition()
        dstX, dstY = self._destShape.GetPosition()

        srcSize = self._srcShape.GetSize()
        dstSize = self._destShape.GetSize()

        self.logger.info(f"({srcX},{srcY}) / ({dstX},{dstY})")
        # Find new positions
        # Little tips
        osrcX, osrcY, odstX, odstY = dstX, dstY, srcX, srcY

        osrcX += dstSize[0]/2
        osrcY += dstSize[1]/2
        odstX += srcSize[0]/2
        odstY += srcSize[1]/2

        srcAnchor.SetPosition(osrcX, osrcY)
        dstAnchor.SetPosition(odstX, odstY)

    def _computeLinkLength(self, srcPosition: Tuple[float, float], destPosition: Tuple[float, float]) -> float:
        """

        Returns:  The length of the link between the source shape and destination shape
        """
        dx, dy = self._computeDxDy(srcPosition, destPosition)
        linkLength = sqrt(dx*dx + dy*dy)
        if linkLength == 0:
            linkLength = 0.01

        return linkLength

    def _computeDxDy(self, srcPosition: Tuple[float, float], destPosition: Tuple[float, float]) -> Tuple[float, float]:
        """

        Returns: a tuple of deltaX and deltaY of the shape position
        """
        if self._srcShape is None or self._destShape is None:
            raise IllegalOperationException('Either the source or the destination shape is None')

        # srcX, srcY = self._srcShape.GetPosition()
        # dstX, dstY = self._destShape.GetPosition()
        srcX, srcY = srcPosition
        dstX, dstY = destPosition

        dx = dstX - srcX
        dy = dstY - srcY

        return dx, dy
