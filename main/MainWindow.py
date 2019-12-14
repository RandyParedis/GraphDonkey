from PyQt5 import QtWidgets, QtCore, QtGui, uic
from main.extra.IOHandler import IOHandler
from main.Highlighter import CodeEditor
from main.extra import Constants, Config
from graphviz import Source
import graphviz

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__(flags=QtCore.Qt.WindowFlags())
        uic.loadUi(IOHandler.dir_ui("MainWindow.ui"), self)
        self.scene = self.view.scene()
        if self.scene is None:
            self.scene = QtWidgets.QGraphicsScene(self.view)
            self.view.setScene(self.scene)

        self.restore()

        self.filename = ""
        self.saved = False
        self.updateTitle()

        self.editor = None
        self.setupEditor()

        # Set actions
        self.actionNew.triggered.connect(self.new)
        self.action_New.triggered.connect(self.new)
        self.actionOpen.triggered.connect(self.open)
        self.action_Open.triggered.connect(self.open)
        self.actionSave.triggered.connect(self.save)
        self.action_Save.triggered.connect(self.save)
        self.actionSave_As.triggered.connect(self.saveAs)
        self.actionRender.triggered.connect(self.displayGraph)
        self.action_Render.triggered.connect(self.displayGraph)

        self.actionAboutGraphviz.triggered.connect(self.aboutGraphviz)
        self.actionAboutQt.triggered.connect(self.aboutQt)

    def updateTitle(self):
        rest = "undefined"
        if self.filename != "":
            rest = self.filename
        if not self.saved:
            rest += " *"
        self.setWindowTitle(Constants.APP_NAME + " v" + Constants.APP_VERSION + " - " + rest)

    def setupEditor(self):
        if self.editor is None:
            font = QtGui.QFont()
            font.setFamily('Ubuntu Monospace')
            font.setFixedPitch(True)
            font.setPointSize(12)

            self.editor = CodeEditor(self)
            self.editor.setFont(font)
            self.graphvizData.layout().addWidget(self.editor)
        else:
            self.editor.clear()

        self.displayGraph()

    def aboutGraphviz(self):
        QtWidgets\
            .QMessageBox\
            .about(self,
                   "About Graphviz",
                   "Graphviz is open source graph visualization software. Graph visualization is a way of representing "
                   "structural information as diagrams of abstract graphs and networks. It has important applications "
                   "in networking, bioinformatics,  software engineering, database and web design, machine learning, "
                   "and in visual interfaces for other technical domains.\n\n"
                   "Current installed version is %s.\n\n"
                   "More information on www.graphviz.org" % graphviz.__version__)

    def aboutQt(self):
        QtWidgets.QMessageBox.aboutQt(self)

    def new(self):
        # TODO: confirmation if not saved
        self.setupEditor()
        self.filename = ""
        self.saved = False
        self.updateTitle()

    def open(self):
        # TODO: confirmation if not saved
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog\
            .getOpenFileName(self, "Open a Graphviz File", "", "All Files (*);;" + Config.file_list_open(),
                             options=options)
        if fileName:
            self.setupEditor()
            self.filename = fileName
            self.saved = True
            self.updateTitle()

            ext = fileName.split(".")[-1]
            if Config.valid_ext(ext, Config.FILE_TYPES_OPEN):
                with open(fileName, "r") as myfile:
                    data = "".join(myfile.readlines())
                    dot = Source(data, format=ext)
                    self.editor.setText(dot.source)

            self.displayGraph()

    def save(self):
        if self.filename == "":
            self.saveAs()
        else:
            ext = self.filename.split(".")[-1]
            dot = Source(self.editor.toPlainText())
            contents = dot.pipe(ext)
            with open(self.filename, 'bw') as myfile:
                myfile.write(contents)
            self.saved = True
            self.updateTitle()

    def saveAs(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, t = QtWidgets.QFileDialog\
            .getSaveFileName(self, "Save a Graphviz File", "", "All Files (*);;" + Config.file_list_save(),
                             options=options)
        if fileName:
            # TODO: confirmation box
            ext = fileName.split(".")[-1]
            rext = Config.obtain_ext(t)
            if len(fileName.split(".")) == 1:
                ext = "plain"
            if rext == "":
                rext = ext
            if ext is not rext:
                fileName += "." + rext
            if Config.valid_ext(rext, Config.FILE_TYPES_SAVE):
                self.filename = fileName
                self.save()


    def displayGraph(self):
        self.scene.clear()
        dot = Source(self.editor.toPlainText())
        bdata = dot.pipe('jpg')
        image = QtGui.QImage()
        image.loadFromData(bdata)
        pixmap = QtGui.QPixmap.fromImage(image)
        self.scene.addPixmap(pixmap)

    def restore(self):
        # Restore layout from memory iff needs be/possible
        settings = IOHandler.get_settings()
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))

    def closeEvent(self, event: QtGui.QCloseEvent):
        settings = IOHandler.get_settings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        QtWidgets.QMainWindow.closeEvent(self, event)
