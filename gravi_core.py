#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 15:15:37 2019

@author: neuhauser
This is core function
"""

import numpy as np
import sys
import time
#from multiprocessing import Pool
#import os
import raster_io as io
from gravi_class import Cell


## Programm:        
def get_start_idx(release):
    row_list, col_list = np.where(release > 0)  # Gives back the indices of the release areas
    if len(row_list) > 0:
        altitude_list = []
        for i in range(len(row_list)):
            altitude_list.append(dem[row_list[i], col_list[i]])    
        altitude_list, row_list, col_list = list(zip(*sorted(zip(altitude_list, row_list, col_list), reverse=True)))  #Sort this lists by altitude
    return row_list, col_list   


def back_calculation(cell):
    back_list = []
    for parent in cell.parent:
        back_list.append(parent)
    for cell in back_list:
        for parent in cell.parent:
            back_list.append(parent)
    return back_list


def calculation(dem, release, forest, process):

    # Create needed arrays
    mass_array = np.zeros_like(dem)
    elh = np.zeros_like(dem)
    count_array = np.zeros_like(dem)

    row_list, col_list = get_start_idx(release)
    startcell_idx = 0
    while startcell_idx < len(row_list):
        sys.stdout.write(
            '\r' "Calculating Startcell: " + str(startcell_idx + 1) + " of " + str(len(row_list)) + " = " + str(
                round((startcell_idx + 1) / len(row_list) * 100, 2)) + "%" '\r')
        sys.stdout.flush()
        cell_list = []
        row_idx = row_list[startcell_idx]
        col_idx = col_list[startcell_idx]
        dem_ng = dem[row_idx - 1:row_idx + 2, col_idx - 1:col_idx + 2]  # neighbourhood DEM
        if (nodata in dem_ng) or np.size(dem_ng) < 9:
            startcell_idx += 1
            continue

        startcell = Cell(process, row_idx, col_idx, dem_ng, cellsize, 1, 0, forest[row_idx, col_idx], None, startcell=True)
        # If this is a startcell just give a Bool to startcell otherwise the object startcell

        cell_list.append(startcell)
        for cells in cell_list:
            row, col, mass, kin_e = cells.calc_distribution()
            if len(mass) > 0:
                # mass, row, col  = list(zip(*sorted(zip( mass, row, col), reverse=False)))
                kin_e, mass, row, col = list(zip(*sorted(zip(kin_e, mass, row, col), reverse=False)))
                # Sort this lists by elh to start from top to bottom

            for i in range(len(cell_list)):  # Check if Cell already exists
                k = 0
                while k < len(row):
                    if row[k] == cell_list[i].rowindex and col[k] == cell_list[i].colindex:
                        cell_list[i].add_mass(mass[k])
                        cell_list[i].add_parent(cells)
                        cell_list[i].kin_e = max(cell_list[i].kin_e, kin_e[k])
                        row = np.delete(row, k)
                        col = np.delete(col, k)
                        mass = np.delete(mass, k)
                        kin_e = np.delete(kin_e, k)
                    else:
                        k += 1

            for k in range(len(row)):
                dem_ng = dem[row[k] - 1:row[k] + 2, col[k] - 1:col[k] + 2]  # neighbourhood DEM
                if (nodata in dem_ng) or np.size(dem_ng) < 9:
                    continue
                cell_list.append(
                    Cell(process, row[k], col[k], dem_ng, cellsize, mass[k], kin_e[k], forest[row[k], col[k]], cells, startcell))

            elh[cells.rowindex, cells.colindex] = max(elh[cells.rowindex, cells.colindex], cells.kin_e)
            mass_array[cells.rowindex, cells.colindex] = max(mass_array[cells.rowindex, cells.colindex], cells.mass)
            count_array[cells.rowindex, cells.colindex] += 1

        release[elh > 0] = 0  # Check if i hited a release Cell, if so set it to zero and get again the indexes of release cells
        # ToDo: if i hit a startcell add this "mass"
        # ToDo: Backcalulation
        row_list, col_list = get_start_idx(release)
        startcell_idx += 1
    return elh, mass_array, count_array
        

   
#Reading in the arrays
# =============================================================================
# path = '/home/neuhauser/git_rep/graviclass/'
# dem_file = path + 'Fonnbu_dhm.asc'
# release_file = path + 'release.tif'
# infra_path = path + 'infra.tif'
# =============================================================================
# =============================================================================
# path = '/home/P/Projekte/18130-GreenRisk4Alps/Simulation/PAR3_Oberammergau/'
# dem_file = path + 'DEM_clipped_for_sim.tif'
# release_file = path + 'init/release_class1_clipped.tif'
# =============================================================================
path = '/home/P/Projekte/18130-GreenRisk4Alps/Simulation/PAR6_ValsGries_AUT/'
dem_file = path + 'dhm_10_6.tif'
release_file = path + 'init/release_rockfall_45deg.tif'
# =============================================================================
# path = 'example/'
# file = path + 'dhm.asc'
# release_file = path + 'release.asc'
# =============================================================================
# =============================================================================
# path = '/home/W/Neuhauser/Frei/Flow-Py/arzler_test/'
# dem_file = path + 'DHM/arzl10m_EPSG31287.tif'
# release_file = path + 'Release/release.tif'
# #infra_path = path + 'infra.tif'
# forest_file = path + 'Forest/Forest_value_v2.tif'
# =============================================================================
#infra_path = 'infra/infra_10_3.tif'
elh_out = path + 'energy_elhmax.tif' # V3 with dh dependend on energylinehight
mass_out = path + 'mass_elhmax.tif'
count_out = path + "cell_counts_elhmax.tif"
#index_out = path + 'index_flowr.asc'
# =============================================================================
# elh_out = path + 'energy_flowr_fonnbu.asc' # V3 with dh dependend on energylinehight
# mass_out = path + 'mass_flowr_fonnbu.asc'
# =============================================================================


dem, header = io.read_raster(dem_file)
cellsize = header["cellsize"]
nodata = header["noDataValue"]
release, header_release = io.read_raster(release_file) 
#infra, header = io.read_raster(infra_path) 
try:
    forest, header_forest = io.read_raster(forest_file)
except:
    forest = np.zeros_like(dem)


elh = np.zeros_like(dem)
mass_array = np.zeros_like(dem)
count_array = np.zeros_like(dem)
# index_array = np.zeros_like(dem)

start = time.time()
# Core

row_list, col_list = get_start_idx(release)
# =============================================================================
# for i in range(len(row_list)):
#     calc_list.append((row_list[i], col_list[i]))
# 
# 
# cpu_number = len(os.sched_getaffinity(0)) # counts number of cpu free.
# pool = Pool(processes=4)
# pool.map(calculation, calc_list)
# =============================================================================
startcell_idx = 0
process = 'Avalanche'
while startcell_idx < len(row_list):
    sys.stdout.write('\r' "Calculating Startcell: " + str(startcell_idx+1) + " of " + str(len(row_list)) + " = " + str(round((startcell_idx + 1)/len(row_list)*100,2)) + "%" '\r')
    sys.stdout.flush()
    cell_list = []
    row_idx = row_list[startcell_idx]
    col_idx = col_list[startcell_idx]    
    dem_ng = dem[row_idx - 1:row_idx + 2, col_idx - 1:col_idx + 2]  # neighbourhood DEM
    if (nodata in dem_ng) or np.size(dem_ng) < 9:
        startcell_idx += 1
        continue
    
    startcell = Cell(process, row_idx, col_idx, dem_ng, cellsize, 1, 0, forest[row_idx, col_idx], None, startcell=True)
    # If this is a startcell just give a Bool to startcell otherwise the object startcell
    
    cell_list.append(startcell)
    for cells in cell_list:
        row, col, mass, kin_e = cells.calc_distribution()
        if len(mass) > 0:
            # mass, row, col  = list(zip(*sorted(zip( mass, row, col), reverse=False)))
            kin_e, mass, row, col = list(zip(*sorted(zip(kin_e, mass, row, col), reverse=False)))
            # Sort this lists by mass to start the spreading from the middle

        for i in range(len(cell_list)):  # Check if Cell already exists
            k = 0
            while k < len(row):
                if row[k] == cell_list[i].rowindex and col[k] == cell_list[i].colindex:
                    cell_list[i].add_mass(mass[k])
                    cell_list[i].add_parent(cells)
                    cell_list[i].kin_e = max(cell_list[i].kin_e, kin_e[k]) 
                    row = np.delete(row, k)
                    col = np.delete(col, k)
                    mass = np.delete(mass, k)
                    kin_e = np.delete(kin_e, k)
                else:                                 
                    k += 1
         
        for k in range(len(row)):
            dem_ng = dem[row[k]-1:row[k]+2, col[k]-1:col[k]+2]  # neighbourhood DEM
            if (nodata in dem_ng) or np.size(dem_ng) < 9:
                continue
            cell_list.append(Cell(process, row[k], col[k], dem_ng, cellsize, mass[k], kin_e[k], forest[row[k], col[k]], cells, startcell))

        elh[cells.rowindex, cells.colindex] = max(elh[cells.rowindex, cells.colindex], cells.kin_e)
        mass_array[cells.rowindex, cells.colindex] = max(mass_array[cells.rowindex, cells.colindex], cells.mass)
        count_array[cells.rowindex, cells.colindex] += 1

    release[elh > 0] = 0  # Check if i hited a release Cell, if so set it to zero and get again the indexes of release cells
    #ToDo: if i hit a startcell add this "mass"
    #ToDo: Backcalulation
    row_list, col_list = get_start_idx(release)
    startcell_idx += 1

end = time.time()            
print('Time needed: ' + str(end - start) + ' seconds')

# Output
io.output_raster(dem_file, elh_out, elh)
io.output_raster(dem_file, mass_out, mass_array)
io.output_raster(dem_file, count_out, count_array)
    
