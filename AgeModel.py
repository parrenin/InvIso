#TODO: compare with age and temperature profiles from the EDC ice core.
#TODO: add a sigma on G0 of 5 mW/m^2

import time
import sys
import math as m
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.collections import LineCollection
from matplotlib.colors import LogNorm
from scipy.interpolate import interp1d
from scipy.optimize import leastsq
from matplotlib.backends.backend_pdf import PdfPages
from scipy.special import erf


###Registration of start time
start_time = time.time()     



#Physical constants
Kg0=9.828
Kg1=-5.7*10**-3
Lf=333.5*10**3
rhog=917.
cg0=152.5
cg1=7.122
ggrav=9.81
#Tf0=273.16          #This is the value from Cuffey and Paterson (2010)
#Tf1=-9.8e-8          #This is the value from Cuffey and Paterson (2010)
Tf0=273.16-0.024         #This is the value from Catherine Ritz's thesis
Tf1=-7.4e-8         #This is the value from Catherine Ritz's thesis

def cg(T):
#    return 2097.*np.ones(np.shape(T))    #at 0 degC
    return cg0+cg1*T

def Kg(T, D):
    """From Patterson eqs. 9.2 and 9.4"""
#    return 2.10*np.ones(np.shape(T))     #at 0 degC
#    return Kg0*np.exp(Kg1*T)
    KiT=Kg0*np.exp(Kg1*T)
    return (2.*KiT*D)/(3.-D)

def Tf(P):
    return Tf0+Tf1*P

def interp1d_stair_aver(x, y):   #TODO: deal with the case x not sorted
    """
    Interpolation of a staircase function using averaging.
    This function returns nan outside of the input abscissa range.
    """
    def f(xp):
        yp=np.empty(np.size(xp)-1)
        xmod=x[~(np.isnan(x)+np.isnan(y))]
        ymod=y[~(np.isnan(x)+np.isnan(y))]
        yint=np.cumsum(np.concatenate((np.array([0]),ymod[:-1]*(xmod[1:]-xmod[:-1]))))
        g=interp1d(xmod,yint, bounds_error=False, fill_value=np.nan)
#        yp=np.where((xp[:-1]>min(xmod))*(xp[1:]<max(xmod)),(g(xp[1:])-g(xp[:-1]))/(xp[1:]-xp[:-1]),np.nan)     #Maybe this is suboptimal since we compute twice g(xp[i])
        yp=np.where((xp[:-1]>min(xmod))*(xp[1:]<max(xmod)),(g(xp[1:])-g(xp[:-1]))/(xp[1:]-xp[:-1]),np.nan)     #Maybe this is suboptimal since we compute twice g(xp[i])
        return yp

    return f

def interp1d_stair_aver_withnan(x, y):   #TODO: deal with the case x not sorted
    """
    Interpolation of a staircase function using averaging.
    This function returns nan when there are all nans in one interpolation interval.
    """
    def f(xp):
        xmod=x[~(np.isnan(x)+np.isnan(y))]
        ymod=y[~(np.isnan(x)+np.isnan(y))]
        yp=np.empty(np.size(xp)-1)
        yint=np.cumsum(np.concatenate((np.array([0]),ymod[:-1]*(xmod[1:]-xmod[:-1]))))
        g=interp1d(xmod,yint, bounds_error=False, fill_value=np.nan)
#        yp=np.where((xp[:-1]>min(xmod))*(xp[1:]<max(xmod)),(g(xp[1:])-g(xp[:-1]))/(xp[1:]-xp[:-1]),np.nan)     #Maybe this is suboptimal since we compute twice g(xp[i])
        yp=np.where((xp[:-1]>min(xmod))*(xp[1:]<max(xmod)),(g(xp[1:])-g(xp[:-1]))/(xp[1:]-xp[:-1]),np.nan)     #Maybe this is suboptimal since we compute twice g(xp[i])
        for i in range(np.size(xp)-1):
            if np.isnan(y[np.where((x>=xp[i])*(x<xp[i+1]))]).all():
                yp[i]=np.nan
        return yp

    return f

def interp1d_lin_aver_withnan(x,y):
    """
    Interpolation of a linear by parts function using averaging.
    This function returns nan when there are all nans in one interpolation interval.
    """
    def f(xp):
        yp=np.empty(np.size(xp)-1)
        for i in range(np.size(xp)-1):
#            print i, xp[i], xp[i+1]
            if np.isnan(y[np.where((x>xp[i])*(x<xp[i+1]))]).all():
                yp[i]=np.nan
            else:
                xmod=x[~(np.isnan(x)+np.isnan(y))]
                ymod=y[~(np.isnan(x)+np.isnan(y))]
                xmod2=xmod[np.where((xmod>xp[i])*(xmod<xp[i+1]))]
                ymod2=ymod[np.where((xmod>xp[i])*(xmod<xp[i+1]))]
                xmod3=np.concatenate((np.array([xp[i]]),xmod2,np.array([xp[i+1]])))
                g=interp1d(x,y)
                ymod3=np.concatenate((np.array([g(xp[i])]),ymod2,np.array([g(xp[i+1])])))
#                print xmod3
#                print ymod3
                yp[i]=np.sum((ymod3[1:]+ymod3[:-1])/2*(xmod3[1:]-xmod3[:-1]))
                yp[i]=yp[i]/(xp[i+1]-xp[i])
#                print yp[i]
        return yp
    return f
      
def interp1d_lin_aver(x,y):
    """
    Interpolation of a linear by parts function using averaging.
    This function returns nan when there are all nans in one interpolation interval.
    """
    def f(xp):
        yp=np.empty(np.size(xp)-1)
        for i in range(np.size(xp)-1):
#            print i, xp[i], xp[i+1]
            xmod=x[~(np.isnan(x)+np.isnan(y))]
            ymod=y[~(np.isnan(x)+np.isnan(y))]
            xmod2=xmod[np.where((xmod>xp[i])*(xmod<xp[i+1]))]
            ymod2=ymod[np.where((xmod>xp[i])*(xmod<xp[i+1]))]
            xmod3=np.concatenate((np.array([xp[i]]),xmod2,np.array([xp[i+1]])))
            g=interp1d(x,y, bounds_error=False, fill_value=np.nan)
            ymod3=np.concatenate((np.array([g(xp[i])]),ymod2,np.array([g(xp[i+1])])))
#                print xmod3
#                print ymod3
            if np.isnan(ymod3).all():
                yp[i]=np.nan
            else:
                xmod4=xmod3[np.where(~(np.isnan(ymod3)+np.isnan(xmod3)))]
                ymod4=ymod3[np.where(~(np.isnan(ymod3)+np.isnan(xmod3)))]
#                if i==9:
#                    print xmod4,ymod4
                yp[i]=np.sum((ymod4[1:]+ymod4[:-1])/2*(xmod4[1:]-xmod4[:-1]))
                yp[i]=yp[i]/(xmod4[-1]-xmod4[0])
#                print yp[i]
        return yp
    return f


class RadarLine:

    def __init__(self, label):
        self.label=label

    def init(self):
        self.is_bedelev=False
        self.calc_sigma=True
        self.invert_G0=False
        self.settick='auto'

        #definition of some global parameters
        execfile(self.label+'../parameters-AllRadarLines.py')
        filename=self.label+'parameters.py'
        if os.path.isfile(filename):
            execfile(filename)


        #Reading the radar dataset
        nbcolumns=6+self.nbiso+self.is_bedelev
        print 'nbcolumns:',nbcolumns
        readarray=np.loadtxt(self.label+'radar-data.txt', usecols=range(nbcolumns))
        self.LON_raw=readarray[:,0]
        self.LAT_raw=readarray[:,1]
        self.x_raw=readarray[:,2]
        self.y_raw=readarray[:,3]
        self.distance_raw=readarray[:,4]
#        self.thk_raw=readarray[:,5]*self.dilatation_factor
        self.thk_raw=readarray[:,5]+self.firn_correction
        if self.is_bedelev:
            self.bedelev=readarray[:,6]-self.firn_correction
            self.iso_raw=np.transpose(readarray[:,7:7+self.nbiso])+self.firn_correction
        else:
            self.iso_raw=np.transpose(readarray[:,6:6+self.nbiso])+self.firn_correction

#        #Interpolation of the radar dataset
#        if self.reverse_distance:
#            toto=self.distance_raw[-1]-self.distance_end
#            self.distance_end=self.distance_raw[-1]-self.distance_start
#            self.distance_start=toto+0.
##            print self.distance_start, self.distance_end
#            self.distance_raw=self.distance_raw[-1]-self.distance_raw
#            self.LON_raw=self.LON_raw[::-1]
#            self.LAT_raw=self.LAT_raw[::-1]
#            self.x_raw=self.x_raw[::-1]
#            self.y_raw=self.y_raw[::-1]
#            self.distance_raw=self.distance_raw[::-1]
#            self.thk_raw=self.thk_raw[::-1]
#            self.iso_raw=self.iso_raw[:,::-1]
       
#        if self.reset_distance:
#            self.distance_raw=self.distance_raw-self.distance_start

        if self.distance_start=='auto':
            self.distance_start=int(np.min(self.distance_raw)+2.99)
        if self.distance_end=='auto':
            self.distance_end=int(np.max(self.distance_raw)-2.)

        #Interpolation of the datasets
        self.distance=np.arange(self.distance_start, self.distance_end+self.resolution, self.resolution) 
#        self.distance=np.arange(90, 100+self.resolution, self.resolution) 
#        f=interp1d(self.distance_raw,self.thk_raw)  #TODO: we want to integrate here to smooth the record. Same for iso.
#        self.thk=f(self.distance)
        f=interp1d_stair_aver(self.distance_raw,self.thk_raw)    #TODO: the input function is not a staircase one
        self.thk=f(np.concatenate((self.distance-self.resolution/2, np.array([self.distance[-1]+self.resolution/2]))))
        self.iso=np.zeros((self.nbiso,np.size(self.distance)))
        self.iso_modage=np.empty_like(self.iso)
        self.iso_EDC=np.zeros(self.nbiso)
        for i in range(self.nbiso):
            f=interp1d_lin_aver(self.distance_raw,self.iso_raw[i,:])
            self.iso[i,:]=f(np.concatenate((self.distance-self.resolution/2, np.array([self.distance[-1]+self.resolution/2]))))
        f=interp1d(self.distance_raw,self.LON_raw)
        self.LON=f(self.distance)
        f=interp1d(self.distance_raw, self.LAT_raw)
        self.LAT=f(self.distance)



        #Reading the AICC2012 dataset, calculation of steady age and interpolation
        readarray=np.loadtxt(self.label+'../AICC2012.txt')
        self.AICC2012_depth=readarray[:,0]
        self.AICC2012_iedepth=readarray[:,1]
        self.AICC2012_accu=readarray[:,2]
        self.AICC2012_age=readarray[:,3]
        self.AICC2012_sigma=readarray[:,4]

#        self.AICC2012_steadyage=np.cumsum(np.concatenate((np.array([self.AICC2012_age[0]]),(self.AICC2012_age[1:]-self.AICC2012_age[:-1])*self.AICC2012_accu[:-1]/(self.AICC2012_iedepth[1:]-self.AICC2012_iedepth[:-1])/self.AICC2012_accu[0]*(self.AICC2012_depth[1:]-self.AICC2012_depth[:-1]))))
        self.AICC2012_averageaccu=np.sum((self.AICC2012_age[1:]-self.AICC2012_age[:-1])*self.AICC2012_accu[:-1])/(self.AICC2012_age[-1]-self.AICC2012_age[0])
        print 'average accu: ',self.AICC2012_averageaccu
        self.AICC2012_steadyage=np.cumsum(np.concatenate((np.array([self.AICC2012_age[0]]),(self.AICC2012_age[1:]-self.AICC2012_age[:-1])*self.AICC2012_accu[:-1]/self.AICC2012_averageaccu)))
#        self.AICC2012_steadyage=self.AICC2012_steadyage*self.AICC2012_age[-1]/self.AICC2012_steadyage[-1]
        print 'steady/unsteady ratio: ', self.AICC2012_steadyage[-1]/self.AICC2012_age[-1]

#        print 'prior value on melting',self.m_EDC

        if (self.is_EDC and self.calc_isoage):
#        if self.is_EDC:
            for i in range(self.nbiso):
                f=interp1d(self.distance_raw,self.iso_raw[i,:])
                self.iso_EDC[i]=f(self.distance_EDC)

            f=interp1d(self.AICC2012_depth,self.AICC2012_age)
            self.iso_age=f(self.iso_EDC)
            self.iso_age=np.transpose([self.iso_age])
            f=interp1d(self.AICC2012_depth,self.AICC2012_sigma)
            self.iso_sigma=f(self.iso_EDC)
            self.iso_sigma=np.transpose([self.iso_sigma])

            output=np.hstack((self.iso_age, self.iso_sigma))
#            with open(self.label+'-ages.txt','w') as f:
#                f.write('#age (yr BP)\tsigma_age (yr BP)\n')
#                np.savetxt(f,output, delimiter="\t") 
            with open(self.label+'ages.txt','w') as f:
                f.write('#age (yr BP)\tsigma_age (yr BP)\n')
                np.savetxt(f,output, delimiter="\t")

#Reading ages of isochrones and their sigmas
        readarray=np.loadtxt(self.label+'ages.txt')
        self.iso_age=np.transpose([readarray[:,0]])
        self.iso_age=self.iso_age[0:self.nbiso]
        self.iso_sigma=np.transpose([readarray[:,1]])
        self.iso_sigma=self.iso_sigma[0:self.nbiso]
        f=interp1d(self.AICC2012_age,self.AICC2012_steadyage)
        self.iso_steadyage=f(self.iso_age)





        f=interp1d(np.concatenate((self.AICC2012_depth,np.array([self.AICC2012_depth[-1]+3000]))),np.concatenate((self.AICC2012_iedepth,np.array([self.AICC2012_iedepth[-1]+3000]))))
        g=interp1d(np.concatenate((self.AICC2012_iedepth,np.array([self.AICC2012_iedepth[-1]+3000]))),np.concatenate((self.AICC2012_depth,np.array([self.AICC2012_depth[-1]+3000]))))
#        self.isoie=f(self.iso)
        self.thkie=f(self.thk)

        self.a=self.a*np.ones(np.size(self.distance))
        self.G0=self.G0*np.ones_like(self.distance)
#        self.mu=self.m/self.a
        self.pprime=self.pprime*np.ones(np.size(self.distance))
        self.p=np.empty_like(self.pprime)
        self.s=self.s*np.ones(np.size(self.distance))

        self.zetagrid=np.arange(0,1+self.dzeta,self.dzeta)
        self.zetagrid=self.zetagrid[::-1]
        self.zetagrid=np.transpose([self.zetagrid])
        self.agesteady=np.zeros((np.size(self.zetagrid),np.size(self.distance)))
        self.age=np.zeros((np.size(self.zetagrid),np.size(self.distance)))
        self.age_density=np.zeros((np.size(self.zetagrid)-1,np.size(self.distance)))
        self.T=np.empty_like(self.age)
        self.T_anal=np.empty_like(self.age)
        self.Tf=np.empty_like(self.distance)
        self.Tm=np.empty_like(self.distance)
        self.alpha=np.empty_like(self.distance)
        self.zeta=np.ones((np.size(self.zetagrid),np.size(self.distance)))*self.zetagrid
        self.depth=self.thk*(1-self.zeta)
        self.depthie=f(self.depth)
        self.zetaie=(self.thkie-self.depthie)/self.thkie
        self.dist=np.ones((np.size(self.zetagrid),np.size(self.distance)))*self.distance
        self.D=(self.depthie[1:,]-self.depthie[:-1,])/(self.depth[1:,]-self.depth[:-1,])
        self.DeltaT=np.empty_like(self.distance)
        self.G=np.empty_like(self.distance)
        self.m=np.empty_like(self.distance)
        self.mu=np.empty_like(self.distance)
        self.omega_D=np.empty_like(self.age)
        self.omega=np.empty_like(self.age)
        self.tau=np.empty_like(self.age)
        self.uz=np.empty_like(self.age)
        self.sigma_a=np.zeros_like(self.distance)
        self.sigma_m=np.zeros_like(self.distance)
        self.sigma_pprime=np.zeros_like(self.distance)
        self.sigma_G0=np.zeros_like(self.distance)
        self.sigma_age=np.zeros_like(self.age)
        self.sigma_logage=np.zeros_like(self.age)
        self.is_fusion=np.empty_like(self.distance)

# Model function

    def model1D(self, j):

        #Steady plug flow without melting thermal model (cf. document from Catherine)
        self.p[j]=-1+m.exp(self.pprime[j])
        self.Tf[j]=Tf(rhog*ggrav*self.thkie[j])     #FIXME: take into account temporal variations of ice thickness
        self.Tm[j]=(self.Ts+self.Tf[j])/2       #We assume first that we have melting point everywhere
        self.alpha[j]=m.sqrt(self.a[j]/365./24./3600./self.thk[j]/Kg(self.Tm[j], 1.)*rhog*cg(self.Tm[j])/2.)
        self.DeltaT[j]=self.Ts-self.Tf[j]
        self.G[j]=-self.DeltaT[j]*2*Kg(self.Tm[j], 1.)*self.alpha[j]/m.sqrt(m.pi)/erf(self.thkie[j]*self.alpha[j])
        self.is_fusion[j]=(self.G0[j]>self.G[j])
        self.G[j]=min(self.G[j], self.G0[j])
        self.m[j]=(self.G0[j]-self.G[j])*365.242*24*3600/rhog/Lf
        self.T[:,j]=self.Ts-self.G[j]*m.sqrt(m.pi)/2./Kg(self.Tm[j], 1.)/self.alpha[j]*(erf(self.alpha[j]*self.zeta[:,j]*self.thkie[j])-erf(self.alpha[j]*self.thkie[j]))
        self.T_anal[:,j]=self.T[:,j]+0.

        #Mechanical model
        self.mu[j]=self.m[j]/self.a[j]
        self.omega_D[:,j]=1-(self.p[j]+2)/(self.p[j]+1)*(1-self.zetaie[:,j])+1/(self.p[j]+1)*(1-self.zetaie[:,j])**(self.p[j]+2)	#Parrenin et al. (CP, 2007a) 2.2 (3)
        self.omega[:,j]=self.s[j]*self.zetaie[:,j]+(1-self.s[j])*self.omega_D[:,j]   #Parrenin et al. (CP, 2007a) 2.2 (2)
        self.tau[:,j]=(1-self.mu[j])*self.omega[:,j]+self.mu[j]
        self.uz[:,j]=-self.a[j]/365.242/24/3600*self.tau[:,j]

        for it in range(self.tm_iter):

            #Steady non-plug flow thermal model
            self.G=np.empty_like(self.distance)
            if self.is_fusion[j]:
                self.T[0,j]=self.Ts
                self.T[-1,j]=self.Tf[j]
                self.Btemp=np.transpose(np.zeros(np.size(self.zetagrid)-2))
                self.Atemp=1/(self.dzeta*self.thk[j])*(np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),1)+np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),-1)+np.diag(-Kg((self.T[:-2,j]+self.T[1:-1,j])/2, self.D[:-1,j])-Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),0))
                self.Atemp=self.Atemp-0.5*rhog*np.transpose([(self.D[:-1,j]+self.D[1:,j])/2*self.uz[1:-1,j]*cg(self.T[1:-1,j])])*(np.diag(np.ones(np.size(self.zetagrid)-3),-1)-np.diag(np.ones(np.size(self.zetagrid)-3),1))   #TODO:We are missing a term due to heat production by deformatio
                self.Btemp[0]=-(Kg((self.T[0,j]+self.T[1,j])/2, self.D[0,j])/self.dzeta/self.thk[j]-0.5*rhog*(self.D[0,j]+self.D[1,j])/2*cg(self.T[1,j])*self.uz[1,j])*self.Ts
                self.Btemp[-1]=-(Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j]+0.5*rhog*(self.D[-1,j]+self.D[-2,j])/2*cg(self.T[-2,j])*self.uz[-2,j])*self.Tf[j]
                self.T[1:-1,j]=np.linalg.solve(self.Atemp,self.Btemp)
                self.G[j]=-Kg((self.T[-1,j]+self.T[-2,j])/2, self.D[-1,j])*(self.T[-2,j]-self.T[-1,j])/(self.depthie[-1,j]-self.depthie[-2,j])
                self.m[j]=(self.G0[j]-self.G[j])*365.242*24*3600/rhog/Lf
                if self.G0[j]<=self.G[j]:
                    self.is_fusion[j]=False
            else:
                self.T[0,j]=self.Ts
                self.Btemp=np.transpose(np.zeros(np.size(self.zetagrid)-1))
                self.Atemp=1/(self.dzeta*self.thk[j])*(np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),1)+np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),-1)+np.diag(-Kg((self.T[:-2,j]+self.T[1:-1,j])/2, self.D[:-1,j])-Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),0))
                self.Atemp=self.Atemp-0.5*rhog*np.transpose([(self.D[:-1,j]+self.D[1:,j])/2*self.uz[1:-1,j]*cg(self.T[1:-1,j])])*(np.diag(np.ones(np.size(self.zetagrid)-3),-1)-np.diag(np.ones(np.size(self.zetagrid)-3),1))   #TODO:We are missing a term due to heat production by deformation
                vector=np.concatenate((np.zeros(np.size(self.zetagrid)-3), np.array([ Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j] - 0.5*rhog*(self.D[-1,j]+self.D[-2,j])/2*cg(self.T[-2,j])*self.uz[-2,j] ]) ))
                self.Atemp=np.concatenate(( self.Atemp, np.array([ vector ]).T ), axis=1)
                vector=np.concatenate(( np.zeros(np.size(self.zetagrid)-3), Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j] * np.array([1,-1]) ))
                self.Atemp=np.concatenate(( self.Atemp, np.array([ vector ])  ), axis=0)

                self.Btemp[0]=-(Kg((self.T[0,j]+self.T[1,j])/2, self.D[0,j])/self.dzeta/self.thk[j]-0.5*(self.D[0,j]+self.D[1,j])/2*rhog*cg(self.T[0,j])*self.uz[1,j])*self.Ts  #Is there an indice problem here?
                self.Btemp[-1]=-self.G0[j]
                self.T[1:,j]=np.linalg.solve(self.Atemp,self.Btemp)
                self.G[j]=self.G0[j]
                self.m[j]=0.
                if self.T[-1,j]>self.Tf[j]:
                    self.is_fusion[j]=True

            #Mechanical model
            self.mu[j]=self.m[j]/self.a[j]
            self.tau[:,j]=(1-self.mu[j])*self.omega[:,j]+self.mu[j]
            self.uz[:,j]=-self.a[j]/365.242/24/3600*self.tau[:,j]


        self.age_density[:,j]=np.where((self.tau[1:,j]+self.tau[:-1,j])/2>0 ,1/self.a[j]/(self.tau[1:,j]+self.tau[:-1,j])*2,np.nan)
#        toto=np.concatenate(( np.array([[ self.age_surf ]]),np.array([(self.depthie[1:,j]-self.depthie[:-1,j])*self.age_density[:,j]]) ))
        self.agesteady[:,j]=np.cumsum(np.concatenate((np.array([ self.age_surf ]),(self.depthie[1:,j]-self.depthie[:-1,j])*self.age_density[:,j] )), axis=0)

#        for j in range(np.size(self.distance)):
#            self.agesteady[:,j]=np.cumsum(np.concatenate((np.array([self.age_surf]),(self.depthie[1:,j]-self.depthie[:-1,j])/self.a[j]/(self.tau[1:,j]+self.tau[:-1,j])*2)))

#        self.agesteady[0,:]=self.age_surf
#        for i in range(1,np.size(self.zetagrid)):
#            self.agesteady[i,:]=np.where(self.tau[i,:]+self.tau[i-1,:]>0,self.agesteady[i-1,:]+(self.depthie[i,:]-self.depthie[i-1,:])/self.a/(self.tau[i,:]+self.tau[i-1,:])*2,1000000)
#            self.agesteady[i,:]=np.where(self.agesteady[i,:]<1000000,self.agesteady[i,:],1000000)

        f=interp1d(np.concatenate((np.array([-1000000000]),self.AICC2012_steadyage,np.array([1000000*self.AICC2012_steadyage[-1]]))),np.concatenate((np.array([self.AICC2012_age[0]]),self.AICC2012_age,np.array([1000000*self.AICC2012_age[-1]]))))
        self.age[:,j]=f(self.agesteady[:,j])

        return np.concatenate(( np.array([self.a[j]]),np.array([self.m[j]]),np.array([self.pprime[j]]),self.age[:,j],np.log(self.age[1:,j]),np.array([self.G0[j]]) ))

    def model(self):
        self.p=-1+np.exp(self.pprime)
        #Steady plug flow without melting thermal model (cf. document from Catherine)
        self.Tf=Tf(rhog*ggrav*self.thkie)     #FIXME: take into account temporal variations of ice thickness
#We assume first that we have melting point everywhere
        self.Tm=(self.Ts+self.Tf)/2
        self.alpha=np.sqrt(self.a/365./24./3600./self.thk/Kg(self.Tm, 1.)*rhog*cg(self.Tm)/2.)
        self.DeltaT=self.Ts-self.Tf  
        self.G=-self.DeltaT*2*Kg(self.Tm, 1.)*self.alpha/m.sqrt(m.pi)/erf(self.thkie*self.alpha)
        self.is_fusion=np.where(self.G0>self.G,True,False)
        self.G=np.where(self.is_fusion, self.G, self.G0)
        self.m=(self.G0-self.G)*365.242*24*3600/rhog/Lf
        self.T=self.Ts-self.G*m.sqrt(m.pi)/2./Kg(self.Tm, 1.)/self.alpha*(erf(self.alpha*self.zeta*self.thkie)-erf(self.alpha*self.thkie))
#        self.m=np.zeros(np.size(self.distance))
        self.T_anal=self.T+0.

        #Mechanical model
        self.mu=self.m/self.a
        #self.s=variables[2*np.size(self.distance):3*np.size(self.distance)]
        self.omega_D=1-(self.p+2)/(self.p+1)*(1-self.zetaie)+1/(self.p+1)*(1-self.zetaie)**(self.p+2)	#Parrenin et al. (CP, 2007a) 2.2 (3)
        self.omega=self.s*self.zetaie+(1-self.s)*self.omega_D   #Parrenin et al. (CP, 2007a) 2.2 (2)
        self.tau=(1-self.mu)*self.omega+self.mu
        self.uz=-self.a/365.242/24/3600*self.tau

        for it in range(self.tm_iter):
#            print it

            #Steady non-plug flow thermal model
            self.G=np.empty_like(self.distance)
            for j in range(np.size(self.distance)):
#                print j
                if self.is_fusion[j]:
                    self.T[0,j]=self.Ts
                    self.T[-1,j]=self.Tf[j]
                    self.Btemp=np.transpose(np.zeros(np.size(self.zetagrid)-2))
    #                self.Atemp=Kg(self.Tb[j])/self.dzeta/self.thkie[j]*(np.diag(np.ones(np.size(self.zetagrid)-3),1)+np.diag(np.ones(np.size(self.zetagrid)-3),-1)+np.diag(-2*np.ones(np.size(self.zetagrid)-2),0))+0.5*rhog*np.transpose([self.uz[1:-1,j]*cg(self.T[1:-1,j])])*(np.diag(np.ones(np.size(self.zetagrid)-3),1)-np.diag(np.ones(np.size(self.zetagrid)-3),-1))
    #                self.Btemp[0]=-(Kg(self.Tb[j])/self.dzeta/self.thkie[j]-cg(self.T[1,j])*rhog*self.uz[1,j])*self.Ts
    #                self.Btemp[-1]=-(Kg(self.Tb[j])/self.dzeta/self.thkie[j]+cg(self.T[-2,j])*rhog*self.uz[-2,j])*self.Tb[j]
                    self.Atemp=1/(self.dzeta*self.thk[j])*(np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),1)+np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),-1)+np.diag(-Kg((self.T[:-2,j]+self.T[1:-1,j])/2, self.D[:-1,j])-Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),0))
#                    self.Atemp=self.Atemp-0.5*rhog*np.transpose([self.uz[1:-1,j]])*(np.diag(cg(self.T[1:-2,j]),-1)-np.diag(cg(self.T[2:-1,j]),1))   #TODO:We are missing a term due to heat production by deformation + mistaken formula which is not matrician + missing relative density term?
#                    print 'shape of uz and cg',np.shape(self.uz[1:-1,j]),np.shape(cg(self.T[1:-1,j])),np.shape(self.uz[1:-1,j]*cg(self.T[1:-1,j]))
                    self.Atemp=self.Atemp-0.5*rhog*np.transpose([(self.D[:-1,j]+self.D[1:,j])/2*self.uz[1:-1,j]*cg(self.T[1:-1,j])])*(np.diag(np.ones(np.size(self.zetagrid)-3),-1)-np.diag(np.ones(np.size(self.zetagrid)-3),1))   #TODO:We are missing a term due to heat production by deformatio
#                    self.Btemp[0]=-(Kg((self.T[0,j]+self.T[1,j])/2, self.D[0,j])/self.dzeta/self.thk[j]-0.5*rhog*cg(self.T[0,j])*self.uz[1,j])*self.Ts   #Old formula with wrong indice
#                    self.Btemp[-1]=-(Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j]+0.5*rhog*cg(self.T[-1,j])*self.uz[-2,j])*self.Tf[j]   #Old formula with wrong indice
                    self.Btemp[0]=-(Kg((self.T[0,j]+self.T[1,j])/2, self.D[0,j])/self.dzeta/self.thk[j]-0.5*rhog*(self.D[0,j]+self.D[1,j])/2*cg(self.T[1,j])*self.uz[1,j])*self.Ts
                    self.Btemp[-1]=-(Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j]+0.5*rhog*(self.D[-1,j]+self.D[-2,j])/2*cg(self.T[-2,j])*self.uz[-2,j])*self.Tf[j]
                    self.T[1:-1,j]=np.linalg.solve(self.Atemp,self.Btemp)
    #                self.G[j]=Kg(self.Tb[j])*(self.T[-1,j]-self.T[-2,j])/(self.depthie[-1,j]-self.depthie[-2,j])
                    self.G[j]=-Kg((self.T[-1,j]+self.T[-2,j])/2, self.D[-1,j])*(self.T[-2,j]-self.T[-1,j])/(self.depthie[-1,j]-self.depthie[-2,j])
                    self.m[j]=(self.G0[j]-self.G[j])*365.242*24*3600/rhog/Lf
                    if self.G0[j]<=self.G[j]:
                        self.is_fusion[j]=False
                else:
                    self.T[0,j]=self.Ts
                    self.Btemp=np.transpose(np.zeros(np.size(self.zetagrid)-1))
#                    self.Atemp=1/self.dzeta/self.thk[j]*(np.diag(Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),1)+np.diag(Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),-1)+np.diag(-Kg((self.T[:-1,j]+self.T[1:,j])/2, self.D[:,j])-np.concatenate((Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),np.array([0.]))),0))  #Old buggy formulation
#                    self.Atemp=self.Atemp-0.5*rhog*np.transpose([(self.D[:,j]+self.D[:,j])/2*self.uz[1:,j]])*(np.diag(np.concatenate((cg(self.T[1:-2,j]),np.array([0.]))),-1)-np.diag(cg(self.T[2:,j]),1))  #Old buggy formulation
                    self.Atemp=1/(self.dzeta*self.thk[j])*(np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),1)+np.diag(Kg((self.T[1:-2,j]+self.T[2:-1,j])/2, self.D[1:-1,j]),-1)+np.diag(-Kg((self.T[:-2,j]+self.T[1:-1,j])/2, self.D[:-1,j])-Kg((self.T[1:-1,j]+self.T[2:,j])/2, self.D[1:,j]),0))
                    self.Atemp=self.Atemp-0.5*rhog*np.transpose([(self.D[:-1,j]+self.D[1:,j])/2*self.uz[1:-1,j]*cg(self.T[1:-1,j])])*(np.diag(np.ones(np.size(self.zetagrid)-3),-1)-np.diag(np.ones(np.size(self.zetagrid)-3),1))   #TODO:We are missing a term due to heat production by deformation
                    vector=np.concatenate((np.zeros(np.size(self.zetagrid)-3), np.array([ Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j] - 0.5*rhog*(self.D[-1,j]+self.D[-2,j])/2*cg(self.T[-2,j])*self.uz[-2,j] ]) ))
                    self.Atemp=np.concatenate(( self.Atemp, np.array([ vector ]).T ), axis=1)
                    vector=np.concatenate(( np.zeros(np.size(self.zetagrid)-3), Kg((self.T[-2,j]+self.T[-1,j])/2, self.D[-1,j])/self.dzeta/self.thk[j] * np.array([1,-1]) ))
                    self.Atemp=np.concatenate(( self.Atemp, np.array([ vector ])  ), axis=0)

                    self.Btemp[0]=-(Kg((self.T[0,j]+self.T[1,j])/2, self.D[0,j])/self.dzeta/self.thk[j]-0.5*(self.D[0,j]+self.D[1,j])/2*rhog*cg(self.T[0,j])*self.uz[1,j])*self.Ts  #Is there an indice problem here?
                    self.Btemp[-1]=-self.G0[j]
                    self.T[1:,j]=np.linalg.solve(self.Atemp,self.Btemp)
                    self.G[j]=self.G0[j]
                    self.m[j]=0.
                    if self.T[-1,j]>self.Tf[j]:
                        self.is_fusion[j]=True
#            self.is_fusion=np.where(self.G0>self.G,True,False)
#            self.G=np.where(self.is_fusion, self.G, self.G0)
#            self.m=(self.G0-self.G)*365.242*24*3600/rhog/Lf

            #Mechanical model
            self.mu=self.m/self.a
            #self.s=variables[2*np.size(self.distance):3*np.size(self.distance)]
#            self.omega_D=1-(self.p+2)/(self.p+1)*(1-self.zetaie)+1/(self.p+1)*(1-self.zetaie)**(self.p+2)	#Parrenin et al. (CP, 2007a) 2.2 (3)
#            self.omega=self.s*self.zetaie+(1-self.s)*self.omega_D   #Parrenin et al. (CP, 2007a) 2.2 (2)
            self.tau=(1-self.mu)*self.omega+self.mu
            self.uz=-self.a/365.242/24/3600*self.tau


        self.age_density=np.where((self.tau[1:,]+self.tau[:-1,])/2>0 ,1/self.a/(self.tau[1:,]+self.tau[:-1,])*2,np.nan)
        self.agesteady=np.cumsum(np.concatenate((np.array([self.age_surf*np.ones(np.size(self.distance))]),(self.depthie[1:,]-self.depthie[:-1,])*self.age_density)), axis=0)

#        for j in range(np.size(self.distance)):
#            self.agesteady[:,j]=np.cumsum(np.concatenate((np.array([self.age_surf]),(self.depthie[1:,j]-self.depthie[:-1,j])/self.a[j]/(self.tau[1:,j]+self.tau[:-1,j])*2)))

#        self.agesteady[0,:]=self.age_surf
#        for i in range(1,np.size(self.zetagrid)):
#            self.agesteady[i,:]=np.where(self.tau[i,:]+self.tau[i-1,:]>0,self.agesteady[i-1,:]+(self.depthie[i,:]-self.depthie[i-1,:])/self.a/(self.tau[i,:]+self.tau[i-1,:])*2,1000000)
#            self.agesteady[i,:]=np.where(self.agesteady[i,:]<1000000,self.agesteady[i,:],1000000)

        f=interp1d(np.concatenate((np.array([-1000000000]),self.AICC2012_steadyage,np.array([1000000*self.AICC2012_steadyage[-1]]))),np.concatenate((np.array([self.AICC2012_age[0]]),self.AICC2012_age,np.array([1000000*self.AICC2012_age[-1]]))))
        self.age=f(self.agesteady)


        return np.concatenate((self.a,self.m,self.pprime,self.age.flatten(),self.G0))

#Residuals function

    def residuals1D(self, variables1D, j):
        self.a[j]=variables1D[0]
#        print 'a: ',self.a[j]
#        self.m=variables[np.size(self.distance):2*np.size(self.distance)]
        self.pprime[j]=variables1D[1]
        if self.invert_G0:
            self.G0[j]=variables1D[2]

        self.model1D(j)
        f=interp1d(self.depth[:,j],self.age[:,j])
#        print self.age[:,j]
        self.iso_modage[:,j]=f(self.iso[:,j])
#        print self.iso_modage[:,j]
#        print 'shape iso_age and iso_sigma:', np.shape(self.iso_age),np.shape(self.iso_sigma)
        resi=(self.iso_age.flatten()-self.iso_modage[:,j])/self.iso_sigma.flatten()
#        print resi
        resi=resi[np.where(~np.isnan(resi))]
        resi=np.concatenate((resi,np.array([ (self.pprime[j]-self.pprime_prior)/self.pprime_sigma ]) ))
        if self.invert_G0:
            resi=np.concatenate((resi, np.array([ (self.G0[j]-self.G0_prior)/self.G0_sigma ]) ))
#        resi=np.append(resi,(self.pprime[j]-self.pprime_prior)/self.pprime_sigma)
#        if self.invert_G0:
#            resi=np.append(resi,(self.G0[j]-self.G0_prior)/self.G0_sigma)
#        print 'Residual: ',resi
        return resi

    def residuals(self, variables):
        self.a=variables[0:np.size(self.distance)]
#        self.m=variables[np.size(self.distance):2*np.size(self.distance)]
        self.pprime=variables[np.size(self.distance):2*np.size(self.distance)]
        if self.invert_G0:
            self.G0=variables[2*np.size(self.distance):3*np.size(self.distance)]

        age=self.model()
        for j in range(np.size(self.distance)):
            f=interp1d(self.depth[:,j],self.age[:,j])
            self.iso_modage[:,j]=f(self.iso[:,j])
        resi=(self.iso_age-self.iso_modage)/self.iso_sigma
        iso_age_flatten=self.iso_age.flatten()
        resi=resi.flatten()
        resi=resi[np.where(~np.isnan(resi))]
        resi=np.concatenate((resi,(self.pprime-self.pprime_prior)/self.pprime_sigma))
        if self.invert_G0:
            resi=np.concatenate((resi,(self.G0-self.G0_prior)/self.G0_sigma))
        return resi


#    def jacobian1D(self, j):
#        epsilon=np.sqrt(np.diag(self.hess1D))/100000000.
#        model0=self.model1D(j)
#        jacob=np.empty((np.size(self.variables1D), np.size(model0)))
#        for i in np.arange(np.size(self.variables1D)):
#            self.variables1D[i]=self.variables1D[i]+epsilon[i]
#            self.residuals1D(self.variables1D, j)
#            model1=self.model1D(j)
#            jacob[i]=(model1-model0)/epsilon[i]
#            self.variables1D[i]=self.variables1D[i]+epsilon[i]
#        self.residuals1D(self.variables1D, j)
#       return jacob

    def jacobian1D(self, j):
        epsilon=np.sqrt(np.diag(self.hess1D))/100000000.
        model0=self.model1D(j)
        jacob=np.empty((np.size(self.variables1D), np.size(model0)))
        for i in np.arange(np.size(self.variables1D)):
            self.variables1D[i]=self.variables1D[i]+epsilon[i]
            self.residuals1D(self.variables1D, j)
            model1=self.model1D(j)
            self.variables1D[i]=self.variables1D[i]-epsilon[i]
            self.residuals1D(self.variables1D, j)
            model2=self.model1D(j)
            jacob[i]=(model1-model2)/2./epsilon[i]
            self.variables1D[i]=self.variables1D[i]+epsilon[i]
        self.residuals1D(self.variables1D, j)

        return jacob


    def jacobian(self):
        epsilon=np.sqrt(np.diag(self.hess))/100000000.
        model0=self.model()
        jacob=np.empty((np.size(self.variables), np.size(model0)))
        for i in np.arange(np.size(self.variables)):
            self.variables[i]=self.variables[i]+epsilon[i]
            self.residuals(self.variables)
            model1=self.model()
            jacob[i]=(model1-model0)/epsilon[i]
            self.variables[i]=self.variables[i]-epsilon[i]
        model0=self.model()

        return jacob



    def accu_layers(self):
        self.accusteady_layer=np.zeros((self.nbiso,np.size(self.distance)))
        for j in range(np.size(self.distance)):
            f=interp1d(self.depth[:,j],self.age[:,j])
            self.iso_modage[:,j]=f(self.iso[:,j])
            self.accusteady_layer[0,j]=self.a[j]*(self.iso_modage[0,j]-self.age_surf)/(self.iso_age[0]-self.age_surf)
            self.accusteady_layer[1:,j]=self.a[j]*(self.iso_modage[1:,j]-self.iso_modage[:-1,j])/(self.iso_age[1:]-self.iso_age[:-1]).flatten()

        return

    def sigma1D(self,j):
        jacob=self.jacobian1D(j)


        index=0
        c_model=np.dot(np.transpose(jacob[:,index:index+1]),np.dot(self.hess1D,jacob[:,index:index+1]))
        self.sigma_a[j]=np.sqrt(np.diag(c_model))[0]
        index=index+1
        c_model=np.dot(np.transpose(jacob[:,index:index+1]),np.dot(self.hess1D,jacob[:,index:index+1]))
        self.sigma_m[j]=np.sqrt(np.diag(c_model))[0]
        index=index+1
        c_model=np.dot(np.transpose(jacob[:,index:index+1]),np.dot(self.hess1D,jacob[:,index:index+1]))
        self.sigma_pprime[j]=np.sqrt(np.diag(c_model))[0]
        index=index+1
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.age[:,j])]),np.dot(self.hess1D,jacob[:,index:index+np.size(self.age[:,j])]))
        self.sigma_age[:,j]=np.sqrt(np.diag(c_model))
#        print np.size(self.sigma_age)
        index=index+np.size(self.age[:,j])
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.age[1:,j])]),np.dot(self.hess1D,jacob[:,index:index+np.size(self.age[1:,j])]))
        self.sigma_logage[1:,j]=np.sqrt(np.diag(c_model))
        self.sigma_logage[0,j]=np.nan
        index=index+np.size(self.age[1:,j])
        c_model=np.dot(np.transpose(jacob[:,index:index+1]),np.dot(self.hess1D,jacob[:,index:index+1]))
        self.sigma_G0[j]=np.sqrt(np.diag(c_model))[0]


        return

    def sigma(self):
        jacob=self.jacobian()

        index=0
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.a)]),np.dot(self.hess,jacob[:,index:index+np.size(self.a)]))
        self.sigma_a=np.sqrt(np.diag(c_model))
        index=index+np.size(self.a)
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.m)]),np.dot(self.hess,jacob[:,index:index+np.size(self.m)]))
        self.sigma_m=np.sqrt(np.diag(c_model))
        index=index+np.size(self.m)
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.p)]),np.dot(self.hess,jacob[:,index:index+np.size(self.p)]))
        self.sigma_pprime=np.sqrt(np.diag(c_model))
        index=index+np.size(self.p)
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.age)]),np.dot(self.hess,jacob[:,index:index+np.size(self.age)]))
        self.sigma_age=np.sqrt(np.diag(c_model))
#        print np.size(self.sigma_age)
        self.sigma_age=np.reshape(self.sigma_age,(np.size(self.zetagrid),np.size(self.distance)))
        index=index+np.size(self.age)
        c_model=np.dot(np.transpose(jacob[:,index:index+np.size(self.G0)]),np.dot(self.hess,jacob[:,index:index+np.size(self.G0)]))
        self.sigma_G0=np.sqrt(np.diag(c_model))

        return

#Plotting the raw and interpolated radar datasets
    def data_display(self):
        plt.figure('Data')
        plt.plot(self.distance_raw, self.thk_raw, label='raw bedrock', color='b', linewidth=2)
        plt.plot(self.distance, self.thk, label='interpolated bedrock', color='k', linewidth=2)
        for i in range(self.nbiso):
            if i==0:
                plt.plot(self.distance_raw, self.iso_raw[i,:], color='b', label='raw isochrones')
                plt.plot(self.distance, self.iso[i,:], color='k', label='interpolated isochrones')
            else:
                plt.plot(self.distance_raw, self.iso_raw[i,:], color='b')
                plt.plot(self.distance, self.iso[i,:], color='k')
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        plt.legend(loc=1)
        x1,x2,y1,y2 = plt.axis()
        plt.axis((x1,x2,y2,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        pp=PdfPages(self.label+'Data.pdf')
        pp.savefig(plt.figure('Data'))
        pp.close()

#Plot of the model results

    def model_display(self):

        plt.figure('Model steady')
        plt.plot(self.distance, self.thk, label='obs. bedrock', color='k', linewidth=2)
        for i in range(self.nbiso):
            if i==0:
                plt.plot(self.distance, self.iso[i,:], color='k', label='obs. isochrones')
            else:
                plt.plot(self.distance, self.iso[i,:], color='k')
        levels=np.arange(0, 1600000, 100000)
        levels_color=np.arange(0, 1500000, 10000)
        plt.contourf(self.dist, self.depth, self.agesteady, levels_color)
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        plt.legend(loc=2)
        cb=plt.colorbar()
        cb.set_ticks(levels)
        cb.set_ticklabels(levels)
        cb.set_label('Modeled steady age')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),y2,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        pp=PdfPages(self.label+'Model-steady.pdf')
        pp.savefig(plt.figure('Model steady'))
        pp.close()


        fig=plt.figure('Model')
        plotmodel = fig.add_subplot(111, aspect=self.aspect)
        plt.plot(self.distance, self.thk, color='k', linewidth=2)
        for i in range(self.nbiso):
            if i==0:
                plt.plot(self.distance, self.iso[i,:], color='w', label='obs. isochrones')
            else:
                plt.plot(self.distance, self.iso[i,:], color='w')
        levels=np.arange(0, 1600000, 100000)
        levels_color=np.arange(0, 1500000, 10000)
        plt.contourf(self.dist, self.depth, self.age, levels_color)
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        if self.is_legend:
            leg=plt.legend(loc=1)
            frame=leg.get_frame()
            frame.set_facecolor('0.75')
        cb=plt.colorbar()
        cb.set_ticks(levels)
        cb.set_ticklabels(levels)
        cb.set_label('Modeled age (yr)')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),self.max_depth,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        if self.settick=='manual':
            plotmodel.set_xticks(np.arange(self.min_tick,self.max_tick+1.,self.delta_tick))
        pp=PdfPages(self.label+'Model.pdf')
        pp.savefig(plt.figure('Model'))
        pp.close()

        fig = plt.figure('Model confidence interval')
        plotmodelci = fig.add_subplot(111, aspect=self.aspect)
        plt.plot(self.distance, self.thk, color='k', linewidth=2)
        for i in range(self.nbiso):
            if i==0:
                plt.plot(self.distance, self.iso[i,:], color='w', label='obs. isochrones')
            else:
                plt.plot(self.distance, self.iso[i,:], color='w')
#        levels=np.arange(0, 200000, 20000)
        levels_log=np.arange(2, 6, 0.1)
        levels=np.power(10, levels_log)
#        levels=np.array([100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000, 250000])
        plt.contourf(self.dist, self.depth, self.sigma_age, levels, norm = LogNorm())
        cb=plt.colorbar()
        cb.set_label('Modeled age confidence interval (yr)')
#        levels_labels=np.where( np.equal(np.mod(np.arange(2,6,0.1), 1), 0) , np.power(10., np.arange(2,6,0.1)), "" ) 
        levels_labels=np.array([])
        for i in np.arange(2,6,1):
            levels_labels=np.concatenate((levels_labels, np.array([10**i, '', '', '', '', '', '', '', '']) ))
        cb.set_ticklabels(levels_labels)
        levels_ticks=np.concatenate(( np.arange(100, 1000, 100), np.arange(1000, 10000, 1000), np.arange(10000, 100000, 10000), np.arange(100000, 600000, 100000) )) 
        cb.set_ticks(levels_ticks)
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        if self.is_legend:
            leg=plt.legend(loc=1)
            frame=leg.get_frame()
            frame.set_facecolor('0.75')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),self.max_depth,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        if self.settick=='manual':
            plotmodelci.set_xticks(np.arange(self.min_tick,self.max_tick+1.,self.delta_tick))
        pp=PdfPages(self.label+'Model-confidence-interval.pdf')
        pp.savefig(plt.figure('Model confidence interval'))
        pp.close()


        plt.figure('Thinning')
        plt.plot(self.distance, self.thk, label='obs. bedrock', color='k', linewidth=2)
        for i in range(self.nbiso):
            if i==0:
                plt.plot(self.distance, self.iso[i,:], color='k', label='obs. isochrones')
            else:
                plt.plot(self.distance, self.iso[i,:], color='k')
        plt.contourf(self.dist, self.depth, self.tau)
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        plt.legend(loc=2)
        cb=plt.colorbar()
        cb.set_label('Modeled thinning')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),y2,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        pp=PdfPages(self.label+'Thinning.pdf')
        pp.savefig(plt.figure('Thinning'))
        pp.close()

        fig=plt.figure('Temperature')
        plt.plot(self.distance, self.thk, label='obs. bedrock', color='k', linewidth=2)
        plt.plot(self.distance, np.where(self.is_fusion,np.nan,self.thk), color='b', linewidth=4)
        plt.contourf(self.dist, self.depth, self.T)
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([0., 3200.])
            plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('depth (m)')
        plt.legend(loc=2)
        cb=plt.colorbar()
        cb.set_label('Modeled temperature (K)')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),y2,0))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        pp=PdfPages(self.label+'Temperature.pdf')
        pp.savefig(plt.figure('Temperature'))
        pp.close()
#        plt.close(fig)

#        fig = plt.figure('Accumulation history')
        lines=[zip(self.distance, self.accusteady_layer[i,:]) for i in range(self.nbiso)]
        z=(self.iso_age.flatten()[1:]+self.iso_age.flatten()[:-1])/2
        z=np.concatenate(( np.array([(self.age_surf+self.iso_age.flatten()[0])/2]) , z ))
        fig, ax = plt.subplots()
        lines = LineCollection(lines, array=z, cmap=plt.cm.rainbow, linewidths=2)
        ax.add_collection(lines)
        ax.autoscale()
        cb=fig.colorbar(lines)
        cb.set_label('Average layer age (yr)')
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
        plt.ylabel('steady accumulation (ice-cm/yr)')
        if self.reverse_distance:
            plt.gca().invert_xaxis()


        pp=PdfPages(self.label+'AccumulationHistory.pdf')
        pp.savefig(fig)
        pp.close()
#        plt.close(fig)



#Plot of the parameters

    def parameters_display(self):
        f=plt.figure('Parameters')
#        f=plt.figure('Parameters', figsize=(4,6))
        plotpara = plt.subplot(311, aspect=self.aspect/(self.accu_max-self.accu_min)*self.max_depth/3)
        plt.plot(self.distance, self.a*100, label='accumulation', color='b')
        plt.plot(self.distance, (self.a-self.sigma_a)*100, color='b', linestyle='--')
        plt.plot(self.distance, (self.a+self.sigma_a)*100, color='b', linestyle='--')
        plt.ylabel('accu. (cm/yr)')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance), self.accu_min, self.accu_max))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([self.accu_min, self.accu_max])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
#        plt.legend()
        if self.settick=='manual':
            plotpara.set_xticks(np.arange(self.min_tick,self.max_tick+1.,self.delta_tick))
        plotpara=plt.subplot(312, aspect=self.aspect/(self.melting_max-self.melting_min)*self.max_depth/3)
        plt.plot(self.distance, self.m*1000, label='melting', color='r')
        plt.plot(self.distance, (self.m-self.sigma_m)*1000, color='r', linestyle='--')
        plt.plot(self.distance, (self.m+self.sigma_m)*1000, color='r', linestyle='--')
        plt.ylabel('melting (mm/yr)')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),self.melting_min,self.melting_max))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([self.melting_min, self.melting_max])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
        plotpara.yaxis.tick_right()
        plotpara.yaxis.set_label_position('right')
        if self.settick=='manual':
            plotpara.set_xticks(np.arange(self.min_tick,self.max_tick+1.,self.delta_tick))
        plotpara=plt.subplot(313, aspect=self.aspect/(m.log(self.p_max+1)-m.log(self.p_min+1))*self.max_depth/3)
        plt.plot(self.distance, self.pprime, label='p', color='g')
        plt.plot(self.distance, self.pprime-self.sigma_pprime, color='g', linestyle='--')
        plt.plot(self.distance, self.pprime+self.sigma_pprime, color='g', linestyle='--')
        plt.ylabel('p+1 parameter')
        if self.is_EDC:
            EDC_x=np.array([self.distance_EDC, self.distance_EDC])
            EDC_y=np.array([m.log(self.p_min), m.log(self.p_max)])
            if self.EDC_line_dashed==True:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2, linestyle='--')
            else:
                plt.plot(EDC_x, EDC_y, label='EDC ice core', color='r', linewidth=2)
#        plotpara.set_yticks(np.log(np.arange(1.,11.)))
        plotpara.set_yticks(np.log(np.concatenate((np.arange(1.,10.),10.*np.arange(1.,10.) )) ))
        labels=["1", "", "", "", "", "", "", "", "", "10"]
        plotpara.set_yticklabels(labels)
        if self.settick=='manual':
            plotpara.set_xticks(np.arange(self.min_tick,self.max_tick+1.,self.delta_tick))
        x1,x2,y1,y2 = plt.axis()
        plt.axis((min(self.distance),max(self.distance),m.log(self.p_min+1),m.log(self.p_max+1)))
        if self.reverse_distance:
            plt.gca().invert_xaxis()
        if self.is_NESW:
            plt.xlabel('<NE - distance (km) - SW>')
        else:
            plt.xlabel('distance (km)')
#        plt.legend()
        f.subplots_adjust(hspace=0)
        plt.setp([a.get_xticklabels() for a in f.axes[:-1]], visible=False)
        pp=PdfPages(self.label+'Parameters.pdf')
        pp.savefig(plt.figure('Parameters'))
        pp.close()

        if self.invert_G0:
            plt.figure('Geothermal heat flux')
            plt.plot(self.distance, self.G0*1000, label='G0', color='k')
            plt.plot(self.distance, (self.G0-self.sigma_G0)*1000, color='k', linestyle='--')
            plt.plot(self.distance, (self.G0+self.sigma_G0)*1000, color='k', linestyle='--')
            plt.ylabel('$G_0$ (mW/m$^2$)')
        if self.reverse_distance:
            plt.gca().invert_xaxis()
#            plt.yaxis.tick_right()
#            plt.yaxis.set_label_position('right')
            pp=PdfPages(self.label+'GeothermalHeatFlux.pdf')
            pp.savefig(plt.figure('Geothermal heat flux'))
            pp.close()


    def parameters_save(self):
        output=np.vstack((self.LON, self.LAT, self.distance,self.a, self.sigma_a, self.accusteady_layer))
        header='#LON\tLAT\tdistance(km)\taccu(ice-m/yr)\tsigma_accu'
        header=header+'\tlayer'+str(int((self.iso_age[0]+self.age_surf)/2000))+'kyr'
        for i in range(self.nbiso-1):
            header=header+'\tlayer'+str(int((self.iso_age[i+1]+self.iso_age[i])/2000))+'kyr'
        header=header+'\n'
        with open(self.label+'a.txt','w') as f:
            f.write(header)
            np.savetxt(f,np.transpose(output), delimiter="\t") 
        output=np.vstack((self.LON, self.LAT, self.distance,self.m, self.sigma_m))
        with open(self.label+'m.txt','w') as f:
            f.write('#LON\tLAT\tdistance(km)\tmelting(ice-m/yr)\tsigma_melting\n')
            np.savetxt(f,np.transpose(output), delimiter="\t") 
        output=np.vstack((self.LON, self.LAT, self.distance,self.pprime, self.sigma_pprime))
        with open(self.label+'pprime.txt','w') as f:
            f.write('#LON\tLAT\tdistance(km)\tpprime\tsigma_pprime\n')
            np.savetxt(f,np.transpose(output), delimiter="\t") 
        output=np.vstack((self.LON, self.LAT, self.distance,self.G0, self.sigma_G0))
        with open(self.label+'G0.txt','w') as f:
            f.write('#LON\tLAT\tdistance(km)\tG0\tsigma_G0\n')
            np.savetxt(f,np.transpose(output), delimiter="\t") 

    def bot_age_save(self):
        output=np.vstack((self.LON, self.LAT, self.distance,self.agebot,self.sigmaagebot,np.exp(np.log(self.agebot)-2*self.sigmalogagebot) ))
        with open(self.label+'agebottom.txt','w') as f:
            f.write('#LON\tLAT\tdistance(km)\tage(yr-b1950)\tsigma(yr)\tage-min(yr-b1950)\n')
            np.savetxt(f,np.transpose(output), delimiter="\t") 

    def EDC(self):
        f=interp1d(self.distance,self.age)
        age_EDC=f(self.distance_EDC)
        g=interp1d(self.distance,self.sigma_age)
        sigmaage_EDC=g(self.distance_EDC)
        h=interp1d(self.distance,self.depth)
        depth_EDC=h(self.distance_EDC)
        print 'Thickness at EDC is:',depth_EDC[-1]
        i=interp1d(depth_EDC,age_EDC)
        age_EDC_bot=i(max(depth_EDC)-60)
        j=interp1d(depth_EDC,sigmaage_EDC)
        sigmaage_EDC_bot=j(max(depth_EDC)-60)
        print 'Age at EDC at 3200 m depth is: ',age_EDC_bot,'+-',sigmaage_EDC_bot
        f=interp1d(self.distance,self.p)
        p_EDC=f(self.distance_EDC)
        print 'p parameter at EDC is: ', p_EDC
        f=interp1d(self.distance,self.a)
        a_EDC=f(self.distance_EDC)
        print 'accumulation at EDC is: ', a_EDC
        f=interp1d(self.distance,self.m)
        m_EDC=f(self.distance_EDC)
        print 'melting at EDC is: ', m_EDC

        readarray=np.loadtxt(self.label+'temperatures_EDC.txt')
        datatempEDC_depth=readarray[:,0]
        datatempEDC_temp=readarray[:,1]+273.15
        f=interp1d(self.distance,self.T)
        temp_EDC=f(self.distance_EDC)
        f=interp1d(self.distance,self.T_anal)
        temp_anal_EDC=f(self.distance_EDC)
        plt.figure('Temperature at EDC')
        plt.plot(temp_EDC, depth_EDC, label='model')
        plt.plot(temp_anal_EDC, depth_EDC, label='analytical solution')
        plt.plot(datatempEDC_temp, datatempEDC_depth, label='data')
        plt.ylabel('depth (m)')
        plt.xlabel('temperature (K)')
        x1,x2,y1,y2 = plt.axis()
        plt.axis((x1,x2,y2,0.))
        plt.legend()
        pp=PdfPages(self.label+'temperatures_EDC.pdf')
        pp.savefig(plt.figure('Temperature at EDC'))
        pp.close()

    def max_age(self):
        self.agebot=np.empty_like(self.distance)
        self.sigmaagebot=np.empty_like(self.distance)
        self.sigmalogagebot=np.empty_like(self.distance)
        for j in range(np.size(self.distance)):
            f=interp1d(self.depth[:,j],self.age[:,j])
            self.agebot[j]=f(max(self.depth[:,j])-60)
            g=interp1d(self.depth[:,j],self.sigma_age[:,j])
            self.sigmaagebot[j]=g(max(self.depth[:,j])-60)
            h=interp1d(self.depth[1:,j],self.sigma_logage[1:,j])
            self.sigmalogagebot[j]=h(max(self.depth[:,j])-60)
        j=np.argmax(self.agebot)
        self.agemax=max(self.agebot)
        self.sigmaagemax=self.sigmaagebot[j]
        self.distanceagemax=self.distance[j]
        f=interp1d(self.distance_raw,self.LON_raw)
        g=interp1d(self.distance_raw,self.LAT_raw)
        self.LONagemax=f(self.distanceagemax)
        self.LATagemax=g(self.distanceagemax)
        print 'Maximum age is ',self.agemax,'+-',self.sigmaagemax
        print 'It occurs at a distance of ',self.distanceagemax,' km, with coordinates ',self.LONagemax,', ',self.LATagemax        





#Main
RLlabel=sys.argv[1]
if RLlabel[-1]!='/':
    RLlabel=RLlabel+'/'
print 'Radar line is: ',RLlabel
print 'Creation of the radar line'
RL=RadarLine(RLlabel)
print 'Initialization of radar line'
RL.init()
print 'Data display'
RL.data_display()
if RL.opt_method=='leastsq':
    print 'Optimization by leastsq'
    if RL.invert_G0:
        RL.variables=np.concatenate((RL.a,RL.pprime,RL.G0))
    else:
        RL.variables=np.concatenate((RL.a,RL.pprime))
#        self.variables=np.concatenate((self.a,self.m,self.s))
    RL.variables,RL.hess,infodict,mesg,ier=leastsq(RL.residuals, RL.variables, full_output=1)
    print mesg
    RL.residuals(RL.variables)
    print 'Calculation of confidence intervals'
    if RL.calc_sigma==False:
        RL.hess=np.zeros((np.size(RL.variables),np.size(RL.variables)))
    RL.sigma()
elif RL.opt_method=='none':
    if RL.invert_G0:
        RL.variables=np.concatenate((RL.a,RL.pprime,RL.G0))
    else:
        RL.variables=np.concatenate((RL.a,RL.pprime))
    print 'No optimization'
    RL.residuals(RL.variables)
elif RL.opt_method=='none1D':
    print 'Forward model 1D'
    for j in range(np.size(RL.distance)):
        if RL.invert_G0:
            RL.variables1D=np.array([ RL.a[j],RL.pprime[j],RL.G0[j] ])
        else:
            RL.variables1D=np.array([ RL.a[j],RL.pprime[j] ])
        RL.residuals1D(RL.variables1D,j)
elif RL.opt_method=='leastsq1D':
    print 'Optimization by leastsq1D'    
    for j in range(np.size(RL.distance)):
#    for j in range(1):
        print 'index along the radar line: ', j
        if RL.invert_G0:
            RL.variables1D=np.array([ RL.a[j],RL.pprime[j],RL.G0[j] ])
        else:
            RL.variables1D=np.array([ RL.a[j],RL.pprime[j] ])
        RL.variables1D,RL.hess1D,infodict,mesg,ier=leastsq(RL.residuals1D, RL.variables1D, args=(j), full_output=1)
        RL.residuals1D(RL.variables1D,j)
        if RL.calc_sigma==False:
          RL.hess1D=np.zeros((np.size(RL.variables1D),np.size(RL.variables1D)))
#        print RL.hess1D
        RL.sigma1D(j)
#    RL.distance=RL.distance[np.where(RL.distance==RL.distance[0])]
#    RL.a=RL.a[np.where(RL.distance==RL.distance[0])]
#    RL.pprime=RL.pprime[np.where(RL.distance==RL.distance[0])]
#    RL.G0=RL.G0[np.where(RL.distance==RL.distance[0])]
#    RL.depthie=RL.depthie[:,np.where(RL.distance==RL.distance[0])]
#    if RL.invert_G0:
#        RL.variables=np.concatenate((RL.a,RL.pprime,RL.G0))
#    else:
#        RL.variables=np.concatenate((RL.a,RL.pprime))
##        self.variables=np.concatenate((self.a,self.m,self.s))
#    print 'Optimization by leastsq-1D'
#    RL.variables,RL.hess,infodict,mesg,ier=leastsq(RL.residuals, RL.variables, full_output=1)
#    print mesg
else:
    print RL.opt_method,': Optimization method not recognized.'
    quit()
print 'recalculating forward model'
#RL.model()

RL.accu_layers()





print 'Model display'
RL.model_display()
print 'parameters display'
RL.parameters_display()
RL.parameters_save()
if RL.is_EDC:
    RL.EDC()
RL.max_age()
RL.bot_age_save()
print 'Program execution time: ', time.time() - start_time, 'seconds' 
