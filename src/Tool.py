

class Tool:
    """
    Tool : a tool for pyut's toolboxes

    :author: C.Dutoit
    :contact: <dutoitc@hotmail.com>
    :version: $Revision: 1.5 $
    """

    def __init__(self, theId, img, caption, tooltip, initialCategory, actionCallback, propertiesCallback, wxID=-1, isToggle=False):
        """
        Constructor.

        @param string theId : a unique ID for this tool (plugin id + tool id)
        @param img2py_string img : img for that tool
        @param string caption : caption for this tool
        @param string tooltip : tip for this tool, role
        @param string initialCategory : category for this tool (plugin id?)
        @param function actionCallback : callback function for doing action
        @param function propertiesCallback : callback function for displaying tool properties
        @param wxID : a wx unique ID, used for callback
        @param isToggle : True if the tool can be toggled

        @author C.Dutoit
        """
        self._id  = theId
        self._img = img
        self._caption = caption
        self._tooltip = tooltip
        self._initialCategory    = initialCategory
        self._actionCallback     = actionCallback
        self._propertiesCallback = propertiesCallback
        self._wxID     = wxID
        self._isToggle = isToggle

    # Some accessors
    def getImg(self):
        return self._img

    def getCaption(self):
        return self._caption

    def getToolTip(self):
        return self._tooltip

    def getInitialCategory(self):
        return self._initialCategory

    def getActionCallback(self):
        return self._actionCallback

    def getPropertiesCallback(self):
        return self._propertiesCallback

    def getWXID(self):
        return self._wxID

    def getIsToggle(self):
        return self._isToggle

    def __repr__(self):
        return f'Tool: Caption: `{self._caption}` initialCategory: `{self._initialCategory}` id: `{self._id}` wxID: `{self._wxID}`'
