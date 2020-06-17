
from typing import Dict
from typing import List
from typing import cast

from logging import Logger
from logging import getLogger

from antlr4 import ParserRuleContext

from org.pyut.plugins.iopythonsupport.pyantlrparser.Python3Parser import Python3Parser
from org.pyut.plugins.iopythonsupport.pyantlrparser.Python3Visitor import Python3Visitor


class PyutPythonVisitor(Python3Visitor):

    PYTHON_SELF:        str = 'self'
    PYTHON_SELF_COMMA:  str = f'{PYTHON_SELF},'
    FIELD_IDENTIFIER:   str = f'{PYTHON_SELF}.'
    PYTHON_CONSTRUCTOR: str = '__init__'

    MethodName          = str
    ClassName           = str
    ParentName          = str
    ChildName           = str
    MultiParameterNames = str                # comma separated parameter names
    Field               = str

    MethodCode     = List[str]
    MethodNames    = List[MethodName]
    ParameterNames = List[MultiParameterNames]
    Fields         = List[Field]
    Children       = List[ChildName]

    Methods    = Dict[ClassName, MethodNames]
    Parameters = Dict[MethodName, ParameterNames]
    MethodCode = Dict[MethodName, MethodCode]
    Parents    = Dict[ParentName, Children]

    def __init__(self):

        self.logger: Logger = getLogger(__name__)

        self.classMethods: PyutPythonVisitor.Methods    = {}
        self.parameters:   PyutPythonVisitor.Parameters = {}
        self.methodCode:   PyutPythonVisitor.MethodCode = {}
        self.fields:       PyutPythonVisitor.Fields     = []
        self.parents:      PyutPythonVisitor.Parents    = {}

    def visitFuncdef(self, ctx: Python3Parser.FuncdefContext):

        className = self._checkIfMethodBelongsToClass(ctx, Python3Parser.ClassdefContext)
        if className:
            methodName = ctx.getChild(1).getText()
            self.logger.debug(f'visitFuncdef: methodName: {methodName}')
            if className not in self.classMethods:
                self.classMethods[className] = [methodName]
            else:
                self.classMethods[className].append(methodName)

            self.__getMethodCode(methodName, ctx)

        return super().visitChildren(ctx)

    def visitClassdef(self, ctx: Python3Parser.ClassdefContext):

        className: str = ctx.getChild(1).getText()
        self.logger.info(f'visitClassdef: Visited class: {className}')

        argListCtx: Python3Parser.ArglistContext = self._findArgListContext(ctx)
        if argListCtx is not None:
            self._createParentChildEntry(argListCtx, className)

        return super().visitClassdef(ctx)

    def visitParameters(self, ctx: Python3Parser.ParametersContext):

        if len(ctx.children) > 1:
            parameterNames: PyutPythonVisitor.MultiParameterNames = ctx.getChild(1).getText()
            methodName:     PyutPythonVisitor.MethodName          = self._getParametersMethodName(ctx.parentCtx)
            self.logger.debug(f'visitParameters: parameterNames: {parameterNames} in method {methodName}')

            if parameterNames != PyutPythonVisitor.PYTHON_SELF:
                strippedParameterNames: PyutPythonVisitor.MultiParameterNames = parameterNames.replace(PyutPythonVisitor.PYTHON_SELF_COMMA, "")
                if strippedParameterNames not in self.parameters:
                    self.parameters[methodName] = [strippedParameterNames]
                else:
                    self.parameters[methodName].append(strippedParameterNames)

        return super().visitChildren(ctx)

    def visitExpr_stmt(self, ctx: Python3Parser.Expr_stmtContext):

        exprText: str = ctx.getText()

        if exprText.startswith(PyutPythonVisitor.FIELD_IDENTIFIER) is True:
            areWeAField: bool = self.__isThisInitMethod(ctx)
            if areWeAField is True:
                self.logger.info(f'Field expression: {exprText}')
                self.fields.append(exprText.replace(PyutPythonVisitor.FIELD_IDENTIFIER, ''))

        return super().visitChildren(ctx)

    def _checkIfMethodBelongsToClass(self, node: Python3Parser.FuncdefContext, classType):

        while node.parentCtx:
            if isinstance(node, classType):
                return node.getChild(1).getText()
            node = node.parentCtx
        return None

    def _getParametersMethodName(self, parentCtx: Python3Parser.FuncdefContext) -> MethodName:

        methodName: PyutPythonVisitor.MethodName = parentCtx.getChild(1).getText()
        return methodName

    def _createParentChildEntry(self, parentCtx: Python3Parser.ArglistContext, childName: str):

        parentName: str = parentCtx.getText()
        self.logger.info(f'Class: {childName} is subclass of {parentName}')

        if parentName in self.parents:
            children: PyutPythonVisitor.Children = self.parents[parentName]
            children.append(childName)
        else:
            children: PyutPythonVisitor.Children = [childName]

        self.parents[parentName] = children

    def __getMethodCode(self, methodName: MethodName, ctx: Python3Parser.FuncdefContext):

        methodText:     str       = ctx.getText()
        splitText:      List[str] = methodText.split('\n')
        justMethodCode: List[str] = splitText[1:len(splitText)]

        self.logger.debug(f'justMethodCode: {justMethodCode}')

        self.methodCode[methodName] = justMethodCode

    def _findArgListContext(self, ctx: Python3Parser.ClassdefContext) -> Python3Parser.ArglistContext:

        argListCtx: Python3Parser.ArglistContext = cast(Python3Parser.ArglistContext, None)
        for childCtx in ctx.children:
            if isinstance(childCtx, Python3Parser.ArglistContext):
                argListCtx = childCtx
                break

        return argListCtx

    def __isThisInitMethod(self, ctx: Python3Parser.Expr_stmtContext) -> bool:

        ans: bool = False

        methodCtx: Python3Parser.FuncdefContext = self.__findMethodContext(ctx)
        if methodCtx is not None:
            methodName: str = methodCtx.getChild(1).getText()
            if methodName == PyutPythonVisitor.PYTHON_CONSTRUCTOR:
                ans = True

        return ans

    def __findMethodContext(self, ctx: Python3Parser.Expr_stmtContext) -> Python3Parser.FuncdefContext:

        currentCtx: ParserRuleContext = ctx

        while isinstance(currentCtx, Python3Parser.FuncdefContext) is False:
            currentCtx = currentCtx.parentCtx
            if currentCtx is None:
                break

        if currentCtx is not None:
            self.logger.info(f'Found method: {currentCtx.getChild(1).getText()}')

        return cast(Python3Parser.FuncdefContext, currentCtx)