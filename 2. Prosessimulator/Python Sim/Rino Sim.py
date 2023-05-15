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

s. 411: Ved såkalt hardware-in-the-oop-testing består deler av det simulerte reguleringssystemet av fysiske,
virkelig komponenter. Det er vanligvis selve regulatorenheten, MEN OGSÅ AKTUATOREN OG SENSOREN KAN VÆRE
FYSISKE KOMPONENTER.

"""

#%% Biblioteker

import numpy as np
import math
import matplotlib.pyplot as plt

#%% Avgrensninger


#%% Simulation Time Settings

t_start = 0  # [min] 
t_stop = 10000 # [min]

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

pumpe_q_max = 1.9998 # [m^3/min] - Volumetrisk strømning ved maks pådrag. Funnet ved 120m^3 / 60s*60s
pumpe_q_min = 0 # [m^3/min] - Volumetrisk strømning ved 4 mA
pumpe_q_init = 0.9396 # [m^3/min] - Volumetrisk strømning ved første iterasjon | funnet ved totalstrømning fra begge pumpene / timer / 60*60
# 27.01.23 En forenklet versjon som ikke tar for seg mottrykk (net head) i røret og antatt linear pumpekurve

def ReturnK_p(pumpe_q_max, u_range):
    k_p = pumpe_q_max / u_range
    return k_p

k_p = ReturnK_p(pumpe_q_max, u_range) # Forholdet mellom pådragssignal og volumetrisk strømning


#%% Innløpsventil parameter

C_v1 = 0.005 # [x] Valve flow coefficient


#%% Utløpsventil parameter

C_v2 = 0.05# [x] Valve flow coefficient

#%% PID-regulator parameter
Pu = 0
Kpu = 100
Kp = Kpu # Kpu*0.25
Ti = np.inf # Kpu*1.25
Td = 0
#P = 1 # proporsjonal forsterkning
#I = 10000000 # Integraltid
#D = 0 # Derivattid
u_man = 8 # Manuelt pådrag

settpunkt = 2.8 # Setpunkt i tanken | 40% i en 7m høy tank
# her går det an å lage en formel for utregning fra h [m] til h [%]

modus = "auto"

#%% Alarmgrenser



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
    

class Reservoir:
    def __init__(self, h_max, h_min, radius, h_init):
        
        self.h_max = h_max
        self.h_min = h_min
        self.radius = radius
        self.areal = self.Areal()
        
        self.h = h_init
        
        # if (self.h > h_max): # prøv å få dette til å fungere
        #     self.h = h_max
        # elif (self.h < h_min):
        #     self.h = h_min
        # else:
        #     pass
        
        self.h_prosent = (self.h/self.h_max)*100
        
        # denne er for GIVAS 09:10 01.02.2023 - 09:10 02.02.2023
        #self.DynamiskForbruk = [0, 0.003425, 0.003425, 0, 0, 0, 0, 0.06, 0.06, 0, 0, 0.0043, 0, 0, 0, 0, 0,0,0,0,0,0,0,0]
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
      
        if (flowIn > pumpe_q_max):
            flowIn = pumpe_q_max
        elif (flowIn < pumpe_q_min):
            flowIn = pumpe_q_min
        return flowIn # [m^3/s]


class Regulator:
    def __init__(self, settpunkt, prosessverdi, P, I, D, u_man, modus):
        
        self.settpunkt = settpunkt
        self.prosessverdi = prosessverdi
        self.P = P
        self.I = I
        self.D = D
        self.u_man = u_man
        self.modus = modus.upper() # ".upper()" forhindrer syntax error
        
        self.u_i_forrige = 0 # Test
        
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
            
            
            #Oppdater u_i_forrige
            self.u_i_forrige = u_i
            
        elif self.modus == "MAN":
            # Regulatoren er nå i manuell modus
            u = self.u_man
            
        else:
            # Feilmelding
            print("Vennligst skriv MAN eller AUTO på kodelinje: 83")
        u = np.clip(u,u_min,u_max)
        return u

#%% Opprett objekter av klassene


mittReservoir = Reservoir(reservoir_h_max, reservoir_h_min, reservoir_radius, reservoir_h_init)
minRegulator = Regulator(settpunkt, mittReservoir.StatiskForbruk(), Kp, Ti, Td, u_man, modus)
minPumpe = Pumpe(Kp, u_min, u_max, minRegulator.Pådrag())
minDataLagring = DataLagring(t_stop, mittReservoir.h, minPumpe.FlowIn(), mittReservoir.StatiskForbruk(), minRegulator.settpunkt)

#%%Program-loop

for t in range (t_start, t_stop):
   
 
    # dh_dt = f_in - f_out / A
    
    if (t < 2000):
        minRegulator.settpunkt = 2.8
        minDataLagring.settpunkt = 2.8
    elif (t >= 2000):
        minRegulator.settpunkt = 2.94
        minDataLagring.settpunkt = 2.94
    
    dh_dt = (minPumpe.FlowIn() - mittReservoir.StatiskForbruk()) / mittReservoir.Areal()
    
   
       
    
    # Mitt reservoir.h oppdaterer høyden i tanken per iterasjon
    mittReservoir.h += dh_dt 
    
    # Oppdater nivået i tanken
    if (mittReservoir.h > reservoir_h_max):
        minRegulator.prosessverdi = reservoir_h_max
        mittReservoir.h = reservoir_h_max
    elif (mittReservoir.h < reservoir_h_min):
        minRegulator.prosessverdi = reservoir_h_min
        mittReservoir.h = reservoir_h_min
    
    # Oppdater error 
    minRegulator.e = minRegulator.Error()
    
    # Generer nytt pådrag til pumpa
    # if (minPumpe.u > u_max):
    #     minPumpe.u = u_max
    # elif (minPumpe.u < u_min):
    #     minPumpe.u = u_min  
  
    minPumpe.u = minRegulator.Pådrag()
    # minPumpe.u = np.clip(minPumpe.u,u_min,u_max)
  
    # Lagring av verdier til Datalagringsklassen
    minDataLagring.t_array[t] = t
    minDataLagring.h_t_array[t] = mittReservoir.h
    minDataLagring.f_in_t_array[t] = minPumpe.FlowIn()
    minDataLagring.f_out_t_array[t] = mittReservoir.StatiskForbruk()
    minDataLagring.settpunkt_array[t] = minRegulator.settpunkt
    minDataLagring.u_array[t] = minRegulator.Pådrag()
    

#%% plotting

plt.close('all')
plt.figure("Plot")

plt.subplot(3,1,1)
plt.plot(minDataLagring.t_array, minDataLagring.h_t_array, label = "Prosessverdi")
plt.plot(minDataLagring.t_array, minDataLagring.settpunkt_array, 'r', label = 'Settpunkt')
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, reservoir_h_init - 1, 8])
plt.title("Nivå i tank")
plt.ylabel("level [m]")

plt.subplot(3,1,2)
plt.plot(minDataLagring.t_array, minDataLagring.f_in_t_array, label = "Innstrømning")
plt.plot(minDataLagring.t_array, minDataLagring.f_out_t_array, label = "Utstrømning")
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, pumpe_q_min, 3])
plt.title("Inn-/utstrømning")
plt.ylabel("Volumstrømning [m^3/s]")

plt.subplot(3,1,3)
plt.plot(minDataLagring.t_array, minDataLagring.u_array, label = "Pumpepådrag")
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, u_min, 20])
plt.title("Pumpepådrag")
plt.xlabel("Time [s]")
plt.ylabel("Pådrag [mA]")

plt.show()