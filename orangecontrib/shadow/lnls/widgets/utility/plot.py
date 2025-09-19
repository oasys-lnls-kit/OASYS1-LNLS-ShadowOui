#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar 21 11:42:34 2020

@author: sergio.lordano
"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import LogNorm
from optlnls.math import get_fwhm, calc_rms, zero_padding
from optlnls.fitting import gauss_function, lorentz_function, lorentz_gauss_function, pseudo_voigt_asymmetric
from optlnls.fitting import fit_gauss, fit_lorentz, fit_lorentz_gauss, fit_pseudo_voigt_asymmetric
from scipy.signal import savgol_filter

def find_peak(xz):
    zmax = [0, 0]; xmax = [0, 0]

    for i in range(len(xz[:,0])):
        for j in range(len(xz[0,:])):
            
            if(xz[i,j] > zmax[1]):
                zmax[0] = j
                zmax[1] = xz[i,j]
                                
            if(xz[i,j] > xmax[1]):
                xmax[0] = i
                xmax[1] = xz[i,j]
                
    return xmax, zmax


def beam_integral(mtx):
    px = ((mtx[0, -1] - mtx[0, 1]) / (len(mtx[0,1:]) - 1))
    py = ((mtx[-1, 0] - mtx[1, 0]) / (len(mtx[1:,0]) - 1))
    return np.sum(mtx[1:,1:])*px*py

def plot_beam(beam2D, show_plot=True, outfilename='', outfileext='png', cut=0, textA=0, textB=0, textC=0, textD=0, fitType=0, 
                     overSampling=200.0, fwhm_zeroPadding=0, unitFactor=1e3, xlabel='X', ylabel='Y', zlabel='', units=2, plot_title='', 
                     invertXY=False, scale=0, fwhm_threshold=0.5, fwhm_int_ext=1, show_colorbar=0, z_min_factor=0,
                     x_cut_pos=0.0, y_cut_pos=0.0, x_range = 0, y_range = 0, cmap='jet', grid=1, integral=0, peak_density=0,
                     x_range_min=-0.25, x_range_max=0.25, y_range_min=-0.25, y_range_max=0.25, z_range_min=float('NaN'), z_range_max=float('NaN'),
                     zero_pad_x=0, zero_pad_y=0, export_slices=0, isdensity=1, savgol=[11,4],
                     figure=None, ax2D=None, axX=None, axY=None, axT=None):
    """
    

    Parameters
    ----------
    beam2D : 2D array
        2D numpy array where first row is x coordinates, first column
        is y coordinates, [0,0] is not used, and [1:1:] is the z axis.
    plotting : boolean, optional
        Show plot. The default is True.
    outfilename : str, optional
        file path to save output plot. The default is ''.
    outfileext : str, optional
        extension of the output file. The default is 'png'.
    cut : int, optional
        Type of x,y slice to show. 
        0: integrated 
        1: cut at (0,0) 
        2: cut at peak value
        3: cut at mean value
        4: cut at custom position given by x_cut_pos and y_cut_pos
        The default is 0.
    textA : int, optional
        Option of text to show in plot. 
        1: Text from plot_title
        2: Mean value
        3: Peak position
        4: Window range
        5: FWHM
        6: RMS
        7: Peak value
        8: Fit mean value
        9: Fit peak position
        10: Fit FWHM
        11: Fit RMS
        12: Fit peak value
        13: Integral
        The default is 0.
    textB : int, optional
        Option of text to show in plot. as in textA. The default is 0.
    textC : int, optional
        Option of text to show in plot. as in textA. The default is 0.
    textD : int, optional
        Option of text to show in plot. as in textA. The default is 0.
    fitType : int, optional
        Fit the slices. 
        1: Gauss
        2: Lorentz
        3: Gauss-Lorentz      
        4: Savitzky-Golay filter
        5: Pseudo Voigt Asymmetric
        The default is 0 (don't fit).
    overSampling : float, optional
        multiplication factor for slice number of points for FWHM. The default is 200.0.
    unitFactor : float, optional
        multiplication factor for changing units. The default is 1e3.
    xlabel : str, optional
        horizontal axis label. The default is 'X'.
    ylabel : str, optional
        vertical axis label. The default is 'Z'.
    units : int or str, optional
        Option for unit factor and label.
        1: mm
        2: um
        3: nm
        str: sets unitLabel 
        The default is 2.
    plot_title : str, optional
        DESCRIPTION. The default is ''.
    invertXY : boolean, optional
        DESCRIPTION. The default is False.
    scale : str, optional
        DESCRIPTION. The default is 0.
    fwhm_threshold : float, optional
        DESCRIPTION. The default is 0.5.
    fwhm_int_ext : int, optional
        DESCRIPTION. The default is 0.
    show_colorbar : boolean, optional
        DESCRIPTION. The default is 0.
    z_min_factor : float, optional
        change z minimum, e.g. for log plots. The default is 0.
    x_cut_pos : float, optional
        DESCRIPTION. The default is 0.0.
    y_cut_pos : float, optional
        DESCRIPTION. The default is 0.0.
    x_range : int, optional
        DESCRIPTION. The default is 0.
    y_range : int, optional
        DESCRIPTION. The default is 0.
    cmap : str, optional
        DESCRIPTION. The default is 'jet'.
    grid : int, optional
        DESCRIPTION. The default is 1.
    integral : float, optional
        DESCRIPTION. The default is 0.
    peak_density : float, optional
        For normalization. The default is 0.
    x_range_min : float, optional
        DESCRIPTION. The default is -0.25.
    x_range_max : float, optional
        DESCRIPTION. The default is 0.25.
    y_range_min : float, optional
        DESCRIPTION. The default is -0.25.
    y_range_max : float, optional
        DESCRIPTION. The default is 0.25.
    zero_pad_x : int, optional
        DESCRIPTION. Zero padding in x direction. The default is 0.
    zero_pad_z : int, optional
        DESCRIPTION. Zero padding in z direction. The default is 0.
    figure: matplotlib.figure.Figure, optional
        DESCRIPTION. The default is None.
    ax2D: matplotlib.axes.Axes, optional
        DESCRIPTION. The default is None.
    axX: matplotlib.axes.Axes, optional
        DESCRIPTION. The default is None.
    axY: matplotlib.axes.Axes, optional
        DESCRIPTION. The default is None.
    axT: matplotlib.axes.Axes, optional
        DESCRIPTION. The default is None.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """

    # HANDLE UNITS
    if(units == 0): # [mm]
        unitFactor = 1
        unitLabel = 'mm'
        
    elif(units == 1): # [um]
        unitFactor = 1e3
        unitLabel = '$\mu$m'
        
    elif(units == 2): # [nm]
        unitFactor = 1e6
        unitLabel = 'nm'
        
    else:
        unitLabel = units # units is a string in this case
    
    if(zero_pad_x != 0 or zero_pad_y != 0 ):
        beam2D = zero_padding(beam2D, zero_pad_x, zero_pad_y)
    
    # TRADE X and Y axes if needed
    if(invertXY):        
        z_axis = beam2D[0,1:]*unitFactor
        x_axis = beam2D[1:,0]*unitFactor
        xz = np.array(beam2D[1:,1:]).transpose()
            
    else:       
        z_axis = beam2D[1:,0]*unitFactor
        x_axis = beam2D[0,1:]*unitFactor
        xz = np.array(beam2D[1:,1:])
        
    if(isdensity):
        xz = xz / unitFactor**2

    # NORMALIZE TO PEAK DENSITY
    if(peak_density < 0):
        xz = xz / np.max(xz)

    elif(peak_density > 0):
        xz = xz / peak_density

    
    # NORMALIZE TO INTEGRAL 
    if(integral > 0.0):
        #arbitrary_units_integral = numpy.sum(xz) * (x_axis[int(len(x_axis)/2 + 1)]-x_axis[int(len(x_axis)/2)]) * (z_axis[int(len(z_axis)/2 + 1)]-z_axis[int(len(z_axis)/2)])
        arbitrary_units_integral = beam_integral(beam2D)
        xz = xz / arbitrary_units_integral # probability density function (integral equal to 1)
        xz = xz * integral # distribution in physical units [unit = unit[integral] / (unit[x_azis] * unit[z_axis])] 
    else:   
        integral = beam_integral(beam2D)    
        
    xz_max = np.max(xz)
    xz_min = np.min(xz)
    
    
    x_cut_coord = 0.0
    z_cut_coord = 0.0
   
    # FIND MEAN VALUE
    z_int = np.array([np.sum(xz[i,1:]) for i in range(len(z_axis))])
    x_int = np.array([np.sum(xz[1:,j]) for j in range(len(x_axis))])
    z_mean = np.average(z_axis, weights=z_int)
    x_mean = np.average(x_axis, weights=x_int)
    
    # FIND PEAK VALUES
    xmax, zmax = [[0, 0], [0, 0]]
    
    # CHANGE MINIMUM VALUE IF NEEDED (e.g. z_min_factor=1e-5 for log plots)
    if(z_min_factor != 0):
        xz[xz < z_min_factor * xz_max] = z_min_factor * xz_max 
        
        xz_max = np.max(xz)
        xz_min = np.min(xz)
    
    
    if(cut==0): # PLOT INTEGRATED DISTRIBUTION
        z_cut = np.array([np.sum(xz[i,1:]) for i in range(len(z_axis))])*(x_axis[int(len(x_axis)/2 + 1)]-x_axis[int(len(x_axis)/2)])
        x_cut = np.array([np.sum(xz[1:,j]) for j in range(len(x_axis))])*(z_axis[int(len(z_axis)/2 + 1)]-z_axis[int(len(z_axis)/2)])
        
    elif(cut==1): # PLOT CUT AT ZERO
        z_cut = xz[:, np.abs(x_axis).argmin()]
        x_cut = xz[np.abs(z_axis).argmin(), :]
    
    elif(cut==2): # PLOT CUT AT PEAK
        xmax, zmax = find_peak(xz)
        x_cut_coord = x_axis[zmax[0]]
        z_cut_coord = z_axis[xmax[0]]
        z_cut = xz[:, zmax[0]]
        x_cut = xz[xmax[0], :]

    elif(cut==3): # PLOT CUT AT MEAN VALUE OF INTEGRATED DISTRIBUTION
        x_cut_coord = x_axis[np.abs(x_axis-x_mean).argmin()]
        z_cut_coord = z_axis[np.abs(z_axis-z_mean).argmin()]
        z_cut = xz[:, np.abs(x_axis-x_mean).argmin()]
        x_cut = xz[np.abs(z_axis-z_mean).argmin(), :]
        
    elif(cut==4): # PLOT CUT AT CUSTOM VALUES
        x_cut_coord = x_axis[np.abs(x_axis-x_cut_pos).argmin()]
        z_cut_coord = z_axis[np.abs(z_axis-y_cut_pos).argmin()]
        z_cut = xz[:, np.abs(x_axis-x_cut_pos).argmin()]
        x_cut = xz[np.abs(z_axis-y_cut_pos).argmin(), :]
        pass
    

    offsetFactorX = 1.0
    
    if np.log10(x_cut.max()) > 3:
        expoX = int(np.floor(np.log10(x_cut.max())))
        offsetFactorX = 10**expoX
        x_cut = x_cut/offsetFactorX

    offsetFactorZ = 1.0
 
    if np.log10(z_cut.max()) > 3:
        expoZ = int(np.floor(np.log10(z_cut.max())))
        offsetFactorZ = 10**expoZ
        z_cut = z_cut/offsetFactorZ

    x_cut_max = np.max(x_cut)
    x_cut_min = np.min(x_cut)
    z_cut_max = np.max(z_cut)    
    z_cut_min = np.min(z_cut)
    

    z_cut_rms = calc_rms(z_axis, z_cut)
    x_cut_rms = calc_rms(x_axis, x_cut)
    
    z_cut_fwhm = get_fwhm(z_axis, z_cut, oversampling=overSampling, zero_padding=zero_padding, avg_correction=False, threshold=fwhm_threshold, inmost_outmost=fwhm_int_ext)
    x_cut_fwhm = get_fwhm(x_axis, x_cut, oversampling=overSampling, zero_padding=zero_padding, avg_correction=False, threshold=fwhm_threshold, inmost_outmost=fwhm_int_ext)
    
        # ==================================================================== #
    # === FITTING DISTRIBUTIONS ========================================== #
    # ==================================================================== #
    
    if(fitType != 0):
        
        if(fitType==1):

            popt_z_cut, perr_z_cut = fit_gauss(z_axis, z_cut, [z_cut_max, z_mean, z_cut_rms], 10000)
            z_cut_fit = gauss_function(z_axis, popt_z_cut[0], popt_z_cut[1], popt_z_cut[2])
                    
            popt_x_cut, perr_x_cut = fit_gauss(x_axis, x_cut, [x_cut_max, x_mean, x_cut_rms], 10000)
            x_cut_fit = gauss_function(x_axis, popt_x_cut[0], popt_x_cut[1], popt_x_cut[2])
            
        elif(fitType==2):

            poptl_z_cut, perrl_z_cut = fit_lorentz(z_axis, z_cut, [z_cut_max, z_mean, z_cut_rms], 10000)
            z_cut_fit = lorentz_function(z_axis, poptl_z_cut[0], poptl_z_cut[1], poptl_z_cut[2])
            
            poptl_x_cut, perrl_x_cut = fit_lorentz(x_axis, x_cut, [x_cut_max, x_mean, x_cut_rms], 10000)
            x_cut_fit = lorentz_function(x_axis, poptl_x_cut[0], poptl_x_cut[1], poptl_x_cut[2])

        elif(fitType==3):

            poptlg_z_cut, perrlg_z_cut = fit_lorentz_gauss(z_axis, z_cut, [z_mean, z_cut_max, z_cut_rms, z_cut_max, z_cut_rms], 10000)
            z_cut_fit = lorentz_gauss_function(z_axis, poptlg_z_cut[0], poptlg_z_cut[1], poptlg_z_cut[2], poptlg_z_cut[3], poptlg_z_cut[4])
    
            poptlg_x_cut, perrlg_x_cut = fit_lorentz_gauss(x_axis, x_cut, [x_mean, x_cut_max, x_cut_rms, x_cut_max, x_cut_rms], 10000)
            x_cut_fit = lorentz_gauss_function(x_axis, poptlg_x_cut[0], poptlg_x_cut[1], poptlg_x_cut[2], poptlg_x_cut[3], poptlg_x_cut[4])
            
        ### savgol filter
        elif(fitType==4):
            
            z_cut_fit = savgol_filter(z_cut, window_length=savgol[0], polyorder=savgol[1])
            x_cut_fit = savgol_filter(x_cut, window_length=savgol[0], polyorder=savgol[1])            
        
        ### Pseudo Voigt Asymmetric
        elif(fitType==5):
            
            poptpva_z_cut, perrtpva_z_cut = fit_pseudo_voigt_asymmetric(z_axis, z_cut, [z_mean, z_cut_max, z_cut_fwhm, 0.0, 0.0, 0.5], 0, 10000)
            z_cut_fit = pseudo_voigt_asymmetric(z_axis, poptpva_z_cut[0], poptpva_z_cut[1], poptpva_z_cut[2], poptpva_z_cut[3], poptpva_z_cut[4], poptpva_z_cut[5])
            
            poptpva_x_cut, perrtpva_x_cut = fit_pseudo_voigt_asymmetric(x_axis, x_cut, [x_mean, x_cut_max, x_cut_fwhm, 0.0, 0.0, 0.5], 0, 10000)
            x_cut_fit = pseudo_voigt_asymmetric(x_axis, poptpva_x_cut[0], poptpva_x_cut[1], poptpva_x_cut[2], poptpva_x_cut[3], poptpva_x_cut[4], poptpva_x_cut[5])
        
        
        z_cut_fit_fwhm = get_fwhm(z_axis, z_cut_fit, oversampling=overSampling, zero_padding=fwhm_zeroPadding, avg_correction=False, threshold=fwhm_threshold, inmost_outmost=fwhm_int_ext)
        x_cut_fit_fwhm = get_fwhm(x_axis, x_cut_fit, oversampling=overSampling, zero_padding=fwhm_zeroPadding, avg_correction=False, threshold=fwhm_threshold, inmost_outmost=fwhm_int_ext)

        z_cut_fit_rms = calc_rms(z_axis, z_cut_fit)
        x_cut_fit_rms = calc_rms(x_axis, x_cut_fit)
        
    if(export_slices):
        
        np.savetxt(outfilename[:-4]+'_x.dat', np.array([x_axis, x_cut * offsetFactorX]).transpose(), fmt='%.6e')
        np.savetxt(outfilename[:-4]+'_y.dat', np.array([z_axis, z_cut * offsetFactorZ]).transpose(), fmt='%.6e')

    
    # =============== PLOT =============== #
    fontsize = 12
    LTborder = 0.04
    space = 0.02
    RBborder = 0.15
    X_or_Y = 0.28 
    width_main = 1 - RBborder - LTborder - X_or_Y - space

    if figure is None:
        figure = plt.figure() 
        figure.set_size_inches((6.2,5.96))


        rect_2D = [LTborder + X_or_Y + space, RBborder, width_main, width_main]
        rect_X =  [LTborder + X_or_Y + space, RBborder + width_main + space, width_main, X_or_Y]
        rect_Y =  [LTborder, RBborder, X_or_Y, width_main]
        rect_T =  [LTborder, RBborder + width_main + space, X_or_Y, X_or_Y]
        
        ax2D = figure.add_axes(rect_2D)
        axX  = figure.add_axes(rect_X, sharex=ax2D)
        axY  = figure.add_axes(rect_Y, sharey=ax2D)
        axT  = figure.add_axes(rect_T)
        
    else:
        ax2D.clear()
        axX.clear()
        axY.clear()
        axT.clear()

    hor_label = 'X'
    vert_label = 'Y'
    #plottitle='Title'
    
    def set_ticks_size(ax, fontsize):
        try:
            for tick in ax.xaxis.get_major_ticks():
                tick.label.set_fontsize(fontsize)
            for tick in ax.yaxis.get_major_ticks():
                tick.label.set_fontsize(fontsize)
        except:
            ax.tick_params(axis='x', labelsize=fontsize)
            ax.tick_params(axis='y', labelsize=fontsize)

    axY.invert_xaxis() # Invert Y axis
    
    # Adjust Ticks
    axX.xaxis.set_major_locator(plt.MaxNLocator(5))
    axY.xaxis.set_major_locator(plt.MaxNLocator(2))
    axY.yaxis.set_major_locator(plt.MaxNLocator(5))
    axX.minorticks_on()
    axY.minorticks_on()
    ax2D.minorticks_on()
    
    set_ticks_size(axX, fontsize)
    set_ticks_size(axY, fontsize)
    set_ticks_size(ax2D, fontsize)
        
    axX.xaxis.set_tick_params(which='both', direction='in', top=True, bottom=True, labelbottom=False)
    axX.yaxis.set_tick_params(which='both', direction='in', top=True, bottom=True, left=True, right=True, labelleft=False, labelright=True, labelsize=fontsize)
    axX.yaxis.set_label_position("right")

    axY.yaxis.set_tick_params(which='both', direction='in', left=True, right=True, labelleft=False, labelright=False)
    axY.xaxis.set_tick_params(which='both', direction='in', top=True, bottom=True)

    ax2D.yaxis.set_label_position("right")
    ax2D.tick_params(axis='both', which='both', direction='out', left=True,top=True,right=True,bottom=True,labelleft=False,labeltop=False, labelright=True,labelbottom=True, labelsize=fontsize)#, width=1.3)
    
    axT.tick_params(axis='both',which='both',left=False,top=False,right=False,bottom=False,labelleft=False,labeltop=False, labelright=False,labelbottom=False)
    
    # if(offsetFactorX > 1):
    #     axX.text(1.0, 1.03, 'x10$^{0}$'.format(str(expoX)), fontsize=fontsize-1, transform=axX.transAxes)
    # if(offsetFactorZ > 1):
    #     axY.text(0.0, -0.13, 'x10$^{0}$'.format(str(expoZ)), fontsize=fontsize-1, transform=axY.transAxes)        
    
    if(offsetFactorX > 1):
        axX.text(1.0, 1.03, 'x10$^{%s}$' % str(expoX), fontsize=fontsize-1, transform=axX.transAxes)
    if(offsetFactorZ > 1):
        axY.text(0.0, -0.13, 'x10$^{%s}$' % str(expoZ), fontsize=fontsize-1, transform=axY.transAxes)        
    


    if(grid):
        axX.grid(which='both', alpha=0.2, linewidth=0.3)
        axY.grid(which='both', alpha=0.2, linewidth=0.3)
    
    # Write Labels
    ax2D.set_xlabel(xlabel + ' [' + unitLabel + ']', fontsize=fontsize)
    ax2D.set_ylabel(ylabel + ' [' + unitLabel + ']', fontsize=fontsize)

    if ((x_cut.min() >= 0) & (z_cut.min() >= 0)):
        if((cut == 0) & (zlabel == '')):
            zlabel = 'ph/s/0.1%/' + unitLabel
        elif((cut > 0) & (zlabel == '')):
            zlabel = 'ph/s/0.1%/' + unitLabel + '$^2$'
    	
        axX.set_ylabel(zlabel, fontsize=fontsize)

    ############## MAKE PLOTS
    extent = [x_axis.min(), x_axis.max(), z_axis.min(), z_axis.max()]
    
    
    if(np.isnan(z_range_min)):
        vmin = xz_min
    else:
        vmin = z_range_min
    
    if(np.isnan(z_range_max)):
        vmax = xz_max
    else:
        vmax = z_range_max
    
    if(scale==0):
        obj = ax2D.imshow(xz, vmin=vmin, vmax=vmax, origin='lower', 
                          aspect='auto', extent=extent, cmap=cmap) # 2D data

    elif(scale==1):
        # If there is a negative or zero number, it will be replaced by half minimum value higher than 0.
        if(vmin <= 0.0):
            xz_min_except_0 = np.min(xz[xz>0])
            xz[xz<=0.0] = xz_min_except_0/2.0
            vmin = xz_min_except_0/2.0

        obj = ax2D.imshow(xz, norm=LogNorm(vmin=vmin, vmax=vmax), origin='lower', 
                          aspect='auto', extent=extent, cmap=cmap)

        axX.set_yscale('log')
        axY.set_xscale('log')
    
    if(cut != 0):
        ax2D.axvline(x=x_cut_coord, color='white', linestyle='--', linewidth=1, alpha=0.3)
        ax2D.axhline(y=z_cut_coord, color='white', linestyle='--', linewidth=1, alpha=0.3)
        axX.axvline(x=x_cut_coord, color='k', linestyle='--', linewidth=1,  alpha=0.2)
        axY.axhline(y=z_cut_coord, color='k', linestyle='--', linewidth=1,  alpha=0.2)
    
    axX.plot(x_axis, x_cut, '-C0')
    axY.plot(z_cut, z_axis, '-C0')
    axX.plot([x_cut_fwhm[1], x_cut_fwhm[2]], [x_cut_fwhm[3], x_cut_fwhm[4]], '+C0', markersize=12) # FWHM marks
    axY.plot([z_cut_fwhm[3], z_cut_fwhm[4]], [z_cut_fwhm[1], z_cut_fwhm[2]], '+C0', markersize=12) # FWHM marks

    if(fitType != 0):        
        
        axX.plot(x_axis, x_cut_fit, 'C1--')
        axY.plot(z_cut_fit, z_axis, 'C1--')
        axX.plot([x_cut_fit_fwhm[1], x_cut_fit_fwhm[2]], [x_cut_fit_fwhm[3], x_cut_fit_fwhm[4]], '+C1', markersize=12) # FWHM marks
        axY.plot([z_cut_fit_fwhm[3], z_cut_fit_fwhm[4]], [z_cut_fit_fwhm[1], z_cut_fit_fwhm[2]], '+C1', markersize=12) # FWHM marks

    if(scale == 0):
        if ((x_cut_min >= 0) & (z_cut_min >= 0)):
            axX.set_ylim(0 - (x_cut_max - x_cut_min)/10, x_cut_max + (x_cut_max - x_cut_min)/10)
            axY.set_xlim(z_cut_max + (z_cut_max - z_cut_min)/10, 0 - (z_cut_max - z_cut_min)/10)
    
               
    
    if(x_range != 0):
        ax2D.set_xlim(x_range_min, x_range_max)
        axX.set_xlim(x_range_min, x_range_max)
    else:
        ax2D.set_xlim(x_axis[0],x_axis[-1])
    
    if(y_range != 0):
        ax2D.set_ylim(y_range_min, y_range_max)
        axY.set_ylim(y_range_min, y_range_max)
    else:
        ax2D.set_ylim(z_axis[0],z_axis[-1])
    
    
            

    #TITLE
    if(len(plot_title) <= 25):
        text1 = plot_title
    else:
        text1 = plot_title[:25] + '\n' + plot_title[25:50]
            
    # MEAN COORDINATES    
    text2  = hor_label+' POS. MEAN = {0:.3f}\n'.format(x_mean)
    text2 += vert_label+' POS. MEAN = {0:.3f}\n\n'.format(z_mean)
    
    # PEAK COORDINATES
    text3  = hor_label+' POS. PEAK = {0:.3f}\n'.format(x_axis[zmax[0]])
    text3 += vert_label+' POS. PEAK = {0:.3f}\n'.format(z_axis[xmax[0]])

    # DATA RANGE
    text4  = hor_label+' RANGE = {0:.3f}\n'.format(x_axis[-1] - x_axis[0])
    text4 += vert_label+' RANGE = {0:.3f}\n'.format(z_axis[-1] - z_axis[0])

    # CUT FWHM
    text5  = hor_label+' FWHM = {0:.3f}\n'.format(x_cut_fwhm[0])
    text5 += vert_label+' FWHM = {0:.3f}\n'.format(z_cut_fwhm[0])
    
    # CUT RMS
    text6  = hor_label+' RMS = {0:.3f}\n'.format(x_cut_rms)
    text6 += vert_label+' RMS = {0:.3f}\n'.format(z_cut_rms)
    
    # CUT MAXIMUM
    text7  = hor_label+' PEAK = {0:.2e}\n'.format(x_cut_max*offsetFactorX)
    text7 += vert_label+' PEAK = {0:.2e}\n'.format(z_cut_max*offsetFactorZ)
    
    text8 = ''; text9 = ''; text10 = ''; text11 = ''; text12 = ''; # IF FIT IS DISABLED
    
    text13  = 'F = {0:.2e} ph/s'.format(integral)
    
    if(fitType != 0):
        
        # MEAN COORDINATES
        text8  = hor_label+' POS. MEAN = {0:.3f}\n'.format(np.average(x_axis, weights=x_cut_fit))
        text8 += vert_label+' POS. MEAN = {0:.3f}\n'.format(np.average(z_axis, weights=z_cut_fit))
        
        # PEAK COORDINATES
        text9  = hor_label+' POS. PEAK = {0:.3f}\n'.format(x_axis[np.abs(x_cut_fit - np.max(x_cut_fit)).argmin()])
        text9 += vert_label+' POS. PEAK = {0:.3f}\n'.format(z_axis[np.abs(z_cut_fit - np.max(z_cut_fit)).argmin()])
        
        # CUT FIT FWHM
        text10  = hor_label+' FWHM = {0:.3f}\n'.format(x_cut_fit_fwhm[0])
        text10 += vert_label+' FWHM = {0:.3f}\n'.format(z_cut_fit_fwhm[0])
        
        # CUT FIT RMS
        text11  = hor_label+' RMS = {0:.3f}\n'.format(x_cut_fit_rms)
        text11 += vert_label+' RMS = {0:.3f}\n'.format(z_cut_fit_rms)
        
        # CUT FIT MAXIMUM
        text12  = hor_label+' PEAK = {0:.2e}\n'.format(np.max(x_cut_fit*offsetFactorX))
        text12 += vert_label+' PEAK = {0:.2e}\n'.format(np.max(z_cut_fit*offsetFactorZ))
            
    def text(x):
        return {
            1 : [text1, 'black'],
            2 : [text2, 'C0'],
            3 : [text3, 'C0'],
            4 : [text4, 'C0'],
            5 : [text5, 'C0'],
            6 : [text6, 'C0'],
            7 : [text7, 'C0'],
            8 : [text8, 'C1'],
            9 : [text9, 'C1'],
            10 : [text10, 'C1'],
            11 : [text11, 'C1'],
            12 : [text12, 'C1'],
            13 : [text13, 'black'],
        }.get(x, ['', 'k'])       
    
    [text_box1, color1] = text(textA)
    [text_box2, color2] = text(textB)
    [text_box3, color3] = text(textC)
    [text_box4, color4] = text(textD)


    axT.text(LTborder + 0.02, RBborder + width_main + space + X_or_Y - 0.01, text_box1, color=color1, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=9, transform= axT.transAxes)
    axT.text(LTborder + 0.02, RBborder + width_main + space + X_or_Y - 0.24, text_box2, color=color2, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=9, transform= axT.transAxes)
    axT.text(LTborder + 0.02, RBborder + width_main + space + X_or_Y - 0.47, text_box3, color=color3, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=9, transform= axT.transAxes)

    if not show_colorbar:
        axT.text(LTborder + 0.02, RBborder + width_main + space + X_or_Y - 0.70, text_box4, color=color4, family='serif', weight='medium', horizontalalignment='left', verticalalignment='top', fontsize=9, transform= axT.transAxes)
    else:
        axTi = axT.inset_axes([0.1, 0.11, 0.8, 0.06])
        cb = plt.colorbar(obj, cax=axTi, orientation='horizontal') 
        axTi.tick_params(axis='x', which='both', direction='out', top=True, bottom=False, labeltop=True, labelbottom=False, labelsize=9, pad=0)
        axTi.xaxis.offsetText.set_fontsize(9)

    if(outfilename != ''):
        figure.savefig(outfilename, dpi=400, transparent=False)

    if(show_plot and figure is None):
        plt.show()
    elif figure is None:
        plt.close()
        		
        #########################################################################
        #### RETURN OUTPUT AS DICT
        
    output = {'rms_x': x_cut_rms,
              'rms_z': z_cut_rms,
              'fwhm_x': x_cut_fwhm[0],
              'fwhm_z': z_cut_fwhm[0],
              'fwhm_x_coords': x_cut_fwhm[1:],
              'fwhm_z_coords': z_cut_fwhm[1:],
              'integral': integral,
              'mean_x': x_mean,
              'mean_z': z_mean,
              'cut_coord_x': x_cut_coord,
              'cut_coord_z': z_cut_coord,
              'peak_value': xz_max,
              'min_value': xz_min,
              'x_axis': x_axis,
              'z_axis': z_axis,     
              'xz': xz
              }
    
    if(fitType != 0):
        output['fit_rms_x'] = x_cut_fit_rms
        output['fit_rms_z'] = z_cut_fit_rms
        output['fit_fwhm_x'] = x_cut_fit_fwhm[0]
        output['fit_fwhm_z'] = z_cut_fit_fwhm[0]           
        output['fit_fwhm_x_coords'] = x_cut_fit_fwhm[1:]
        output['fit_fwhm_z_coords'] = z_cut_fit_fwhm[1:]
        
        
    return output

			
def set_ticks_size(fontsize):
    for tick in plt.gca().xaxis.get_major_ticks():
        tick.label.set_fontsize(fontsize)
    for tick in plt.gca().yaxis.get_major_ticks():
        tick.label.set_fontsize(fontsize)



def plot_xy(x, y, fmts='', labels='', xlabel='', ylabel='', title='', 
            xlim=[], ylim=[], minorticks=1, grid_major=1, grid_minor=0,
            xticks=[], yticks=[], figsize=(4.5, 3.0), alpha=0.9,
            left=0.15, bottom=0.15, right=0.97, top=0.97, 
            legend_loc='best', xscale='linear', yscale='linear',
            savepath='', savedpi=300, showplot=1):
    
    if(labels == ''):
        labels = []
    else:
        labels = [labels]
        
    if(fmts == ''):
        fmts = []
    else:
        fmts = [fmts]
        
        
    fig, ax = plot_xy_list(x=[x], y=[y], labels=labels, fmts=fmts, 
                           xlabel=xlabel, ylabel=ylabel, title=title, 
                           xlim=xlim, ylim=ylim, minorticks=minorticks,
                           xticks=xticks, yticks=yticks, legend_loc=legend_loc,
                           grid_major=grid_major, grid_minor=grid_minor,
                           figsize=figsize, left=left, right=right, alpha=[alpha],
                           bottom=bottom, top=top, xscale=xscale, yscale=yscale, 
                           savepath=savepath, savedpi=savedpi, showplot=showplot)


def plot_xy_list(x, y, fmts=[], labels=[], xlabel='', ylabel='', title='', 
                 xlim=[], ylim=[], minorticks=1, grid_major=1, grid_minor=0,
                 xticks=[], yticks=[], figsize=(4.5, 3.0), alpha=[],
                 left=0.15, bottom=0.15, right=0.97, top=0.97,
                 legend_loc='best', xscale='linear', yscale='linear',
                 savepath='', savedpi=300, showplot=1):

    if not (len(x) == len(y)):
        raise ValueError('number of arrays in X and Y are different. Exiting...')
    
    n = len(x)
    #### plot
    
    legends = 1
    if(labels == []):
        labels = ['']*n
        legends = 0

    if(fmts == []):
        aux = []
        for i in range(n):
            if(i>=10):
                i = i%10
            aux.append('-C{0:d}'.format(i))
        fmts = aux
        
    if(alpha == []):
        alpha = [0.9]*n

    fig, ax = plt.subplots(figsize=figsize)
    plt.subplots_adjust(left, bottom, right, top)
    
    for i in range(n):        
        plt.plot(x[i], y[i], fmts[i], label=labels[i], alpha=alpha[i])
    
    plt.minorticks_on()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.tick_params(which='both', axis='both', direction='in', top=True, right=True)
    
    if(legends):
        plt.legend(loc=legend_loc)
        
    if(xlim != []):
        plt.xlim(xlim)
    
    if(ylim != []):
        plt.ylim(ylim)
        
    if(xticks != []):
        plt.xticks(xticks)
        
    if(yticks != []):
        plt.yticks(yticks)
        
    if(grid_major):
        plt.grid(which='major', alpha=0.5)

    if(grid_minor):
        plt.grid(which='minor', alpha=0.2)
        
    if(xscale in ['log', 'logarithm']):
        plt.xscale('log')

    if(yscale in ['log', 'logarithm']):
        plt.yscale('log')
        
    if(savepath != ''):
        plt.savefig(savepath, dpi=savedpi)
        
    if(showplot):
        plt.show()
    
    return fig, ax