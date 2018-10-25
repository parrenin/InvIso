from mpl_toolkits.basemap import Basemap, cm
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize
from osgeo import gdalconst
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import matplotlib.pyplot as plt
import gdal
import sys


#write_data=True

#lat1=-75.5
#lon1=124.
#lat2=-75.
#lon2=121.
lon1_bm2=-135
lat1_bm2=-48.458667
lon2_bm2=45
lat2_bm2=-48.458667
##
plot_era40=False
plot_spwd=False
plot_cry=False

#Setting RadarLines directory
RLDir=sys.argv[1]
if RLDir[-1]!='/':
    RLDir=RLDir+'/'

execfile(RLDir+'parameters-Maps.py')

#Reading isochrones' ages
readarray=np.loadtxt(RLDir+'ages.txt')
iso_age=np.concatenate((np.array([0]),readarray[:,0]))

#Running model for each radar line
if run_model:
    for i,RLlabel in enumerate(list_RL+list_RL_extra):
        directory=RLDir+RLlabel
        sys.argv=['AgeModel.py',directory]
        execfile('AgeModel.py')
        plt.close("all")

#Reading data for each radar line
for i,RLlabel in enumerate(list_RL):
    directory=RLDir+RLlabel
    accu_array1=np.loadtxt(directory+'/a.txt')
    botage_array1=np.loadtxt(directory+'/agebottom.txt')
    m_array1=np.loadtxt(directory+'/m.txt')
    G0_array1=np.loadtxt(directory+'/G0.txt')
    pprime_array1=np.loadtxt(directory+'/pprime.txt')
    hor_array1=np.loadtxt(directory+'/agehorizons.txt')
    if i==0:
        accu_array=accu_array1
        botage_array=botage_array1
        m_array=m_array1
        G0_array=G0_array1
        pprime_array=pprime_array1
        hor_array=hor_array1
    else:
        accu_array=np.concatenate((accu_array,accu_array1))
        botage_array=np.concatenate((botage_array,botage_array1))
        #save individual lines to highlight in maps
        if directory==RLDir+'VCD_JKB2g_DVD01a/':
            dvd01a_array=np.loadtxt(directory+'/agebottom.txt')
        if directory==RLDir+'OIA_JKB2n_Y77a/':
            y77a_array=np.loadtxt(directory+'/agebottom.txt')
        m_array=np.concatenate((m_array,m_array1))
        G0_array=np.concatenate((G0_array,G0_array1))
        pprime_array=np.concatenate((pprime_array,pprime_array1))
        hor_array=np.concatenate((hor_array,hor_array1))

#Reading data for extra radar lines
for  i,RLlabel in enumerate(list_RL_extra):
    directory=RLDir+RLlabel
    botage_array1=np.loadtxt(directory+'/agebottom.txt')
    m_array1=np.loadtxt(directory+'/m.txt')
    G0_array1=np.loadtxt(directory+'/G0.txt')
    pprime_array1=np.loadtxt(directory+'/pprime.txt')

    botage_array=np.concatenate((botage_array,botage_array1))
    m_array=np.concatenate((m_array,m_array1))
    G0_array=np.concatenate((G0_array,G0_array1))
    pprime_array=np.concatenate((pprime_array,pprime_array1))

#Importing tif files
def readRasterBandAsArray(filename, bandnum):
    raster = gdal.Open(filename, gdalconst.GA_ReadOnly)
    rasterBand = raster.GetRasterBand(bandnum)
    rasterBandArray = rasterBand.ReadAsArray(0, 0, raster.RasterXSize, raster.RasterYSize).astype(np.float)
        
    rasterBandNoDataValue = rasterBand.GetNoDataValue()
    if rasterBandNoDataValue is not None:
        rasterBandArray[rasterBandArray == rasterBandNoDataValue] = np.nan

    return rasterBandArray

#
#list_maps=['accu-steady']
list_maps=['bare-bed','radar-lines','melting','melting-sigma','Height-Above-Bed-0.8Myr','Height-Above-Bed-1Myr','Height-Above-Bed-1.2Myr','Height-Above-Bed-1.5Myr','bottom-age','min-bottom-age','age-100m','age-150m','age-200m','age-250m','resolution-1Myr','resolution-1.2Myr','resolution-1.5Myr', 'geothermal-heat-flux','geothermal-heat-flux-sigma','pprime','pprime-sigma','accu-sigma','accu-steady']
list_length=len(list_maps)
for i in range(nbiso):
    list_maps.append('accu-layer'+ "%02i"%(i+1) +'_'+str(int(iso_age[i]/1000.))+'-'+str(int(iso_age[i+1]/1000.))+'kyr' )
for i in range(nbhor):
    list_maps.append('age-hor'+"%02i"%(i+1))

for i,MapLabel in enumerate(list_maps):

    print MapLabel+' map'

    fig=plt.figure(MapLabel,figsize=(21/2.54,21/2.54))
    plt.title(MapLabel, y=1.05)
#    map0 = Basemap(projection='spstere', lat_ts=-71, boundinglat=-59.996849, lon_0=180, rsphere=(6378137.00,6356752.3142))
    map0 = Basemap(projection='stere', lat_ts=-71, lat_0=-90, lon_0=180, llcrnrlon=lon1_bm2,llcrnrlat=lat1_bm2, urcrnrlon=lon2_bm2,urcrnrlat=lat2_bm2, rsphere=(6378137.00,6356752.3142))
#    lon,lat=map0(-3333500, 0, inverse=True)
#    print lat
#    print map0(0,-60.)
#    map0 = Basemap(projection='spstere', lat_ts=-71, boundinglat=lat, lon_0=180, rsphere=(6378137.00,6356752.3142))
#    urcrnrlon,urcrnrlat=map0(6667000, 6667000, inverse=True)
#    print llcrnrlon,llcrnrlat,urcrnrlon,urcrnrlat
#    map0 = Basemap(projection='stere', lat_ts=-71, lat_0=-90, lon_0=180, llcrnrlat=llcrnrlat, llcrnrlon=llcrnrlon, urcrnrlat=urcrnrlat, urcrnrlon=urcrnrlon, rsphere=(6378137.00,6356752.3142))
    map1 = Basemap(projection='stere', lat_ts=-71, lat_0=-90, lon_0=180, llcrnrlat=lat1, llcrnrlon=lon1, urcrnrlat=lat2, urcrnrlon=lon2, rsphere=(6378137.00,6356752.3142))
    #map1 = Basemap(projection='spstere', boundinglat=-60, lon_0=180, llcrnrx=-4.5e6, llcrnry=-2.3e6, urcrnrx=-5e6, urcrnry=-2.8e6)
    #m = Basemap(projection='stere', lat_0=-75, lon_0=123., width=1e6, height=1e6)
    #m.drawcoastlines()
    #m.fillcontinents(color='white',lake_color='aqua')
    #m.drawmapboundary(fill_color='aqua')

    map1.drawparallels(np.arange(-90.,81.,1.), labels=[True, False, False, True], dashes=[1, 5], color='0.5')
    map1.drawmeridians(np.arange(-180.,180.,2.), latmax=85., labels=[False, True, True, False], dashes=[1, 5], color='0.5')
    map1.drawmapscale(lon1-1.2, lat1+0.2, lon1, lat1, 50, yoffset=10., barstyle='simple')
    
    ax = plt.axes()


    ##Draw bed topography
    #raster = gdal.Open('bedmap2/bedmap2_bed.txt')
    #band = raster.GetRasterBand(1)
    #array = band.ReadAsArray()
    #array=np.where(array==-9999,np.nan,array)

    #map1.imshow(array[::-1,:])
    #map1.colorbar()


    ##Draw bedmap2 surface contours
    raster2 = gdal.Open(RLDir+'bedmap2/bedmap2_surface.txt')
    band2 = raster2.GetRasterBand(1)
    array2 = band2.ReadAsArray()
    array2=np.where(array2==-9999,np.nan,array2)
    zz=array2[::-1,:]

    x = np.linspace(0, map0.urcrnrx, array2.shape[1])
    y = np.linspace(0, map0.urcrnry, array2.shape[0])
#    print map0.urcrnrx,map0.urcrnry
#    x = np.linspace(0, -6667000, array2.shape[1])
#    y = np.linspace(0, -6667000, array2.shape[0])
    x1,y1=map0(lon1,lat1)
    x2,y2=map0(lon2,lat2)
    x=x-x1
    y=y-y1
    xx, yy = np.meshgrid(x, y)
    
    if MapLabel[:4]<>'accu' and MapLabel<>'bare-bed':
        levels=np.concatenate(( np.arange(3150, 3260, 10),np.arange(3260,3270, 2) ))
    else:
        levels=np.concatenate(( np.arange(3150, 3240, 4),np.arange(3240,3270, 2) ))
    cs=map1.contour(xx,yy, zz, colors='red', levels=levels, alpha=0.7) #color=0.5, new=0.6, a=0.25 or 0.7
#    plt.clabel(cs, inline=1, fontsize=10,fmt='%1.0f')


    ##Draw cryosat surface elevations
    surf_cryosat=readRasterBandAsArray(RLDir+'bedmap2/cryosat-dem_clipped.tif',1)
    zz=surf_cryosat[::-1,::-1]
    latmax=-75.391976
    latmin=-74.026265
    lonmax=132.993563
    lonmin=115.141755
    hmin,vmin=map1(lonmin,latmin)
    hmax,vmax=map1(lonmax,latmax)
    extent=(hmin, hmax, vmin, vmax)
    x = np.linspace(hmin, hmax, surf_cryosat.shape[1])
    y = np.linspace(vmin, vmax, surf_cryosat.shape[0])
    xx, yy = np.meshgrid(x, y)

#    plt.imshow(surf_cryosat, origin='upper', cmap=cmocean.cm.gray, extent=extent, norm=Normalize(vmin=3050, vmax=3300)) #'terrain', 0.4, -1000, 900
#    cb1=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0)
#    cb1.set_label('Cryosat-2 surface elevation (m)')
    if MapLabel[:4]<>'accu' and MapLabel<>'bare-bed':
        levels=np.concatenate(( np.arange(3150, 3260, 10),np.arange(3260,3270, 2) ))
    else:
        levels=np.concatenate(( np.arange(3150, 3260, 4),np.arange(3260,3270, 2) ))
    cs=map1.contour(xx,yy,zz[::-1,:], origin='upper', colors='0.2',levels=levels, alpha=0.4)
#    plt.clabel(cs, inline=1, fontsize=10)
#    import pdb; pdb.set_trace()



#    cs2=map1.contour(xx,yy,zz,levels[1:10],linewidths=2)

    ##Draw bedrock map and contours
    raster2 = gdal.Open(RLDir+'bedmap2/bedmap2_bed.txt')
    band2 = raster2.GetRasterBand(1)
    array2 = band2.ReadAsArray()
    array2=np.where(array2==-9999,np.nan,array2)
    zz=array2[::-1,:]

    x = np.linspace(0, map0.urcrnrx, array2.shape[1])
    y = np.linspace(0, map0.urcrnry, array2.shape[0])
    x1,y1=map0(lon1,lat1)
    x2,y2=map0(lon2,lat2)
    x=x-x1
    y=y-y1
    xx, yy = np.meshgrid(x, y)

    levels=np.arange(-1000., 900., 100.)
    plt.imshow(zz[::-1,:], extent=[max(x),min(x),max(y),min(y)], cmap='terrain', norm=Normalize(vmin=-700, vmax=600), alpha=0.4) #'terrain', 0.4, -1000, 900
#    levels=np.arange(-900, 900, 50)
#    cs=map1.contour(xx,yy,zz, colors='0.1', levels=levels, alpha=0.4) #color=0.5, a=0.25

#    x1_bm2,y1_bm2=map1(lon1_bm2,lat1_bm2)
#    x2_bm2,y2_bm2=map1(lon2_bm2,lat2_bm2)
#    print 'x1_bm2: ', x1_bm2
#    print 'x2_bm2: ', x2_bm2
#    x1=map1.llcrnrx
#    print 'x1: ',x1
#    y1=map1.llcrnry
#    x2=map1.urcrnrx
#    y2=map1.urcrnry
#    plt.imshow(zz, cmap='terrain', extent=[x1_bm2,x2_bm2,y1_bm2,y2_bm2])
#    map1.llcrnrx=x1
#    map1.llcrnry=y1
#    map1.urcrnrx=x2
#    map1.urcrnry=y2

#        from matplotlib.colors import LightSource
#        ls = LightSource(azdeg = 90, altdeg = 20)
#        rgb = ls.shade(zz, plt.cm.terrain)
#        im = map1.imshow(rgb, cmap='terrain', alpha=0.25)

#        cs=map1.contour(xx,yy, zz, colors='m', levels=levels, alpha=0.25)
#        plt.clabel(cs, inline=1, fontsize=10,fmt='%1.0f')


###Draw OIA refined bedrock
#    Bed_BlobA_Geoid4=readRasterBandAsArray(RLDir+'bedmap2/Bed_BlobA_Geoid4.tif',1)
##    hmin=1298450.
##    hmax=1391550.
##    vmin=-840950.
##    vmax=-888950.
##    lonmin,latmin=map0(hmin,vmin, inverse=True)
##    lonmax,latmax=map0(hmax,vmax, inverse=True)
#    latmax=-75.1164861
#    latmin=-75.5905194
#    lonmax=121.1456639
#    lonmin=124.3964778
#    hmin,vmin=map1(lonmin,latmin)
#    hmax,vmax=map1(lonmax,latmax)
#    extent=(hmin, hmax, vmin, vmax)
#    plt.imshow(2000*np.ones(np.shape(Bed_BlobA_Geoid4)), cmap='terrain', extent=extent,norm=Normalize(vmin=-1000, vmax=900))
#    plt.imshow(Bed_BlobA_Geoid4, origin='upper', cmap='terrain', extent=extent,norm=Normalize(vmin=-1000, vmax=900), alpha=0.4) #terrain, 0.4, -1000, 900
##    levels=np.arange(-900, 900, 50)
##    cs=map1.contour(xx,yy,zz, colors='0.1',levels=levels, alpha=0.4)


##Draw compiled radar refined bedrock
#    bed_compiled_Duncan=readRasterBandAsArray(RLDir+'bedmap2/compiled_oia_bed_Duncan.tif',1)
#    #    hmin=1298450.
#    #    hmax=1391550.
#    #    vmin=-840950.
#    #    vmax=-888950.
#    #    lonmin,latmin=map0(hmin,vmin, inverse=True)
#    #    lonmax,latmax=map0(hmax,vmax, inverse=True)
#    latmax=-74.842827
#    latmin=-75.623262
#    lonmax=118.874831
#    lonmin=127.247618
#    hmin,vmin=map1(lonmin,latmin)
#    hmax,vmax=map1(lonmax,latmax)
#    extent=(hmin, hmax, vmin, vmax)
#    bed_compiled_Duncan_val = np.ma.array(bed_compiled_Duncan, mask=np.isnan(bed_compiled_Duncan))
#    plt.imshow(2000+0*(np.empty_like(bed_compiled_Duncan_val)), cmap='terrain',extent=extent,norm=Normalize(vmin=-700,vmax=600))
#    plt.imshow(bed_compiled_Duncan_val, origin='upper', cmap='terrain', extent=extent,norm=Normalize(vmin=-700, vmax=600), alpha=0.4) #'terrain', 0.4, -1000, 900
#    #    levels=np.arange(-900, 900, 50)
#    #    cs=map1.contour(xx,yy,zz, colors='0.1',levels=levels, alpha=0.4)


    if plot_era40==False and plot_spwd==False:
        # Plot box around the refined bed
        xborders=np.array([hmin,hmax,hmax,hmin,hmin])
        yborders=np.array([vmin,vmin,vmax,vmax,vmin])
        plt.plot(xborders,yborders,color='k',linestyle='dashed',alpha=0.4)
        # Draw color bar
        cb0=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0, alpha=0.05)
        cb0.set_label('Bedrock elevation (m)')

    #Draw continent's contour
    #raster3 = gdal.Open('bedmap2/bedmap2_icemask_grounded_and_shelves.txt')
    #band3 = raster3.GetRasterBand(1)
    #array3 = band3.ReadAsArray()

    #x = np.linspace(0, map1.urcrnrx, array3.shape[1])
    #y = np.linspace(0, map1.urcrnry, array3.shape[0])
    #xx, yy = np.meshgrid(x, y)
    #map1.contour(xx,yy, array3[::-1,:], colors='k')

    if plot_era40==True:
        #Draw ERA40 detrended present accu
        ERA40=readRasterBandAsArray(RLDir+'bedmap2/accu-ERA40mixed_Cat5.tif',1)
        latmax=-75.3335278
        latmin=-74.8885111
        lonmax=126.3942028
        lonmin=119.9579389
        hmin,vmin=map1(lonmin,latmin)
        hmax,vmax=map1(lonmax,latmax)
        extent=(hmax, hmin, vmin, vmax)
        norm = Normalize(vmin=21.,vmax=41.)
    #    norm = Normalize(vmin=10.,vmax=30.)
    #    plt.imshow(20*np.ones(np.shape(ERA40)), cmap='seismic_r', extent=extent,norm=Normalize(vmin=-1000,     vmax=900))
        plt.imshow(ERA40, origin='lower', cmap=cmocean.cm.thermal, norm=norm, extent=extent, alpha=1) #'seismic_r'
    #    map1.scatter(x,y, c=accu*1000*0.917, marker='o', lw=4, edgecolor='', s=4, norm=norm, cmap='seismic_r')
        xborders=np.array([hmin,hmax,hmax,hmin,hmin])
        yborders=np.array([vmin,vmin,vmax,vmax,vmin])
    #    plt.plot(xborders,yborders,color='k',linestyle='dashed',alpha=0.4)
        cb1=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0)
        cb1.set_label('ERA40 accumulation rate (mm-we/yr)')

    if plot_spwd==True:
        #Draw ERA40 detrended present accu
        SPWD=readRasterBandAsArray(RLDir+'bedmap2/spwd_dc_Max.tif',1)
#        hmin=972360.329
#        hmax=1747360.329
#        vmin=-1299430.751
#        vmax=-515430.751
#        lonmin,latmin=map0(hmin,vmin, inverse=True)
#        lonmax,latmax=map0(hmax,vmax, inverse=True)
        latmax=-75.1432556
        latmin=-73.3463278
        lonmax=143.192594
        lonmin=106.434836
        hmin,vmin=map1(lonmin,latmin)
        hmax,vmax=map1(lonmax,latmax)
        extent=(hmax, hmin, vmin, vmax)
        norm = Normalize(vmin=-1.5,vmax=1.5)
#        plt.imshow(20*np.ones(np.shape(SPWD)), cmap=cmocean.cm.gray, extent=extent, norm=norm)
        plt.imshow(SPWD, origin='lower', cmap=cmocean.cm.balance, extent=extent, norm=norm, alpha=1) #cmocean.cm.dense_r
    #    map1.scatter(x,y, c=accu*1000*0.917, marker='o', lw=4, edgecolor='', s=4, norm=norm, cmap='seismic_r')
        xborders=np.array([hmin,hmax,hmax,hmin,hmin])
        yborders=np.array([vmin,vmin,vmax,vmax,vmin])
    #    plt.plot(xborders,yborders,color='k',linestyle='dashed',alpha=0.4)
        cb1=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0)
        cb1.set_label('SPWD (m/km)')


    #Draw Bedmap2 surface curvature y (Cat dataset)
#    cry=readRasterBandAsArray(RLDir+'bedmap2/curvature_bm2_cry_Cat3.tif',1)
#    latmax=-75.9745299
#    latmin=-74.2942778
#    lonmax=119.9816394
#    lonmin=126.3691982
#    hmin,vmin=map1(lonmin,latmin)
#    hmax,vmax=map1(lonmax,latmax)
#    extent=(hmax, hmin, vmin, vmax)
##        norm = Normalize(vmin=21.,vmax=41.)
#    #    norm = Normalize(vmin=10.,vmax=30.)
#    #    plt.imshow(20*np.ones(np.shape(ERA40)), cmap='seismic_r', extent=extent,norm=Normalize(vmin=-1000, vmax=900))
#    plt.imshow(cry, origin='lower', cmap='Greys', extent=extent, alpha=1)
#    #    map1.scatter(x,y, c=accu*1000*0.917, marker='o', lw=4, edgecolor='', s=4, norm=norm, cmap='seismic_r')
#    xborders=np.array([hmin,hmax,hmax,hmin,hmin])
#    yborders=np.array([vmin,vmin,vmax,vmax,vmin])
#    #    plt.plot(xborders,yborders,color='k',linestyle='dashed',alpha=0.4)
#    cb1=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0)
#    cb1.set_label('Curvature in y')


    levels='auto'

    if MapLabel=='bare-bed':
        if plot_era40==True:
            cblabel='Bedrock elevation (m)'
        if plot_spwd==True:
            cblabel='SPWD (m/km)'
        else:
            cblabel='Bedrock elevation (km)'

    if MapLabel=='radar-lines':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        x,y=map1(LON,LAT)
        map1.scatter(x,y, c='b', marker='o', lw=0., edgecolor='', s=dotsize)
        #highlight lines of interest
        LON=dvd01a_array[:,0]
        LAT=dvd01a_array[:,1]
        x,y=map1(LON,LAT)
        highlight=['#d05048']
        map1.scatter(x,y, c='r', marker='o',lw=0., edgecolor='', s=7)
        LON=y77a_array[:,0]
        LAT=y77a_array[:,1]
        x,y=map1(LON,LAT)
        map1.scatter(x,y, c='r', marker='o',lw=0., edgecolor='', s=7)
        #Add text for paper
        ax2 = plt.axes()
        ax2.text(0.485,0.38,'A', color='red', fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.48,0.96,"A'", color='red', fontweight='bold', transform=ax2.transAxes)
        #bbox=dict(facecolor='white',edgecolor='red',alpha=0.6)
        ax2.text(0.19,0.57,"B", color='red', fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.67,0.63,"B'", color='red', fontweight='bold', transform=ax2.transAxes)
        ax2.text(0.35,0.28,'Ridge',color='black',fontweight='normal',transform=ax2.transAxes,rotation=-32)
        ax2.text(0.35,0.37,'Concordia Subglacial Trench',color='black',fontweight='normal',transform=ax2.transAxes,rotation=-32)
#        ax2.text(0.15,0.67,'LDC',color='black',fontweight='normal',transform=ax2.transAxes,backgroundcolor='white')

    if MapLabel=='bottom-age':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        botage=botage_array[:,4]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=botage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Bottom age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

#        output=np.transpose(np.vstack((LON,LAT,botage)))
#        with open(RLDir+'agebottom.txt','w') as f:
#            f.write('#LON\tLAT\tbottom age (yr)\n')
#            np.savetxt(f,output, delimiter="\t")

    if MapLabel=='min-bottom-age':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        minbotage=botage_array[:,5]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=minbotage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Minimum bottom age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

#        output=np.transpose(np.vstack((LON,LAT,minbotage)))
#        with open(RLDir+'minagebottom.txt','w') as f:
#            f.write('#LON\tLAT\tmin bottom age (yr)\n')
#            np.savetxt(f,output, delimiter="\t")

    if MapLabel=='age-100m':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        botage=botage_array[:,6]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=botage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

    if MapLabel=='age-150m':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        botage=botage_array[:,7]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=botage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

    if MapLabel=='age-200m':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        botage=botage_array[:,8]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=botage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

    if MapLabel=='age-250m':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        botage=botage_array[:,9]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=0.7,vmax=5.)
        map1.scatter(x,y, c=botage/1e6, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Age (Myr)'
        levels=np.array([0.7, 0.8, 0.9, 1.0, 1.2, 1.4, 1.6, 2, 2.5, 3, 3.5, 4, 5])

    if MapLabel=='resolution-1Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        resolution=botage_array[:,10]
        x,y=map1(LON,LAT)

        norm = LogNorm(vmin=1.,vmax=20.)
        map1.scatter(x,y, c=resolution/1e3, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Resolution at 1Myr (kyr/m)'
        levels=np.array([1., 2., 4., 6., 8., 10., 20., 40.])

#        output=np.transpose(np.vstack((LON,LAT,resolution/1e3)))
#        with open(RLDir+'resolution1Myr.txt','w') as f:
#            f.write('#LON\tLAT\tresolution (kyr/m)\n')
#            np.savetxt(f,output, delimiter="\t")

    if MapLabel=='resolution-1.2Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        resolution=botage_array[:,11]
        x,y=map1(LON,LAT)

        map1.scatter(x,y, c=resolution/1e3, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Resolution at 1.2Myr (kyr/m)'
        levels=np.array([1., 2., 4., 6., 8., 10., 20., 40.])

#        output=np.transpose(np.vstack((LON,LAT,resolution/1e3)))
#        with open(RLDir+'resolution1.2Myr.txt','w') as f:
#            f.write('#LON\tLAT\tresolution (kyr/m)\n')
#            np.savetxt(f,output, delimiter="\t")

    if MapLabel=='resolution-1.5Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        resolution=botage_array[:,12]
        x,y=map1(LON,LAT)

        map1.scatter(x,y, c=resolution/1e3, marker='o', lw=0., edgecolor='', norm = norm, s=dotsize)
        cblabel='Resolution at 1.5Myr (kyr/m)'
        levels=np.array([1., 2., 4., 6., 8., 10., 20., 40.])

#        output=np.transpose(np.vstack((LON,LAT,resolution/1e3)))
#        with open(RLDir+'resolution1.5Myr.txt','w') as f:
#            f.write('#LON\tLAT\tresolution (kyr/m)\n')
#            np.savetxt(f,output, delimiter="\t")

    if MapLabel=='Height-Above-Bed-0.8Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        height=botage_array[:,14]
        x,y=map1(LON,LAT)

        res=map1.scatter(x,y, c=height, marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='Height above bed (m)'

    if MapLabel=='Height-Above-Bed-1Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        height=botage_array[:,15]
        x,y=map1(LON,LAT)

        res=map1.scatter(x,y, c=height, marker='o', lw=0., edgecolor='', s=dotsize)
        cb.set_label='Height above bed (m)'
        

    if MapLabel=='Height-Above-Bed-1.2Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        height=botage_array[:,16]
        x,y=map1(LON,LAT)

        res=map1.scatter(x,y, c=height, marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='Height above bed (m)'
        

    if MapLabel=='Height-Above-Bed-1.5Myr':

        LON=botage_array[:,0]
        LAT=botage_array[:,1]
        height=botage_array[:,17]
        x,y=map1(LON,LAT)

        res=map1.scatter(x,y, c=height, marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='Height above bed (m)'
        
#        levels=np.array([1., 2., 4., 6., 8., 10., 20., 40.])
#        cb.set_ticks(levels)
#        cb.set_ticklabels(levels)


    elif MapLabel=='melting':

        LON=m_array[:,0]
        LAT=m_array[:,1]
        melting=m_array[:,3]
        x,y=map1(LON,LAT)

        norm = Normalize(vmin=0.,vmax=5.)

        map1.scatter(x,y, c=melting*1e3, marker='o', lw=0., edgecolor='', s=dotsize, norm=norm)
        cblabel='Melting (mm/yr)'
        

#        output=np.transpose(np.vstack((LON,LAT,melting*1e3)))
#        with open(RLDir+'m.txt','w') as f:
#            f.write('#LON\tLAT\tmelting (mm/yr)\n')
#            np.savetxt(f,output, delimiter="\t")


    elif MapLabel=='melting-sigma':

        LON=m_array[:,0]
        LAT=m_array[:,1]
        sigma_melting=m_array[:,4]
        x,y=map1(LON,LAT)

        norm = Normalize(vmin=0.,vmax=1.)


        map1.scatter(x,y, c=sigma_melting*1e3, marker='o', lw=0., edgecolor='', s=dotsize, norm=norm)
        cblabel='$\sigma$ Melting (mm/yr)'
        

    elif MapLabel=='geothermal-heat-flux':

        LON=G0_array[:,0]
        LAT=G0_array[:,1]
        G0=G0_array[:,3]
        x,y=map1(LON,LAT)

        map1.scatter(x,y, c=G0*1e3, marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='G0 (mW/m$^2$)'
        

    elif MapLabel=='geothermal-heat-flux-sigma':

        LON=G0_array[:,0]
        LAT=G0_array[:,1]
        sigma_G0=G0_array[:,4]
        x,y=map1(LON,LAT)

        map1.scatter(x,y, c=sigma_G0*1e3, marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='$\sigma_{G0}$ (mW/m$^2$)'
        

    elif MapLabel=='pprime':

        LON=pprime_array[:,0]
        LAT=pprime_array[:,1]
        pprime=pprime_array[:,3]
        x,y=map1(LON,LAT)

#        levels=np.arange(-1,3.1, 0.1)
        norm = Normalize(vmin=-1.,vmax=3.)
        map1.scatter(x,y, c=pprime, marker='o', lw=0., edgecolor='', s=dotsize, norm=norm)
        cblabel='pprime'
        

#        cb.set_ticks(levels)

#        output=np.transpose(np.vstack((LON,LAT,pprime)))
#        with open(RLDir+'p.txt','w') as f:
#            f.write('#LON\tLAT\tpprime\n')
#            np.savetxt(f,output, delimiter="\t")


    elif MapLabel=='pprime-sigma':

        LON=pprime_array[:,0]
        LAT=pprime_array[:,1]
        sigma_pprime=pprime_array[:,4]
        x,y=map1(LON,LAT)

        norm = Normalize(vmin=0.,vmax=1.)
        map1.scatter(x,y, c=sigma_pprime, marker='o', lw=0., edgecolor='', s=dotsize, norm=norm)
        cblabel='$\sigma$ pprime'
        

    elif i>=list_length-2 and i<list_length+nbiso:

        LON=accu_array[:,0]
        LAT=accu_array[:,1]
        x,y=map1(LON,LAT)
        norm = Normalize(vmin=12.,vmax=22.) #10-30; 12-22 for newest
        if MapLabel=='accu-sigma':
            accu=accu_array[:,4]
            norm = Normalize(vmin=0.,vmax=1.)
        elif MapLabel=='accu-steady':
                if plot_era40==True:
                    accu=accu_array[:,3]/0.65 #divide by 0.65 to go from steady-state to present day (computed by Fred from AICC12)
                else:
                    accu=accu_array[:,3]
#            output=np.transpose(np.vstack((LON,LAT,accu*100)))
#            with open(RLDir+'a.txt','w') as f:
#                f.write('#LON\tLAT\taccu (cm/yr)\n')
#                np.savetxt(f,output, delimiter="\t")

        else:
            accu=accu_array[:,i-list_length+5]


        if plot_era40==True:
            map1.scatter(x,y, c=accu*1000*0.917, marker='o', lw=4, edgecolor='', s=4, vmin=21, vmax=41, cmap=cmocean.cm.thermal) #if use steady-state accu modified to get present day acc, 'seismic_r', vmin=21, vmax=41
        else:
            map1.scatter(x,y, c=accu*1000*0.917, marker='o', lw=4, edgecolor='', s=4, norm=norm)
#            accu_low = np.ma.masked_where((accu*1000*0.917)>17,accu)
#            accu_high = np.ma.masked_where((accu*1000*0.917)<=17,accu)
#            map1.scatter(x,y, c=accu_high*1000*0.917, marker='o', lw=4, edgecolor='', s=4, vmin=-18, vmax=22, cmap='Reds')
#            map1.scatter(x,y, c=accu_low*1000*0.917, marker='o', lw=4, edgecolor='', s=4, norm=norm , cmap=cmocean.cm.thermal) #'seismic_r',cmocean.cm.dense_r, 'seismic_r', norm=norm
        cblabel='accu (mm-we/yr)'
        
    elif i>=list_length+nbiso:
        LON=hor_array[:,0]
        LAT=hor_array[:,1]
        x,y=map1(LON,LAT)

        age=hor_array[:,i-(list_length+nbiso)+3]

        map1.scatter(x,y, c=age/1000., marker='o', lw=0., edgecolor='', s=dotsize)
        cblabel='age (kyr B1950)'


    if MapLabel<>'radar-lines':
        cb=plt.colorbar(orientation='horizontal', shrink=0.7, pad=0.1)
        cb.set_label(cblabel)
        if levels<>'auto':
            cb.set_ticks(levels)
            cb.set_ticklabels(levels)


    if is_drill:
        xdrill,ydrill=map1(lon_drill,lat_drill)
        map1.scatter(xdrill,ydrill, marker='*', c='y', edgecolor='k', s=70)

    plt.tight_layout()

    pp=PdfPages(RLDir+MapLabel+'.pdf')
    pp.savefig(plt.figure(MapLabel))
    pp.close()
    plt.savefig(RLDir+MapLabel+'.'+output_format, format=output_format, bbox_inches='tight')
    plt.close(fig)

plt.show()
