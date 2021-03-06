
from typing import Tuple

from logging import Logger
from logging import getLogger
from logging import INFO
from logging import DEBUG

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

from org.pyut.ogl.OglAssociationLabel import OglAssociationLabel

from org.pyut.ogl.OglLink import OglLink
from org.pyut.ogl.OglPosition import OglPosition


class OglAssociation(OglLink):

    TEXT_SHAPE_FONT_SIZE: int = 12

    clsLogger: Logger = getLogger(__name__)
    """
    Graphical link representation of an association, (simple line, no arrow).
    To get a new link,  use the `OglLinkFactory` and specify
    the link type.  .e.g. OGL_ASSOCIATION for an instance of this class.
    """
    def __init__(self, srcShape, pyutLink, dstShape):
        """

        Args:
            srcShape:   Source shape
            pyutLink:   Conceptual links associated with the graphical links.
            dstShape:   Destination shape
        """
        super().__init__(srcShape, pyutLink, dstShape)

        self._centerLabel:            OglAssociationLabel = OglAssociationLabel()
        self._sourceCardinality:      OglAssociationLabel = OglAssociationLabel()
        self._destinationCardinality: OglAssociationLabel = OglAssociationLabel()

        self._defaultFont: Font = Font(OglAssociation.TEXT_SHAPE_FONT_SIZE, FONTFAMILY_DEFAULT, FONTSTYLE_NORMAL, FONTWEIGHT_NORMAL)

        self.SetDrawArrow(False)

        # self.__hackCenterLabelPosition(cenLblX, cenLblY)

    @property
    def centerLabel(self) -> OglAssociationLabel:
        return self._centerLabel

    @centerLabel.setter
    def centerLabel(self, newValue: OglAssociationLabel):
        self._centerLabel = newValue

    @property
    def sourceCardinality(self) -> OglAssociationLabel:
        return self._sourceCardinality

    @sourceCardinality.setter
    def sourceCardinality(self, newValue: OglAssociationLabel):
        self._sourceCardinality = newValue

    @property
    def destinationCardinality(self) -> OglAssociationLabel:
        return self._destinationCardinality

    @destinationCardinality.setter
    def destinationCardinality(self, newValue: OglAssociationLabel):
        self._destinationCardinality = newValue

    def Draw(self, dc: DC, withChildren: bool = False):
        """
        Called for the content drawing of links.
        We are going to draw all of our stuff, cardinality, Link name, etc; So,

        Args:
            dc:     Device context
            withChildren:   draw the children or not
        """
        OglLink.Draw(self, dc, withChildren)
        sp: Tuple[float, float] = self._srcAnchor.GetPosition()
        dp: Tuple[float, float] = self._dstAnchor.GetPosition()

        oglSp: OglPosition = OglPosition(x=sp[0], y=sp[1])
        oglDp: OglPosition = OglPosition(x=dp[0], y=dp[1])

        self._drawSourceCardinality(dc=dc, sp=oglSp, dp=oglDp)
        self._drawCenterLabel(dc=dc, sp=oglSp, dp=oglDp)
        self._drawDestinationCardinality(dc=dc, sp=oglSp, dp=oglDp)

    def drawLosange(self, dc: DC, filled: bool = False):
        """
        Draw an arrow at the beginning of the line.

        Args:
            dc:         The device context
            filled:     True if the losange must be filled, False otherwise

        Note:  Losange is French for 'diamond'
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

    def _drawCenterLabel(self, dc: DC, sp: OglPosition, dp: OglPosition):

        centerX, centerY = self._computeMidPoint(srcPosition=sp, destPosition=dp)

        saveFont: Font = dc.GetFont()
        dc.SetFont(self._defaultFont)

        centerText: str = self._link.getName()
        dc.DrawText(centerText, centerX, centerY)
        dc.SetFont(saveFont)
        self._centerLabel = self.__updateAssociationLabel(self._centerLabel, x=centerX, y=centerY, text=centerText)

    def _drawSourceCardinality(self, dc: DC, sp: OglPosition, dp: OglPosition):

        dx, dy            = self._computeDxDy(srcPosition=sp, destPosition=dp)

        linkLength: float = self._computeLinkLength(srcPosition=sp, destPosition=dp)

        srcLblX = (20 * dx / linkLength - dx * 5 / linkLength) + sp.x
        srcLblY = (20 * dy / linkLength + dy * 5 / linkLength) + sp.y

        if OglAssociation.clsLogger.isEnabledFor(INFO):
            info = (
                f'{sp=} '
                f'{dp=} '
                f'{dx=} '
                f'{dy=} '
                f'linkLength={linkLength:.2f} '
                f'srcLblX={srcLblX:.2f} '
                f'srcLblY={srcLblY:.2f}'
            )
            OglAssociation.clsLogger.info(info)
        saveFont: Font = dc.GetFont()
        dc.SetFont(self._defaultFont)

        sourceCardinalityText: str = self._link.sourceCardinality
        dc.DrawText(sourceCardinalityText, srcLblX, srcLblY)
        dc.SetFont(saveFont)
        self._sourceCardinality = self.__updateAssociationLabel(self._sourceCardinality, x=srcLblX, y=srcLblY, text=sourceCardinalityText)

    def _drawDestinationCardinality(self, dc: DC, sp: OglPosition, dp: OglPosition):

        dx, dy            = self._computeDxDy(srcPosition=sp, destPosition=dp)

        linkLength: float = self._computeLinkLength(srcPosition=sp, destPosition=dp)

        dstLblX = (-20 * dx / linkLength + dy * 5 / linkLength) + dp.x
        dstLblY = (-20 * dy / linkLength - dy * 5 / linkLength) + dp.y

        saveFont: Font = dc.GetFont()
        dc.SetFont(self._defaultFont)

        destinationCardinalityText: str = self._link.destinationCardinality
        dc.DrawText(destinationCardinalityText, dstLblX, dstLblY)
        self._destinationCardinality = self.__updateAssociationLabel(self._destinationCardinality, x=dstLblX, y=dstLblY, text=destinationCardinalityText)
        dc.SetFont(saveFont)

    def __updateAssociationLabel(self, associationLabel: OglAssociationLabel, x: float, y: float, text: str) -> OglAssociationLabel:

        associationLabel.oglPosition.x = x
        associationLabel.oglPosition.y = y
        associationLabel.text          = text

        return associationLabel

    @staticmethod
    def _computeMidPoint(srcPosition: OglPosition, destPosition: OglPosition) -> Tuple[float, float]:
        """

        Args:
            srcPosition:        Tuple x,y source position
            destPosition:       Tuple x,y destination position

        Returns:
                A tuple that is the x,y position between `srcPosition` and `destPosition`

            [Reference]: https://mathbitsnotebook.com/Geometry/CoordinateGeometry/CGmidpoint.html
        """
        if OglAssociation.clsLogger.isEnabledFor(DEBUG):
            OglAssociation.clsLogger.debug(f'{srcPosition=}  {destPosition=}')
        x1 = srcPosition.x
        y1 = srcPosition.y
        x2 = destPosition.x
        y2 = destPosition.y

        midPointX = abs(x1 + x2) / 2
        midPointY = abs(y1 + y2) / 2

        return midPointX, midPointY

    def __repr__(self):
        return f'OglAssociation - from: {self.getSourceShape()} to: {self.getDestinationShape()}'
