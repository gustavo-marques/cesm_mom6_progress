#!/usr/bin/env python

import io, yaml, os
import matplotlib.pyplot as plt
import numpy as np
import warnings, dask
from datetime import datetime, date
import xarray as xr
from mom6_tools.DiagsCase import DiagsCase
from ncar_jobqueue import NCARCluster
from dask.distributed import Client
from mom6_tools import m6plot
from mom6_tools  import m6toolbox
from mom6_tools.MOM6grid import MOM6grid

def options():
  try: import argparse
  except: raise Exception('This version of python is not new enough. python 2.7 or newer is required.')
  parser = argparse.ArgumentParser(description='''Script for plotting meridional overturning circulation.''')
  parser.add_argument('diag_config_yml_path', type=str, help='''Full path to the yaml file  \
    describing the run and diagnostics to be performed.''')
  #parser.add_argument('-v', '--var', nargs='+', default=['vmo'],
  #                   help='''Variable to be processed (default=['vmo'])''')
  parser.add_argument('-sd','--start_date', type=str, default='',
                      help='''Start year to compute averages. Default is to use value set in diag_config_yml_path''')
  parser.add_argument('-ed','--end_date', type=str, default='',
                      help='''End year to compute averages. Default is to use value set in diag_config_yml_path''')
  parser.add_argument('-fname','--file_name', type=str, default='.mom6.hm_*.nc',  help='''File(s) where vmo should be read. Default .mom6.hm_*.nc''')
  parser.add_argument('-nw','--number_of_workers',  type=int, default=2,
                      help='''Number of workers to use (default=2).''')
  parser.add_argument('-debug',   help='''Add priting statements for debugging purposes''',
                      action="store_true")
  cmdLineArgs = parser.parse_args()
  return cmdLineArgs
  main(cmdLineArgs)

def main():
  # Get options
  args = options()

  nw = args.number_of_workers
  if not os.path.isdir('ncfiles'):
    print('Creating a directory to place figures (ncfiles)... \n')
    os.system('mkdir ncfiles')

  # Read in the yaml file
  diag_config_yml = yaml.load(open(args.diag_config_yml_path,'r'), Loader=yaml.Loader)

  # Create the case instance
  dcase = DiagsCase(diag_config_yml['Case'])
  args.case_name = dcase.casename
  RUNDIR = dcase.get_value('RUNDIR')
  print('Run directory is:', RUNDIR)
  print('Casename is:', dcase.casename)
  print('Number of workers to be used:', nw)

  # set avg dates
  avg = diag_config_yml['Avg']
  if not args.start_date : args.start_date = avg['start_date']
  if not args.end_date : args.end_date = avg['end_date']

  # read grid info
  grd = MOM6grid(RUNDIR+'/'+dcase.casename+'.mom6.static.nc')
  depth = grd.depth_ocean
  # remote Nan's, otherwise genBasinMasks won't work
  depth[np.isnan(depth)] = 0.0
  basin_code = m6toolbox.genBasinMasks(grd.geolon, grd.geolat, depth)

  parallel, cluster, client = m6toolbox.request_workers(nw)

  print('Reading {} dataset...'.format(args.file_name))
  startTime = datetime.now()
  # load data
  def preprocess(ds):
    variables = ['diftrblo', 'difmxylo' ,'difmxybo', 'diftrelo']
    for v in variables:
      if v not in ds.variables:
        ds[v] = xr.zeros_like(ds.vo)
    return ds[variables]

  ds = xr.open_mfdataset(RUNDIR+'/'+dcase.casename+args.file_name,
  parallel=True,
  combine="nested", # concatenate in order of files
  concat_dim="time", # concatenate along time
  preprocess=preprocess,
  ).chunk({"time": 12})


  print('Time elasped: ', datetime.now() - startTime)
  # compute yearly means first
  print('Computing yearly means...')
  startTime = datetime.now()
  ds_yr = ds.resample(time="1Y", closed='left').mean('time')
  print('Time elasped: ', datetime.now() - startTime)

  print('Selecting data between {} and {}...'.format(args.start_date, args.end_date))
  startTime = datetime.now()
  ds_sel = ds_yr.sel(time=slice(args.start_date, args.end_date))
  print('Time elasped: ', datetime.now() - startTime)

  print('Computing time mean...')
  startTime = datetime.now()
  ds_mean = ds_sel.mean('time').compute()
  print('Time elasped: ', datetime.now() - startTime)

  attrs = {'description': 'Time-mean mixing coefficients', 'units': 'm^2/s', 'start_date': avg['start_date'],
       'end_date': avg['end_date'], 'casename': dcase.casename}
  m6toolbox.add_global_attrs(ds_mean,attrs)

  print('Saving netCDF files...')
  ds_mean.to_netcdf('ncfiles/'+str(args.case_name)+'_avg_mixing_coeffs.nc')

  print('Releasing workers ...')
  client.close(); cluster.close()

  return

if __name__ == '__main__':
  main()
