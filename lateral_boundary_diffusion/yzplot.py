from mom6_tools.m6plot import xycompare, xyplot, setFigureSize, chooseColorLevels, \
                       createYZlabels, myStats, yzWeight, boundaryStats, label

from mom6_tools.m6toolbox import section2quadmesh
import numpy as np
import matplotlib.pyplot as plt

def yzplot(field, y=None, z=None, ylabel=None, yunits=None, zlabel=None, zunits=None,
  splitscale=None, title='', suptitle='', clim=None, colormap=None, extend=None, centerlabels=False,
  nbins=None, landcolor=[.5,.5,.5], show_stats=2, aspect=[16,9], resolution=576, axis=None,
  ignore=None, debug=False, cbar=True):
      # Create coordinates if not provided
  ylabel, yunits, zlabel, zunits = createYZlabels(y, z, ylabel, yunits, zlabel, zunits)
  if debug: print('y,z label/units=',ylabel,yunits,zlabel,zunits)
  if len(y)==z.shape[-1]: y = expand(y)
  elif len(y)==z.shape[-1]+1: y = y
  else: raise Exception('Length of y coordinate should be equal or 1 longer than horizontal length of z')
  if ignore is not None: maskedField = np.ma.masked_array(field, mask=[field==ignore])
  else: maskedField = field.copy()
  yCoord, zCoord, field2 = section2quadmesh(y, z, maskedField)

  # Diagnose statistics
  sMin, sMax, sMean, sStd, sRMS = myStats(maskedField, yzWeight(y, z), debug=debug)
  yLims = np.amin(yCoord), np.amax(yCoord)
  zLims = boundaryStats(zCoord)

  # Choose colormap
  if nbins is None and (clim is None or len(clim)==2): nbins=35
  if colormap is None: colormap = chooseColorMap(sMin, sMax)
  cmap, norm, extend = chooseColorLevels(sMin, sMax, colormap, clim=clim, nbins=nbins, extend=extend)

  if axis is None:
    setFigureSize(aspect, resolution, debug=debug)
    axis = plt.gca()

  cs = axis.pcolormesh(yCoord, zCoord, field2, cmap=cmap, norm=norm)
  if cbar:
    cb = plt.colorbar(cs,ax=axis, fraction=.08, pad=0.02, extend=extend)
  if centerlabels and len(clim)>2: cb.set_ticks(  0.5*(clim[:-1]+clim[1:]) )
  axis.set_facecolor(landcolor)
  if splitscale is not None:
    for zzz in splitscale[1:-1]: axis.axhline(zzz,color='k',linestyle='--')
    axis.set_yscale('splitscale', zval=splitscale)
  axis.set_xlim( yLims ); axis.set_ylim( zLims )
  if show_stats > 0:
    axis.annotate('max=%.5g\nmin=%.5g'%(sMax,sMin), xy=(0.0,1.01), xycoords='axes fraction', verticalalignment='bottom', fontsize=10)
    if show_stats > 1:
      if sMean is not None:
        axis.annotate('mean=%.5g\nrms=%.5g'%(sMean,sRMS), xy=(1.0,1.01), xycoords='axes fraction', verticalalignment='bottom', horizontalalignment='right', fontsize=10)
        axis.annotate(' sd=%.5g\n'%(sStd), xy=(1.0,1.01), xycoords='axes fraction', verticalalignment='bottom', horizontalalignment='left', fontsize=10)

  if len(ylabel+yunits)>0: axis.set_xlabel(label(ylabel, yunits))
  if len(zlabel+zunits)>0: axis.set_ylabel(label(zlabel, zunits))
  if len(title)>0: axis.set_title(title)
  if len(suptitle)>0: plt.suptitle(suptitle)
  return cs
