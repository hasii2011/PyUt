
from math import pi
from math import atan
from math import cos
from math import sin

from wx import BLACK_BRUSH
from wx import BLACK_PEN
from wx import DC
from wx import FONTFAMILY_DEFAULT
from wx import FONTSTYLE_NORMAL
from wx import FONTWEIGHT_NORMAL
from wx import WHITE_BRUSH

from wx import Font

from org.pyut.ogl.OglLink import OglLink

# Kind of labels
[CENTER, SRC_CARD, DEST_CARD] = list(range(3))


class OglAssociation(OglLink):

    TEXT_SHAPE_FONT_SIZE: int = 12

    """
    Graphical link representation of association, (simple line, no arrow).
    To get a new link, you should use the `OglLinkFatory` and specify
    the kind of link you want, OGL_ASSOCIATION for an instance of this class.
    """
    def __init__(self, srcShape, pyutLink, dstShape):
        """
        Constructor.

        @param  srcShape : Source shape
        @param  pyutLink : Conceptual links associated with the graphical links.
        @param  dstShape : Destination shape

        """
        super().__init__(srcShape, pyutLink, dstShape)

        # Add labels
        self._labels = {}
        srcPos  = srcShape.GetPosition()
        destPos = dstShape.GetPosition()

        linkLength: float = self._computeLinkLength(srcPosition=srcPos, destPosition=destPos)
        dx, dy            = self._computeDxDy(srcPosition=srcPos, destPosition=destPos)

        cenLblX = -dy * 5 / linkLength
        cenLblY = dx * 5 / linkLength
        srcLblX = 20 * dx/linkLength      # - dy*5/l
        srcLblY = 20 * dy/linkLength     # + dx*5/l
        dstLblX = -20 * dx/linkLength    # + dy*5/l
        dstLblY = -20 * dy/linkLength    # - dy*5/l

        self._defaultFont = Font(OglAssociation.TEXT_SHAPE_FONT_SIZE, FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL)

        # Initialize labels objects
        self._labels[CENTER]    = self.AddText(cenLblX, cenLblY,      "", font=self._defaultFont)
        self._labels[SRC_CARD]  = self._srcAnchor.AddText(srcLblX, srcLblY, "", font=self._defaultFont)
        self._labels[DEST_CARD] = self._dstAnchor.AddText(dstLblX, dstLblY, "", font=self._defaultFont)
        self.updateLabels()
        self.SetDrawArrow(False)

    def updateLabels(self):
        """
        Update the labels according to the link.

        @since 1.14
        @author Laurent Burgbacher <lb@alawa.ch>
        """
        def prepareLabel(textShape, text):
            """
            Update a label.

            @author Laurent Burgbacher <lb@alawa.ch>
            """
            # If label should be drawn
            if text.strip() != "":
                textShape.SetText(text)
                textShape.SetVisible(True)
            else:
                textShape.SetVisible(False)

        # Prepares labels
        prepareLabel(self._labels[CENTER], self._link.getName())
        # prepareLabel(self._labels[SRC_CARD], self._link.getSrcCard())
        # prepareLabel(self._labels[DEST_CARD], self._link.getDestinationCardinality())
        prepareLabel(self._labels[SRC_CARD],  self._link.sourceCardinality)
        prepareLabel(self._labels[DEST_CARD], self._link.destinationCardinality)

    def getLabels(self):
        """
        Get the labels.

        @return TextShape []
        @since 1.0
        """
        return self._labels

    # noinspection PyUnusedLocal
    def Draw(self, dc: DC, withChildren: bool = False):
        """
        Called for contents drawing of links.

        @param dc : Device context
        @param  withChildren : draw the children or not

        @since 1.0
        @author Philippe Waelti <pwaelti@eivd.ch>
        """
        self.updateLabels()
        OglLink.Draw(self, dc)

    def drawLosange(self, dc, filled=False):
        """
        Draw an arrow at the begining of the line.

        @param dc
        @param bool filled : True if the losange must be filled, False otherwise

        Note:  Losange is French for 'diamond'

        @since 1.0
        @author Laurent Burgbacher <lb@alawa.ch>
        """
        pi_6 = pi/6
        points = []
        line = self.GetSegments()
        x1, y1 = line[1]
        x2, y2 = line[0]
        a = x2 - x1
        b = y2 - y1
        if abs(a) < 0.01:  # vertical segment
            if b > 0:
                alpha = -pi/2
            else:
                alpha = pi/2
        else:
            if a == 0:
                if b > 0:
                    alpha = pi/2
                else:
                    alpha = 3 * pi / 2
            else:
                alpha = atan(b/a)
        if a > 0:
            alpha += pi
        alpha1 = alpha + pi_6
        alpha2 = alpha - pi_6
        size = 8
        points.append((x2 + size * cos(alpha1), y2 + size * sin(alpha1)))
        points.append((x2, y2))
        points.append((x2 + size * cos(alpha2), y2 + size * sin(alpha2)))
        points.append((x2 + 2*size * cos(alpha),  y2 + 2*size * sin(alpha)))
        dc.SetPen(BLACK_PEN)
        if filled:
            dc.SetBrush(BLACK_BRUSH)
        else:
            dc.SetBrush(WHITE_BRUSH)
        dc.DrawPolygon(points)
        dc.SetBrush(WHITE_BRUSH)
