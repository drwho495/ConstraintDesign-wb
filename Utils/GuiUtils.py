from PySide import QtWidgets, QtCore, QtGui
import FreeCADGui as Gui
from Utils.Utils import getIDsFromSelection, getElementFromHash, getStringID
from Utils.Preferences import *
import copy

hashToElementSplitStr = "   "
missingStr = "(MISSING)"

class HoverableListWidget(QtWidgets.QListWidget):
    itemHovered = QtCore.Signal(str) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._last_hovered = None

    def mouseMoveEvent(self, event):
        item = self.itemAt(event.pos())
        if item and item != self._last_hovered:
            self._last_hovered = item
            self.itemHovered.emit(item.data(QtCore.Qt.UserRole))
        elif not item:
            self._last_hovered = None
        super().mouseMoveEvent(event)

class SelectorWidget(QtWidgets.QWidget):
    selectionChanged = QtCore.Signal(list)

    def __init__(self, addOldSelection=True, startSelection=[], container=None, sizeLimit=-1):
        super().__init__(None)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.preselected = ""
        self.sizeLimit = sizeLimit

        self.listWidget = HoverableListWidget()
        self.listWidget.setFixedHeight(125)
        self.listWidget.itemHovered.connect(self.onItemHovered)
        
        self.clearButton = QtWidgets.QPushButton("Clear All")
        self.layout.addWidget(self.listWidget)
        self.layout.addWidget(self.clearButton)
        self.hashList = []

        # selection box sizing
        self.minSize = 30
        self.YMargin = 3
        self.multipierSize = 26
        self.maxSize = 150
        self.selecting = True

        self.updateBoxSize()

        if container == None:
            self.activeContainer = Gui.ActiveDocument.ActiveView.getActiveObject("ConstraintDesign")
        else:
            self.activeContainer = container

        self.clearButton.clicked.connect(self.clear)
        
        if addOldSelection:
            self.addSelection(Gui.Selection.getCompleteSelection())
        else:
            Gui.Selection.clearSelection()

        if len(startSelection) != 0:
            self.addSelection(startSelection)

        # Gui.Selection.setSelectionStyle(Gui.Selection.SelectionStyle.GreedySelection)
        self._observer = SelectorWidgetObserver(self)
        self.destroyed.connect(self.cleanup)
    
    def toggleSelections(self, set):
        self.selecting = set
    
    def onItemHovered(self, entry):
        hashSplArray = entry.split(hashToElementSplitStr)
        hash = hashSplArray[0]

        if hashSplArray[1] == missingStr:
            Gui.Selection.clearSelection()
            self.preselected = ""
            return

        if self.activeContainer != None:
            element = getElementFromHash(self.activeContainer, hash)

            if element != None:
                self.preselected = hash
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection(self.activeContainer, f"{element[0].Name}.{element[1]}")
    
    def makeLambda(self, entry): 
        return lambda: self.removeItem(entry)

    def addSelection(self, selection):
        if not self.selecting: return

        if type(selection) != list:
            selection = [selection]
        
        if len(selection) != 0 and type(selection[0]) != str:
            stringIdSelection = getIDsFromSelection(selection, self.activeContainer)
        else:
            stringIdSelection = selection

        print(stringIdSelection)

        for i,sel in enumerate(stringIdSelection):
            if sel == self.preselected:
                continue

            element = getElementFromHash(self.activeContainer, sel)

            if element[0] != None and element[1] != None:
                Gui.Selection.removeSelection(self.activeContainer.Document.Name, self.activeContainer.Name, f'{element[0].Name}.{element[1]}')
                entry = f"{sel}{hashToElementSplitStr}({element[1]})"
            else:
                entry = f"{sel}{hashToElementSplitStr}{missingStr}"

            try:
                if self.sizeLimit != -1 and self.sizeLimit <= self.listWidget.count():
                    continue

                for i in range(self.listWidget.count()):
                    if self.listWidget.item(i).data(QtCore.Qt.UserRole) == entry:
                        return  # Already added
            except:
                pass

            item = QtWidgets.QListWidgetItem()
            item.setData(QtCore.Qt.UserRole, entry)

            widget = QtWidgets.QWidget()
            hbox = QtWidgets.QHBoxLayout(widget)
            hbox.setContentsMargins(5, self.YMargin, 5, self.YMargin)
            label = QtWidgets.QLabel(entry)

            remove_btn = QtWidgets.QToolButton()
            remove_btn.setText("X")
            remove_btn.setToolTip("Remove this item")
            remove_btn.setFixedSize(20, 20)
            remove_btn.setStyleSheet("""
            QToolButton {
                border: none;
                color: #d62828;
                margin-top: -8px;
                font-weight: bold;
                font-size: 14px;
                background: transparent;
            }
            QToolButton:hover {
                color: #a00000;
            }
            """)

            remove_btn.clicked.connect(self.makeLambda(entry))

            hbox.addWidget(label)
            hbox.addStretch()
            hbox.addWidget(remove_btn)

            initialLen = self.listWidget.count()

            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item, widget)

            if initialLen != self.listWidget.count():
                self.hashList.append(sel)

            item = None
            entry = None

        self.updateBoxSize()
        self.emitSelection()
    
    def updateBoxSize(self):
        size = self.listWidget.count() * self.multipierSize
        
        if size <= self.minSize:
            size = self.minSize

        if size >= self.maxSize:
            size = self.maxSize
        
        self.listWidget.setFixedHeight(size)
        
    def removeItem(self, entry):
        initialLen = self.listWidget.count()

        hash = entry.split(hashToElementSplitStr)[0]

        if hash == self.preselected:
            self.preselected = ""
            Gui.Selection.clearSelection()

        row = self.hashList.index(hash)
        self.listWidget.takeItem(row)

        if initialLen != self.listWidget.count():
            self.hashList.pop(row)

        self.updateBoxSize()
        self.emitSelection()

    def clear(self):
        self.listWidget.clear()
        self.hashList = []
        self.preselected = ""

        self.updateBoxSize()
        self.emitSelection()

    def getSelection(self):
        return self.hashList

    def emitSelection(self):
        self.selectionChanged.emit(self.getSelection())

    def cleanup(self):
        # Gui.Selection.setSelectionStyle(Gui.Selection.SelectionStyle.NormalSelection)
        self.listWidget.deleteLater()
        self.clearButton.deleteLater()

        self._observer.cleanup()


class SelectorWidgetObserver:
    def __init__(self, widget):
        self.widget = widget
        self.stop = False
        Gui.Selection.addObserver(self)
    
    def cleanup(self):
        Gui.Selection.removeObserver(self)

        self.stop = True

    def addSelection(self, _, _2, _3, _4):
        if self.stop:
            return

        if self.widget:
            self.widget.addSelection(Gui.Selection.getCompleteSelection())

    # def clearSelection(self, doc):
        # if self.widget:
            # self.widget.listWidget.clear()
            # self.widget.emitSelection()
