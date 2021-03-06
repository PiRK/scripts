# coding: utf-8
# /*##########################################################################
#
# Copyright (c) 2016-2017 European Synchrotron Radiation Facility
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
# ###########################################################################*/
"""
This module implements a widget to plot 2D data as an image, possibly
superimposed on another image (e.g. a picture of a sample), with mask
selection tools.

It is structured in three superposed layers:

- First (deepest) layer containing an optional picture (sample photo, ...)
- Second layer contains the detector data plotted with a transparent colormap
- Final layer contains the selection mask
"""

import numpy

from silx.gui import qt
from silx.gui import icons
from silx.gui.plot import PlotWidget
from silx.gui.plot import PlotActions
from silx.gui.plot import PlotToolButtons

from silx.gui.plot.AlphaSlider import NamedScatterAlphaSlider

from silx.gui.plot.ColormapDialog import ColormapDialog

from silx.gui.plot import ScatterMaskToolsWidget

from silx.io import is_file

try:
    import h5py
except ImportError:
    h5py = None


class ColormapToolButton(qt.QToolButton):
    def __init__(self, parent=None, plot=None):
        self._bg_dialog = None
        self._scatter_dialog = None
        super(ColormapToolButton, self).__init__(parent)
        self.plot = plot

        icon = icons.getQIcon('colormap')
        self.setIcon(icon)

        bgImageCmapAction = qt.QAction("Background image colormap",
                                       self)
        bgImageCmapAction.triggered.connect(self._setBgCmap)

        scatterCmapAction = qt.QAction("Scatter colormap", self)
        scatterCmapAction.triggered.connect(self._setScatterCmap)

        menu = qt.QMenu(self)
        menu.addAction(bgImageCmapAction)
        menu.addAction(scatterCmapAction)
        self.setMenu(menu)
        self.setPopupMode(qt.QToolButton.InstantPopup)

    def _setBgCmap(self):
        if self._bg_dialog is None:
            self._bg_dialog = ColormapDialog()

        image = self.plot.getBackgroundImage()
        if image is None:
            # No active image, set dialog from default info
            colormap = self.plot.getDefaultColormap()

            self._bg_dialog.setHistogram()  # Reset histogram and range if any

        else:
            # Set dialog from active image
            colormap = image.getColormap()

            data = image.getData(copy=False)

            goodData = data[numpy.isfinite(data)]
            if goodData.size > 0:
                dataMin = goodData.min()
                dataMax = goodData.max()
            else:
                qt.QMessageBox.warning(
                    self, "No Data",
                    "Image data does not contain any real value")
                dataMin, dataMax = 1., 10.

            self._bg_dialog.setHistogram()
            self._bg_dialog.setDataRange(dataMin, dataMax)

        self._bg_dialog.setColormap(**colormap)

        # Run the dialog listening to colormap change
        self._bg_dialog.sigColormapChanged.connect(self._bgColormapChanged)
        result = self._bg_dialog.exec_()
        self._bg_dialog.sigColormapChanged.disconnect(self._bgColormapChanged)

        if not result:  # Restore the previous colormap
            self._bgColormapChanged(colormap)

    def _bgColormapChanged(self, colormap):
        image = self.plot.getBackgroundImage()
        if image is not None:
            # Update image: This do not preserve pixmap
            self.plot.setBackgroundImage(image.getData(copy=False),
                                         colormap=colormap)

    def _setScatterCmap(self):
        if self._scatter_dialog is None:
            self._scatter_dialog = ColormapDialog()

        scatter = self.plot.getScatter()
        if scatter is None:
            # No active scatter, set dialog from default info
            colormap = self.plot.getDefaultColormap()

            self._scatter_dialog.setHistogram()  # Reset histogram and range if any

        else:
            # Set dialog from active scatter
            colormap = scatter.getColormap()

            data = scatter.getValueData(copy=False)

            goodData = data[numpy.isfinite(data)]
            if goodData.size > 0:
                dataMin = goodData.min()
                dataMax = goodData.max()
            else:
                qt.QMessageBox.warning(
                    self, "No Data",
                    "Image data does not contain any real value")
                dataMin, dataMax = 1., 10.

            self._scatter_dialog.setHistogram()
            self._scatter_dialog.setDataRange(dataMin, dataMax)
        self._scatter_dialog.setColormap(**colormap)

        # Run the dialog listening to colormap change
        self._scatter_dialog.sigColormapChanged.connect(self._scatterColormapChanged)
        result = self._scatter_dialog.exec_()
        self._scatter_dialog.sigColormapChanged.disconnect(self._scatterColormapChanged)

        if not result:  # Restore the previous colormap
            self._bgColormapChanged(colormap)

    def _scatterColormapChanged(self, colormap):
        scatter = self.plot.getScatter()
        if scatter is not None:
            self.plot.setScatter(scatter.getXData(copy=False),
                                 scatter.getYData(copy=False),
                                 scatter.getValueData(copy=False),
                                 info=scatter.getInfo(),
                                 colormap=colormap)


class MaskScatterWidget(PlotWidget):
    """

    """
    # TODO sigMask
    sigActiveScatterChanged = qt.Signal()
    """emitted when active scatter is removed, added, or set
    (:meth:`setScatter`)"""

    def __init__(self, parent=None, backend=None):
        super(MaskScatterWidget, self).__init__(parent=parent, backend=backend)
        self._activeScatterLegend = "active scatter"
        self._bgImageLegend = "background image"

        self._maskToolsDockWidget = None

        # Init actions
        self.group = qt.QActionGroup(self)
        self.group.setExclusive(False)

        self.resetZoomAction = self.group.addAction(PlotActions.ResetZoomAction(self))
        self.addAction(self.resetZoomAction)

        self.zoomInAction = PlotActions.ZoomInAction(self)
        self.addAction(self.zoomInAction)

        self.zoomOutAction = PlotActions.ZoomOutAction(self)
        self.addAction(self.zoomOutAction)

        self.xAxisAutoScaleAction = self.group.addAction(
            PlotActions.XAxisAutoScaleAction(self))
        self.addAction(self.xAxisAutoScaleAction)

        self.yAxisAutoScaleAction = self.group.addAction(
            PlotActions.YAxisAutoScaleAction(self))
        self.addAction(self.yAxisAutoScaleAction)

        self.colormapButton = ColormapToolButton(parent=self, plot=self)

        self.keepDataAspectRatioButton = PlotToolButtons.AspectToolButton(
            parent=self, plot=self)

        self.yAxisInvertedButton = PlotToolButtons.YAxisOriginToolButton(
            parent=self, plot=self)

        self.group.addAction(self.getMaskAction())

        self._separator = qt.QAction('separator', self)
        self._separator.setSeparator(True)
        self.group.addAction(self._separator)

        self.copyAction = self.group.addAction(PlotActions.CopyAction(self))
        self.addAction(self.copyAction)

        self.saveAction = self.group.addAction(PlotActions.SaveAction(self))
        self.addAction(self.saveAction)

        self.printAction = self.group.addAction(PlotActions.PrintAction(self))
        self.addAction(self.printAction)

        self.alphaSlider = NamedScatterAlphaSlider(parent=self, plot=self)
        self.alphaSlider.setOrientation(qt.Qt.Horizontal)

        # Creating the toolbar also create actions for toolbuttons
        self._toolbar = self._createToolBar(title='Plot', parent=None)
        self.addToolBar(self._toolbar)

        self.setActiveCurveHandling(False)   # avoids color change when selecting

        self.sigContentChanged.connect(self._onContentChanged)

    def _onContentChanged(self, action, kind, legend):
        if kind == "scatter" and legend == self._activeScatterLegend:
            self.sigActiveScatterChanged.emit()

    def setSelectionMask(self, mask, copy=True):
        """Set the mask to a new array.

        :param numpy.ndarray mask: The array to use for the mask.
                    Mask type: array of uint8 of dimension 1,
                    Array of other types are converted.
        :param bool copy: True (the default) to copy the array,
                          False to use it as is if possible.
        :return: None if failed, shape of mask as 1-tuple if successful.
        """
        return self.getMaskToolsDockWidget().setSelectionMask(mask,
                                                              copy=copy)

    def getSelectionMask(self, copy=True):
        """Get the current mask as a 1D array.

        :param bool copy: True (default) to get a copy of the mask.
                          If False, the returned array MUST not be modified.
        :return: The array of the mask with dimension of the scatter data.
                 If there is no scatter data, an empty array is returned.
        :rtype: 1D numpy.ndarray of uint8
        """
        return self.getMaskToolsDockWidget().getSelectionMask(copy=copy)

    def setBackgroundImage(self, image, xscale=(0, 1.), yscale=(0, 1.),
                           colormap=None):
        """

        :param image: 2D image, array of shape (nrows, ncolumns)
            or (nrows, ncolumns, 3) or (nrows, ncolumns, 4) RGB(A) pixmap
        :param xscale: Factors for polynomial scaling  for x-axis,
            *(a, b)* such as :math:`x \mapsto a + bx`
        :param yscale: Factors for polynomial scaling  for y-axis
        """
        self.addImage(image, legend=self._bgImageLegend,
                      origin=(xscale[0], yscale[0]),
                      scale=(xscale[1], yscale[1]),
                      z=0, replace=False,
                      colormap=colormap)

    def getBackgroundImage(self):
        """Return the background image set with :meth:`setBackgroundImage`.

        :return: :class:`silx.gui.plot.items.Image` object
        """
        return self.getImage(legend=self._bgImageLegend)

    def setScatter(self, x, y, v=None, info=None, colormap=None):
        """Set the scatter data, by providing its data as a 1D
        array or as a pixmap.

        :param x: 1D array of x coordinates
        :param y: 1D array of y coordinates
        :param v: Array of values for each point, represented as the color
             of the point on the plot.
        """
        self.addScatter(x, y, v, legend=self._activeScatterLegend,
                        info=info, colormap=colormap)

        self.alphaSlider.setLegend(self._activeScatterLegend)
        self.sigActiveScatterChanged.emit()

    def getScatter(self, legend=None):
        """Return the currently displayed scatter.

        :param legend: None (default value) to get the main scatter, or a
            specific legend to get another scatter.
        :return: :class:`silx.gui.plot.items.Scatter` object
        """
        if legend is None:
            return super(MaskScatterWidget, self).getScatter(
                    legend=self._activeScatterLegend)
        return super(MaskScatterWidget, self).getScatter(legend)

    def getMaskAction(self):
        """QAction toggling image mask dock widget

        :rtype: QAction
        """
        return self.getMaskToolsDockWidget().toggleViewAction()

    def getMaskToolsDockWidget(self):
        """DockWidget with image mask panel (lazy-loaded)."""
        if self._maskToolsDockWidget is None:
            self._maskToolsDockWidget = ScatterMaskToolsWidget.ScatterMaskToolsDockWidget(
                plot=self, name='Mask')
            self._maskToolsDockWidget.hide()
            self.addDockWidget(qt.Qt.BottomDockWidgetArea,
                               self._maskToolsDockWidget)

        return self._maskToolsDockWidget

    def _createToolBar(self, title, parent):
        """Create a QToolBar from the QAction of the PlotWindow.

        :param str title: The title of the QMenu
        :param qt.QWidget parent: See :class:`QToolBar`
        """
        toolbar = qt.QToolBar(title, parent)

        # Order widgets with actions
        objects = self.group.actions()

        # Add push buttons to list
        index = objects.index(self.yAxisAutoScaleAction)

        objects.insert(index + 1, self.colormapButton)
        objects.insert(index + 2, self.keepDataAspectRatioButton)
        objects.insert(index + 3, self.yAxisInvertedButton)

        for obj in objects:
            if isinstance(obj, qt.QAction):
                toolbar.addAction(obj)
            else:
                # keep reference to toolbutton's action for changing visibility
                if obj is self.colormapButton:
                    self.colormapAction = toolbar.addWidget(obj)
                elif obj is self.keepDataAspectRatioButton:
                    self.keepDataAspectRatioAction = toolbar.addWidget(obj)
                elif obj is self.yAxisInvertedButton:
                    self.yAxisInvertedAction = toolbar.addWidget(obj)
                elif obj is self.alphaSlider:
                    self.alphaSliderAction = toolbar.addWidget(obj)
                else:
                    raise RuntimeError()

        self.alphaSliderAction = toolbar.addWidget(self.alphaSlider)
        return toolbar

    def saveSession(self, path):
        """Save session data to an HDF5 file.

        Data saved:
         - background image (2D dataset) with xscale and yscale
         - scatter data: x, y, values (3 x 1D datasets)
         - mask (1D array)

        :param path: Name/path of output file.
        """
        if h5py is None:
            print("Error: h5py is required in order to save session")
            return

        bgImage = self.getBackgroundImage()
        scatter = self.getScatter()

        sessionFile = h5py.File(path, "w")

        sessionFile["background"] = bgImage.getData()
        sessionFile["background X scale"] = [
            bgImage.getOrigin()[0],
            bgImage.getScale()[0]]
        sessionFile["background Y scale"] = [
            bgImage.getOrigin()[1],
            bgImage.getScale()[1]]

        sessionFile["scatter x"] = scatter.getXData()
        sessionFile["scatter y"] = scatter.getYData()
        sessionFile["scatter values"] = scatter.getValueData()

        sessionFile["mask"] = self.getSelectionMask()
        sessionFile.close()

    def loadSession(self, path):
        """Load session from an HDF5 file.

        Data loaded:
         - background image (2D dataset) with xscale and yscale
         - scatter data: x, y, values (3 x 1D datasets)
         - mask (1D array)

        :param path: Name/path of session file
        """
        if not is_file(path):
            raise IOError("Cannot read %s as an HDF5 file")
        # todo: sanity tests

        sessionFile = h5py.File(path, "r")

        self.setBackgroundImage(sessionFile["background"],
                                xscale=sessionFile["background X scale"],
                                yscale=sessionFile["background Y scale"])

        self.setScatter(sessionFile["scatter x"],
                        sessionFile["scatter y"],
                        sessionFile["scatter values"])

        self.setSelectionMask(sessionFile["mask"])

        sessionFile.close()


if __name__ == "__main__":
    app = qt.QApplication([])
    msw = MaskScatterWidget()

    bg_img = numpy.arange(200*150).reshape((200, 150))
    bg_img[75:125, 80:120] = 1000

    twopi = numpy.pi * 2
    x = 50 + 80 * numpy.linspace(0, twopi, num=100) / twopi * numpy.cos(numpy.linspace(0, twopi, num=100))
    y = 150 + 150 * numpy.linspace(0, twopi, num=100) / twopi * numpy.sin(numpy.linspace(0, twopi, num=100))

    v = numpy.arange(100) / 3.14

    msw.setScatter(x, y, v=v)
    msw.setBackgroundImage(bg_img)
    msw.show()
    app.exec_()
