#%% Notater
"""

6.2
1. Definer systemets grenser. Alle fysiske systemer virker i interaksjon med andre systemer.
Det er derfor nødvendig å bestemme grensene for systemene før vi kan begynne å utvikle en matematisk modell
for systemet. Men i de fleste tilfeller blir avgrensningene helt naturlig.

2. Gjør forenklede antakelser. Et eksempel er å anta at temperaturen i en tank er lik overalt, dvs. at
det er homogene forhold

3. Bruk balanseloven for fysiske balanser i systemet. Og angi eventuelle tileggsbetingelser.
Balanseloven lyder:
    
Endring av mengde pr. tid i systemet er lik netto mengdeinnstrømning.

s. 411: Ved såkalt hardware-in-the-loop-testing består deler av det simulerte reguleringssystemet av fysiske,
virkelig komponenter. Det er vanligvis selve regulatorenheten, men også aktuatoren og sensoren kan være
fysiske komponenter.

"""

#%% Biblioteker

import numpy as np
import math
import matplotlib.pyplot as plt
import time
import random

#%% Instrument parameter

maksMåleAvvikNivå = 0 # [%]
maksMåleAvvikStrømning = 0 # [%]


#%% Simulation Time Settings

t_start = 0  # [s] 
t_stop = 60*60 # [s] 

#%% Signal parameter

u_min = 0 # [mA]
u_max = 16 # [mA]
u_range = u_max - u_min # [mA] 

#%% Reservoir parameter

reservoir_h_max = 7 # [m]
reservoir_h_min = 0 # [m]
reservoir_radius = 11 # [m]
reservoir_h_init = 2.8 # [m]

#%% Pumpe parameter

pumpe_q_max = 0.033 # [m^3/s] - Volumetrisk strømning ved maks pådrag. Funnet ved 120m^3 / 60s*60s
pumpe_q_min = 0 # [m^3/s] - Volumetrisk strømning ved 4 mA
pumpe_q_init = 0.015 # [m^3/s] - Volumetrisk strømning ved første iterasjon | funnet ved totalstrømning fra begge pumpene / timer / 60*60
# 27.01.23 En forenklet versjon som ikke tar for seg mottrykk (net head) i røret og antatt linear pumpekurve

def ReturnK_p(pumpe_q_max, u_range):
    k_p = (pumpe_q_max - pumpe_q_min) / u_range
    return k_p

k_p = ReturnK_p(pumpe_q_max, u_range) # Forholdet mellom pådragssignal og volumetrisk strømning


#%% Innløpsventil parameter

C_v1 = 0.005 # [x] Valve flow coefficient


#%% Utløpsventil parameter

C_v2 = 0.005 # [x] Valve flow coefficient

#%% PI(D)-regulator parameter

Kpu = 40 # Kritisk Forsterkning
Pu = 350 # [s] Kritisk Periode

P = Kpu * 0.25 # proporsjonal forsterkning | ZN Relaxed
I = Pu * 1.25 # Integraltid | ZN Relaxed
D = 0 # Derivattid
u_man = 4.056 # Manuelt pådrag | Stabiliserer seg på 40% ved 4.056 i pådrag

settpunkt = 2.8 # Setpunkt i tanken | 40% i en 7m høy tank
# her går det an å lage en formel for utregning fra h [m] til h [%]

outer_loop_modus = "auto"

# %% Initialization of time delay

t_delay = 24
u_delayed_init = 0
N_delay = int(round(t_delay/1)) + 1
delay_array = np.zeros(N_delay) + u_delayed_init

#%% Klasser 

class DataLagring:
    def __init__(self, t, h_t, f_in_t, f_out_t, settpunkt):
        self.t = t # Blir brukt som tid og indeks
        self.h_t = h_t # Høyden i bassenget som funksjon av tid
        self.f_in_t = f_in_t # Flow in som funksjon av tid, fått av pump.Flow()
        self.f_out_t = f_out_t # f_out_t # flow ut som funksjon av tid, fått av Reservoir.FlowOut()
        self.settpunkt = settpunkt
        self.u = pumpe_q_init # Muligens feil
        
        # Arrays til plotting | simulering
        
        self.t_array = np.zeros(t)
        self.h_t_array = np.zeros(t)
        self.f_in_t_array = np.zeros(t)
        self.f_out_t_array = np.zeros(t)
        self.settpunkt_array = np.zeros(t)
        self.u_array = np.zeros(t)
        self.e_array = np.zeros(t)
    

class Reservoir:
    def __init__(self, h_max, h_min, radius, h_init):
        
        self.h_max = h_max
        self.h_min = h_min
        self.radius = radius
        self.areal = self.Areal()
        
        self.h = h_init
        
        # Avgrens min og maks nivå i tank
        self.h = np.clip(self.h, self.h_min, self.h_max)
        
        self.h_prosent = (self.h/self.h_max)*100
        
        # denne er for GIVAS 09:10 01.02.2023 - 09:10 02.02.2023
        self.DynamiskForbruk = [0, 0.003425, 0.003425, 0, 0, 0, 0, 0.06, 0.06, 0, 0, 0.0043, 0, 0, 0, 0, 0,0,0,0,0,0,0,0]
        # Her må det gå an å lage en smartere metode for å finne dynamisk forbruk
        
    def Areal(self):
        reservoir_areal = math.pi*self.radius**2
        return reservoir_areal
    
    def StatiskForbruk(self):
        flowOut = C_v2 * np.sqrt(self.h)
        return flowOut
        

class Pumpe:
    def __init__(self, K_p, u_min, u_max, u):
        
        self.K_p = K_p # [%] forsterkning
        self.u = u # [mA] pådragssignal
        self.u_max = u_max # [mA]
        self.u_min = u_min # [mA]

    def FlowIn(self):
        flowIn = self.K_p * self.u
        return flowIn # [m^3/s]


class Regulator:
    def __init__(self, settpunkt, prosessverdi, P, I, D, u_man, modus):
        
        self.settpunkt = settpunkt
        self.prosessverdi = prosessverdi
        self.P = P
        self.I = I
        self.D = D
        self.u_man = u_man
        self.modus = modus.upper() # ".upper()" forhindrer syntax error ved store og små bokstaver
        
        self.u_i_forrige = u_man
        
        self.e = self.Error()
        self.u = self.Pådrag()
        
    def Error(self):
        e = self.settpunkt - self.prosessverdi
        return e
    
    
    def Pådrag(self):
        if self.modus == "AUTO":
            # Bidrag fra proporsjonalleddet
            u_p = self.P * self.e
            
            # Bidraget fra integralleddet
            u_i = ((self.P / self.I) * self.e) + self.u_i_forrige
            
            # Regn ut total total forsterkning
            u = u_p + u_i # u_d | ikke implementert
            
            #Oppdater u_i_forrige + antiwindup
            if u > 16:
                self.u_i_forrige = self.u_i_forrige
            elif u < 0:
                self.u_i_forrige = self.u_i_forrige
            else:   
                self.u_i_forrige = u_i            
            
            
        elif self.modus == "MAN":
            # Regulatoren er nå i manuell modus
            u = self.u_man
            
        else:
            # Feilmelding
            print("Vennligst skriv MAN eller AUTO på kodelinje: 88")
            
        # Begrens pådragssignal til gitte rammer
        u = np.clip(u, u_min, u_max)
        return u

class Instrument:
    def __init__(self, prosessverdi, måleavvik):
        
        self.prosessverdi = prosessverdi
        self.måleavvik = måleavvik
        
        def PVstøy(self):
            pass


class Nivåmåler(Instrument):
    def PVstøy(self):
        PVavvik = (self.prosessverdi * self.måleavvik) / 100 # +- 0.5 [%]
        PVstøy = random.uniform(self.prosessverdi - PVavvik, self.prosessverdi + PVavvik)
        return PVstøy


class Strømningsmåler(Instrument):
    def PVstøy(self):
        PVavvik = (self.prosessverdi * self.måleavvik) / 100 # +- 0.5 [%]
        PVstøy = random.uniform(self.prosessverdi - PVavvik, self.prosessverdi + PVavvik)
        return PVstøy


#%% Opprett objekter av klassene

mittReservoir = Reservoir(reservoir_h_max, reservoir_h_min, reservoir_radius, reservoir_h_init)
minRegulator = Regulator(settpunkt, mittReservoir.h, P, I, D, u_man, outer_loop_modus)
minPumpe = Pumpe(k_p, u_min, u_max, minRegulator.Pådrag())
minDataLagring = DataLagring(t_stop, mittReservoir.h, minPumpe.FlowIn(), mittReservoir.StatiskForbruk(), minRegulator.settpunkt)
minNivåmåler = Nivåmåler(mittReservoir.h, maksMåleAvvikNivå)
minStrømningsmåler = Strømningsmåler(minPumpe.FlowIn(), maksMåleAvvikStrømning)

#%% Program-loop
 
# Denne løkken simulerer fullt innløp
for i in range (t_delay):
    delay_array[i] = 0.008365 # Denne verdien er funnet ved å se på utstrømningen ved 2.8m høyde i tanken

for t in range (t_start, t_stop):
    
    # forsinker innstrømning i tanken med 120 iterasjoner (minutter) | bare valgt et tall her
    f_in_delayed = delay_array[-1]
    delay_array[1:] = delay_array[0:-1]
    delay_array[0] = minPumpe.FlowIn()

    
    # dh_dt = f_in - f_out / A
    dh_dt = (f_in_delayed*60 - mittReservoir.StatiskForbruk()*60) / mittReservoir.Areal() # | *60 for minutter istedet for sekunder
    
    # Mitt reservoir.h oppdaterer høyden i tanken per iterasjon
    mittReservoir.h += dh_dt
    
    # Måler nivå med Nivåmåler
    minNivåmåler.prosessverdi = mittReservoir.h
    
    # Oppdater regulatorens PV | uten/med støy
    #minRegulator.prosessverdi = minNivåmåler.PVstøy()
    minRegulator.prosessverdi = minNivåmåler.prosessverdi
    
    # Oppdater error
    minRegulator.e = minRegulator.Error()
    
    # Generer nytt pådrag til pumpa
    minPumpe.u = minRegulator.Pådrag()
    
    
    #Sprang i setpunkt for tuning av PID-parameter
    if t == 200:
        minRegulator.settpunkt = minRegulator.settpunkt * 1.1
    

    # Lagring av verdier til Datalagringsklassen
    minDataLagring.t_array[t] = t
    minDataLagring.h_t_array[t] = minNivåmåler.prosessverdi
    minDataLagring.f_in_t_array[t] = f_in_delayed
    minDataLagring.f_out_t_array[t] = mittReservoir.StatiskForbruk()
    minDataLagring.settpunkt_array[t] = minRegulator.settpunkt
    minDataLagring.u_array[t] = minRegulator.Pådrag()
    minDataLagring.e_array[t] = minRegulator.e


#%% plotting

plt.close('all')
plt.figure("Plot")

plt.subplot(3,1,1)
plt.plot(minDataLagring.t_array, minDataLagring.h_t_array, label = "Prosessverdi")
plt.plot(minDataLagring.t_array, minDataLagring.settpunkt_array, 'r', label ='Settpunkt')
plt.legend()
plt.grid()
#plt.axis([t_start, t_stop, mittReservoir.h_min, mittReservoir.h_max])
plt.title("Nivå i tank")
plt.ylabel("level [m]")

plt.subplot(3,1,2)
plt.plot(minDataLagring.t_array, minDataLagring.f_in_t_array, label = "Innstrømning")
plt.plot(minDataLagring.t_array, minDataLagring.f_out_t_array, label = "Utstrømning")
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, pumpe_q_min - 0.001, pumpe_q_max + 0.001]) # +- 0.001 for å se verdien i plottet
plt.title("Inn-/utstrømning")
plt.ylabel("Volumstrømning [m^3/s]")

plt.subplot(3,1,3)
plt.plot(minDataLagring.t_array, minDataLagring.u_array, label = "Pumpepådrag")
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, u_min - 1, u_max + 1]) # +- 1 for å se verdien i plottet
plt.title("Pumpepådrag")
plt.xlabel("Time [s]")
plt.ylabel("Pådrag [mA]")

plt.show()