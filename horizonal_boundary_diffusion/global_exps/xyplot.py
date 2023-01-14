from mom6_tools.m6plot import createXYlabels, myStats, boundaryStats, chooseColorMap, chooseColorLevels, \
                              createXYcoords, label
import matplotlib.pyplot as plt

def xyplot(field, x=None, y=None, area=None,
  xlabel=None, xunits=None, ylabel=None, yunits=None,
  title='', suptitle='',
  clim=None, colormap=None, extend=None, centerlabels=False,
  nbins=None, landcolor=[.5,.5,.5], axis=None, add_cbar=True,
  aspect=[16,9], resolution=576, sigma=2., annotate=True,
  ignore=None, save=None, debug=False, show=False, interactive=False, logscale=False):
  """
  Renders plot of scalar field, field(x,y).
  Arguments:
  field        Scalar 2D array to be plotted.
  x            x coordinate (1D or 2D array). If x is the same size as field then x is treated as
               the cell center coordinates.
  y            y coordinate (1D or 2D array). If x is the same size as field then y is treated as
               the cell center coordinates.
  area         2D array of cell areas (used for statistics). Default None.
  xlabel       The label for the x axis. Default 'Longitude'.
  xunits       The units for the x axis. Default 'degrees E'.
  ylabel       The label for the y axis. Default 'Latitude'.
  yunits       The units for the y axis. Default 'degrees N'.
  title        The title to place at the top of the panel. Default ''.
  suptitle     The super-title to place at the top of the figure. Default ''.
  clim         A tuple of (min,max) color range OR a list of contour levels. Default None.
  sigma         Sigma range for difference plot autocolori levels. Default is to span a 2. sigma range
  annotate     If True (default), annotates stats (mi, max, etc) in the plot.
  colormap     The name of the colormap to use. Default None.
  add_cbar     If true, the colorbar is added to the panel. Otherwise, the function will return the color
               scale object that be used to create a colorbar. Default is True.
  extend       Can be one of 'both', 'neither', 'max', 'min'. Default None.
  centerlabels If True, will move the colorbar labels to the middle of the interval. Default False.
  nbins        The number of colors levels (used is clim is missing or only specifies the color range).
  landcolor    An rgb tuple to use for the color of land (no data). Default [.5,.5,.5].
  aspect       The aspect ratio of the figure, given as a tuple (W,H). Default [16,9].
  resolution   The vertical resolution of the figure given in pixels. Default 720.
  axis         The axis handle to plot to. Default None.
  ignore       A value to use as no-data (NaN). Default None.
  save         Name of file to save figure in. Default None.
  debug        If true, report stuff for debugging. Default False.
  show         If true, causes the figure to appear on screen. Used for testing. Default False.
  interactive  If true, adds interactive features such as zoom, close and cursor. Default False.
  logscale     If true, use logaritmic coloring scheme. Default False.
  """

  # Create coordinates if not provided
  xlabel, xunits, ylabel, yunits = createXYlabels(x, y, xlabel, xunits, ylabel, yunits)
  if debug: print('x,y label/units=',xlabel,xunits,ylabel,yunits)
  xCoord, yCoord = createXYcoords(field, x, y)

  # Diagnose statistics
  if ignore is not None: maskedField = numpy.ma.masked_array(field, mask=[field==ignore])
  else: maskedField = field.copy()
  sMin, sMax, sMean, sStd, sRMS = myStats(maskedField, area, debug=debug)
  xLims = boundaryStats(xCoord)
  yLims = boundaryStats(yCoord)

  # Choose colormap
  if nbins is None and (clim is None or len(clim)==2): nbins=35
  if colormap is None: colormap = chooseColorMap(sMin, sMax)
  if clim is None and sStd is not None:
    cmap, norm, extend = chooseColorLevels(sMean-sigma*sStd, sMean+sigma*sStd, colormap, clim=clim, nbins=nbins, extend=extend, logscale=logscale)
  else:
    cmap, norm, extend = chooseColorLevels(sMin, sMax, colormap, clim=clim, nbins=nbins, extend=extend, logscale=logscale)

  if axis is None:
    setFigureSize(aspect, resolution, debug=debug)
    #plt.gcf().subplots_adjust(left=.08, right=.99, wspace=0, bottom=.09, top=.9, hspace=0)
    axis = plt.gca()
  cs = axis.pcolormesh(xCoord, yCoord, maskedField, cmap=cmap, norm=norm)
  if interactive: addStatusBar(xCoord, yCoord, maskedField)
  if add_cbar: cb = plt.colorbar(cs, ax=axis, fraction=.08, pad=0.02, extend=extend)
  if centerlabels and len(clim)>2: cb.set_ticks(  0.5*(clim[:-1]+clim[1:]) )
  elif clim is not None and len(clim)>2: cb.set_ticks( clim )
  axis.set_facecolor(landcolor)
  axis.set_xlim( xLims )
  axis.set_ylim( yLims )
  if annotate:
    #axis.annotate('max=%.5g\nmin=%.5g'%(sMax,sMin), xy=(0.0,1.01), xycoords='axes fraction', verticalalignment='bottom', fontsize=10)
    if area is not None:
      axis.annotate('mean=%.5g'%(sMean), xy=(0.0,1.01), xycoords='axes fraction', verticalalignment='bottom', fontsize=12)
      print('Min = {}, Max = {}'.format(sMin,sMax))
      #axis.annotate(' sd=%.5g\n'%(sStd), xy=(1.0,1.01), xycoords='axes fraction', verticalalignment='bottom', horizontalalignment='left', fontsize=10)

  if len(xlabel+xunits)>0: axis.set_xlabel(label(xlabel, xunits), fontsize=14)
  if len(ylabel+yunits)>0: axis.set_ylabel(label(ylabel, yunits), fontsize=14)
  if len(title)>0: axis.set_title(title)
  if len(suptitle)>0: plt.suptitle(suptitle)

  if save is not None: plt.savefig(save); plt.close()
  if interactive: addInteractiveCallbacks()
  if show: plt.show(block=False)
  if add_cbar:
    return
  else:
    return cs
