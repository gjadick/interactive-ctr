#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 17 08:06:31 2022

@author: glj
"""

######### README ##################
#
# 1. inputs
#     set 'matfile' to the .mat filename 
#     set 'N_points' to the number of spheres you want to measure
# 
# 2. usage
#     To select ROIs, you must click two diagonal corners.
#     This script automatically loops over all frames of the .mat file.
#     For each frame, first select a signal ROI, then a background ROI. Repeat.
#     (signal ROIs will show as red, background ROIs as blue. It's a little slow though...)
#     (the right plot will be populated with scatter data as it is calculated)
#     To move on to the next frame, double click just inside the upper left corner.
#
####################################

import os
import numpy as np
import scipy.io

import matplotlib
import matplotlib.pyplot as plt


matfile='./01_element.mat'  # name of file to assess
N_points = 100              # number of target data points


def get_ROI(img, diag_corners):
    '''
    given an image and two diag corners of an ROI, 
    returns the 2D ROI selected + coordinates of all four corners
    '''
    x1, y1 = diag_corners[0]
    x2, y2 = diag_corners[1]
    
    # get corners of ROI
    x_corners = [x1, x1, x2, x2]
    y_corners = [y1, y2, y2, y1]
    
    # get integer bounds + ROI image
    x0, xf = np.floor(np.min([x1,x2])).astype(int), np.ceil(np.max([x1,x2])).astype(int)
    y0, yf = np.floor(np.min([y1,y2])).astype(int), np.ceil(np.max([y1,y2])).astype(int)
    img_ROI = img[ y0:yf, x0:xf]
    return img_ROI, x_corners, y_corners


def get_CNR(signal_ROI, background_ROI):
    signal = np.mean(signal_ROI)
    signal_std = np.std(signal_ROI)
    background = np.mean(background_ROI)
    background_std = np.std(background_ROI)
    CNR = np.abs(signal-background)/np.sqrt(signal_std**2 + background_std**2)
    return CNR


def get_CTR(signal_ROI, background_ROI):
    signal = np.mean(signal_ROI)
    background = np.mean(background_ROI)
    CTR = 20*np.log10(signal/background)
    return CTR


def bin_data(x, y, bin_sz):
    '''
    for scatter plot data (x,y),
    bins x values into groupings with width 'bin_sz'
    returns xbins, ybins, and standard deviation of ybins
    '''
    x0 = int(np.min(x) - np.min(x)%bin_sz)
    xf = int(np.max(x) - np.max(x)%bin_sz)
    
    xbins = []
    ybins = []
    ybins_err = []
    for xbin in np.arange(x0, xf+bin_sz, bin_sz):
        this_ybin = [y[i] for i in range(len(x)) if x[i]>=xbin and x[i]<xbin+bin_sz]
        if len(this_ybin)>0:
            xbins.append(xbin+bin_sz/2) # bin center
            ybins.append(np.mean(this_ybin))
            ybins_err.append(np.std(this_ybin))

    return np.array(xbins), np.array(ybins), np.array(ybins_err)



if __name__=='__main__':
    


    mat = scipy.io.loadmat(matfile)
    N = mat['RData'].shape[3]
    im_kwargs = {'cmap': 'gray', 'vmin':0, 'vmax':3e5}

    CTR_data = []   # append data as sublists: [depth_px, CTR, i, xc_signal, yc_signal, xc_background, yc_background]

    #%matplotlib qt
    for i in range(N):
        
        # if all data points finished, break loop
        if len(CTR_data) >= N_points:
            break

        # load image
        M = mat['RData'][:,:,0,i]
        Ny, Nx = M.shape

        # plot image, get ROIs
        fig,[ax, ax2] = plt.subplots(1,2,figsize=[8,6],dpi=150, gridspec_kw={'width_ratios': [2, 1.4]})
        fig.tight_layout(pad=0)
        ax.imshow(M, aspect=0.333, **im_kwargs)
        ax.text(1, 30, f'img #{i+1}/{N}', color='w', family='serif', weight='bold', fontsize=8,  backgroundcolor='k')
        ax.text(1, 60, f'data points #{len(CTR_data)}/{N_points}', color='w', family='serif', weight='bold', fontsize=8, backgroundcolor='k')
        ax.axvline(Nx/2, color='c', lw=1)
        
        # show 'X' in upper left corner, to click through to next image
        ax.plot(.5,3, 'ks', markersize=5)
        ax.plot(.5,3, 'rx', markersize=5, markeredgewidth=1)
        
        # set axes limits for real-time plotting
        ax2.set_xlim(0,500)
        ax2.set_ylim(-50,0)

        if len(CTR_data) > 0:
            ax2.plot([item[0] for item in CTR_data], [item[1] for item in CTR_data], 'ko')

        # get signal 0
        signal = plt.ginput(2)
        signal_ROI, xc_signal, yc_signal = get_ROI(M, signal)
        ax.plot(np.tile(xc_signal,2), np.tile(yc_signal,2) ,'r-')
        fig.canvas.draw()

        # loop over as many spheres as wanted, until click in upper left corner or
        # enough data is acquired.
        while np.sum(np.array(signal)) > 20 and len(CTR_data) <= N_points:

            # get background 
            background = plt.ginput(2)
            background_ROI, xc_background, yc_background = get_ROI(M, background)
            ax.plot(np.tile(xc_background,2), np.tile(yc_background,2) ,'b-')
            fig.canvas.draw()

            # calculate depth as mean of signal ROI
            depth_px = np.mean(yc_signal)      

            # calculate CTR
            CTR = get_CTR(signal_ROI, background_ROI)
            CTR_data.append([depth_px, CTR, xc_signal, i, yc_signal, xc_background, yc_background])

            ax.text(1, 60, f'data points #{len(CTR_data)}/{N_points}', color='w', family='serif', weight='bold', fontsize=8, backgroundcolor='k')
            ax2.plot(depth_px, CTR, 'ko')
            fig.canvas.draw()

            # get signal repeat
            signal = plt.ginput(2)
            signal_ROI, xc_signal, yc_signal = get_ROI(M, signal)
            ax.plot(np.tile(xc_signal,2), np.tile(yc_signal,2) ,'r-')
            fig.canvas.draw()

        plt.close()

        
    # save data as numpy file
    depth_vec = np.array([item[0] for item in CTR_data])
    CTR_vec =   np.array([item[1] for item in CTR_data])
    np.save(matfile.replace('.mat','_CTR.npy'), np.array([depth_vec, CTR_vec]))

    # plot data, scatter plot + binned plot
    bin_sz = 10
    depth_bins, CTR_bins, CTR_bins_err = bin_data(depth_vec, CTR_vec, bin_sz)

    
    # %matplotlib inline  
    fig,ax=plt.subplots(1,2,figsize=[6,3],dpi=150, sharey=True)
    ax[0].plot(depth_vec, CTR_vec, 'k.')
    ax[0].set_ylabel('CTR [dB]', )
    ax[0].set_xlabel('depth [px]')
    ax[1].errorbar(depth_bins, CTR_bins, yerr=CTR_bins_err, marker='.', color='k', ls='')
    ax[1].set_xlabel('depth [px]')
    fig.tight_layout()
    plt.show()
