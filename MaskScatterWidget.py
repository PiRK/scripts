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
from silx.gui.plot import PlotWidget
from silx.gui.plot import PlotActions
from silx.gui.plot import PlotToolButtons

# TODO:
#   Mask
#   Colormap handling


class MaskScatterWidget(PlotWidget):
    """

    """
    # TODO sigMask
    def __init__(self, parent=None, backend=None):
        super(MaskScatterWidget, self).__init__(parent=parent, backend=backend)
        self._activeScatterLegend = "active scatter"
        self._bgImageLegend = "background image"
        #
        # self._maskToolsDockWidget = None

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

        self.colormapAction = self.group.addAction(PlotActions.ColormapAction(self))
        self.addAction(self.colormapAction)

        self.keepDataAspectRatioButton = PlotToolButtons.AspectToolButton(
            parent=self, plot=self)

        self.yAxisInvertedButton = PlotToolButtons.YAxisOriginToolButton(
            parent=self, plot=self)

        # self.group.addAction(self.getMaskAction())

        self._separator = qt.QAction('separator', self)
        self._separator.setSeparator(True)
        self.group.addAction(self._separator)

        self.copyAction = self.group.addAction(PlotActions.CopyAction(self))
        self.addAction(self.copyAction)

        self.saveAction = self.group.addAction(PlotActions.SaveAction(self))
        self.addAction(self.saveAction)

        self.printAction = self.group.addAction(PlotActions.PrintAction(self))
        self.addAction(self.printAction)

        # Creating the toolbar also create actions for toolbuttons
        self._toolbar = self._createToolBar(title='Plot', parent=None)
        self.addToolBar(self._toolbar)

        self.setActiveCurveHandling(False)   # avoids color change when selecting

    def setSelectionMask(self, mask, copy=True):
        """Set the mask to a new array.

        :param numpy.ndarray mask: The array to use for the mask.
                    Mask type: array of uint8 of dimension 1,
                    Array of other types are converted.
        :param bool copy: True (the default) to copy the array,
                          False to use it as is if possible.
        :return: None if failed, shape of mask as 1-tuple if successful.
        """
        #TODO
        pass
        # return self.getMaskToolsDockWidget().setSelectionMask(mask,
        #                                                       copy=copy)

    def getSelectionMask(self, copy=True):
        """Get the current mask as a 1D array.

        :param bool copy: True (default) to get a copy of the mask.
                          If False, the returned array MUST not be modified.
        :return: The array of the mask with dimension of the scatter data.
                 If there is no scatter data, an empty array is returned.
        :rtype: 1D numpy.ndarray of uint8
        """
        pass   # todo
        # return self.getMaskToolsDockWidget().getSelectionMask(copy=copy)

    def setBackgroundImage(self, image, xscale=(0, 1.), yscale=(0, 1.)):
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
                      z=0, replace=False)

    def getBackgroundImage(self):
        """Return the background image set with :meth:`setBackgroundImage`.

        :return: :class:`silx.gui.plot.items.Image` object
        """
        self.getImage(legend=self._bgImageLegend)

    def setScatter(self, x, y, v=None):
        """Set the scatter data, by providing its data as a 1D
        array or as a pixmap.

        :param x: 1D array of x coordinates
        :param y: 1D array of y coordinates
        :param v: Array of values for each point, represented as the color
             of the point on the plot.
        """
        self.addScatter(x, y, v, legend=self._activeScatterLegend)

    def getScatter(self):
        """Return the currently displayed scatter.

        :return: :class:`silx.gui.plot.items.Curve` object
        """
        return self.scatter  # FIXME: return an official plot Scatter object, when available

    # def getMaskAction(self):
    #     """QAction toggling image mask dock widget
    #
    #     :rtype: QAction
    #     """
    #     return self.getMaskToolsDockWidget().toggleViewAction()
    #
    # def getMaskToolsDockWidget(self):
    #     """DockWidget with image mask panel (lazy-loaded)."""
    #     if self._maskToolsDockWidget is None:
    #         self._maskToolsDockWidget = MaskToolsWidget.MaskToolsDockWidget(
    #             plot=self, name='Mask')
    #         self._maskToolsDockWidget.hide()
    #         self.addDockWidget(qt.Qt.BottomDockWidgetArea,
    #                            self._maskToolsDockWidget)
    #
    #     return self._maskToolsDockWidget

    def _createToolBar(self, title, parent):
        """Create a QToolBar from the QAction of the PlotWindow.

        :param str title: The title of the QMenu
        :param qt.QWidget parent: See :class:`QToolBar`
        """
        toolbar = qt.QToolBar(title, parent)

        # Order widgets with actions
        objects = self.group.actions()

        # Add push buttons to list
        index = objects.index(self.colormapAction)
        objects.insert(index + 1, self.keepDataAspectRatioButton)
        objects.insert(index + 2, self.yAxisInvertedButton)

        for obj in objects:
            if isinstance(obj, qt.QAction):
                toolbar.addAction(obj)
            else:
                # keep reference to toolbutton's action for changing visibility
                if obj is self.keepDataAspectRatioButton:
                    self.keepDataAspectRatioAction = toolbar.addWidget(obj)
                elif obj is self.yAxisInvertedButton:
                    self.yAxisInvertedAction = toolbar.addWidget(obj)
                else:
                    raise RuntimeError()

        # alpha_slider = ActiveImageAlphaSlider(parent=self, plot=self)
        # alpha_slider.setOrientation(qt.Qt.Horizontal)
        # toolbar.addWidget(alpha_slider)

        return toolbar

    def saveSession(self, uri=None, sessionFile=None, h5path="/"):
        """Save session data to an HDF5 file.

        Data saved:
         - background image (2D dataset) with xscale and yscale
         - scatter data (1D dataset)
         - mask (1D array)

        :param str uri: URI of group where to save data (e.g.
            /path/to/myfile.h5::/datapath).
        :param sessionFile: Name/path of output file, or h5py.File instance.
            This parameter and ``uri`` are mutually exclusive.
        :param str h5path: Path to output group relative to file root
            This parameter and ``uri`` are mutually exclusive.
        """
        pass   # TODO

    def loadSession(self, uri=None, sessionFile=None, h5path=""):
        """Load session from an HDF5 file.

        Data loaded:
         - background image (2D dataset) with xscale and yscale
         - image data (1D dataset)
         - mask (1D array)

        :param str uri: URI of group where to save data (e.g.
            /path/to/myfile.h5::/datapath).
        :param sessionFile: Name/path of session file, or h5py.File instance.
            This parameter and ``uri`` are mutually exclusive.
        :param str h5path: Path to output group relative to file root.
            This parameter and ``uri`` are mutually exclusive.
        """
        pass  # TODO


if __name__ == "__main__":
    app = qt.QApplication([])
    msw = MaskScatterWidget()

    bg_img = numpy.arange(200*150).reshape((200, 150))
    bg_img[75:125, 80:120] = 1000

    twopi = numpy.pi * 2
    x = 50 + 80 * numpy.linspace(0, twopi, num=100) / twopi * numpy.cos(numpy.linspace(0, twopi, num=100))
    y = 150 + 150 * numpy.linspace(0, twopi, num=100) / twopi * numpy.sin(numpy.linspace(0, twopi, num=100))

    v = numpy.arange(100)

    msw.setScatter(x, y, v=v)
    msw.setBackgroundImage(bg_img)
    msw.show()
    app.exec_()
