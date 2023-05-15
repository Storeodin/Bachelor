#%% Notater
"""
https://control.com/forums/threads/tuning-of-cascade-control.21580/
A requirement of cascade control is that the secondary loop should be faster than the
primary loop. A good rule of thumb is at least 3-10 times faster.

time_delay på 120 iterasjoner. 


Finn en måte å simulere smartstyrt kaskade vs vanlig kaskade og finn ut hvor penger du sparer på å kjøre
når prisen er under gjennomsnitt :-)
"""

#%% Biblioteker

import numpy as np
import math
import matplotlib.pyplot as plt
import random

#%% Pris

pris_kaskade = 0
pris_smartstyring = 0

#%% Kjører smartstyring | Her er vi ute etter å ha tilgang til StyringsProfilArray i variable explorer

exec(open('Smartstyring_rev2.py').read())

# Danner et array med styringsprofil sekund for sekund
StyringsProfilSekundforSekund = [0]
strømPrisSekundforSekund = [0]

# Endrer styringsprofilarray fra timer til sekunder
for i in range (24):
    for t in range(60*60):
        StyringsProfilSekundforSekund.append(styringsProfilArray[i])
        strømPrisSekundforSekund.append(stromPrisArrayDagens[i]) # [Kr/kWt]    

#%% Instrument parameter

MåleAvvikNivå = 0.5 # [%]
MåleAvvikStrømning = 0.5 # [%]

#%% Simulation Time Settings

t_start = 0  # [s]
t_stop = 60*60*24 # [s]

#%% Signal parameter

u_min = 0 # [mA]
u_max = 16 # [mA]
u_range = u_max - u_min # [mA]

#%% Reservoir parameter

reservoir_h_max = 7 # [m]
reservoir_h_min = 0 # [m]
reservoir_radius = 11 # [m]
reservoir_h_init = 2.8 # [m]

reservoir_lavkutt = 1.4 # [m]
reservoir_høykutt = 5.6 # [m]

#%% Pumpe parameter

# fant pumpe_q_max på PV206 prosessbilde.jpg ved å ta 49.2m^3/t / 30.4A / 60*60 = 0.022m^3/s
# men blir dette feil?,  vet jo ikke hvor faktoren fra rampup er. står 1% ramp per sek på PV206 parameterbilde
# pumpe_q_max = 0.022 # [m^3/s]

pumpe_energiforbruk = 191 # kW/t ved max

# kW/h per mA (styresignal)
pumpe_energi_forbruk_per_mA = pumpe_energiforbruk / 16 # [kWt/mA]

# kW/s per mA (Styresignal)
pumpe_energi_forbruk_per_s_per_mA = pumpe_energi_forbruk_per_mA / 3600 # [kWs/mA]

pumpe_q_max = 0.033 # [m^3/s] - Volumetrisk strømning ved maks pådrag. Funnet ved 120m^3 / 60s*60s
pumpe_q_min = 0 # [m^3/s] - Volumetrisk strømning ved 4 mA
pumpe_q_init = 0.015 # [m^3/s] - Volumetrisk strømning ved første iterasjon | funnet ved totalstrømning fra begge pumpene / timer / 60*60
# 27.01.23 En forenklet versjon som ikke tar for seg mottrykk (net head) i røret og antatt linear pumpekurve

def ReturnK_p(pumpe_q_max, u_range):
    k_p = (pumpe_q_max - pumpe_q_min) / u_range
    return k_p

k_p = ReturnK_p(pumpe_q_max, u_range) # Forholdet mellom pådragssignal og volumetrisk strømning

#%% Filter Parameter

TidsIntervall = 100
NivaaVindu = np.ones(TidsIntervall)*reservoir_h_init
StromningsVindu = np.ones(TidsIntervall)*pumpe_q_init

#%% Innløpsventil parameter

C_v1 = 0.005 # [x] Valve flow coefficient

#%% Utløpsventil parameter

C_v2 = 0.005 # [x] Valve flow coefficient

#%% Primærsløyfe nivå-PI(D)-regulator parameter

ol_Kpu = 2 # Kritisk Forsterkning # 40.035
ol_Pu = 3000 # [s] Kritisk Periode # 483

ol_P = ol_Kpu*0.25 # proporsjonal forsterkning | ZN Relaxed
ol_I = ol_Pu*1.25 # Integraltid | ZN Relaxed
ol_D = 0 # Derivattid
ol_u_man = np.sqrt(2.8)*C_v2 # Manuelt pådrag | Stabiliserer seg på 40% ved 0.008365 i pådrag ved inner loop i auto

ol_settpunkt = 2.8 # Settpunkt i tanken | 40% i en 7m høy tank
# her går det an å lage en formel for utregning fra h [m] til h [%]

ol_modus = "auto"

#%% Sekundærsløyfe strømnings-PI(D)-regulator parameter

il_Kpu = 484.81 # Kritisk Forsterkning
il_Pu = 28 # Kristisk Periode

il_P = il_Kpu*0.25 # Proporsjonal forsterkning
il_I = il_Pu*1.25 # Intergraltid
il_D = 0 # Derivattid
il_u_man = 4.0566 # Manuelt pådrag

il_pv_init = pumpe_q_init
il_sp_init = np.sqrt(2.8)*C_v2
#il_sp_init = ol_settpunkt - reservoir_h_init # Settpunkt i flow = pådrag fra nivåregulator

il_modus = "auto"

#%% Initialization of time delay flow in

f_delay = 120
f_delayed_init = 0
N_delay_f = int(round(f_delay/1)) + 1
delay_array = np.zeros(N_delay_f) + f_delayed_init

#%% Initialisering av tidsforsinkelse ved måling av strømning

f_meas_delay = 12
f_meas_delayed_init = 0
N_delay_meas = int(round(f_meas_delay/1)) + 1
f_meas_delay_array = np.zeros(N_delay_meas) + f_meas_delayed_init

#%% funksjoner

def BesparelseProsent(pris_kaskade, pris_smartstyring):
    besparelse = ((pris_kaskade - pris_smartstyring) / pris_kaskade) * 100
    return besparelse

#%% Klasser 

def Sum(array):
	sum = 0
	for i in array:
		sum += i
	return sum

class DataLagring:
    def __init__(self, t, h_t, f_in_t, f_out_t, settpunkt):
        self.t = t # Blir brukt som tid og indeks
        self.h_t = h_t # Høyden i bassenget som funksjon av tid
        self.f_in_t = f_in_t # Flow in som funksjon av tid, fått av pump.Flow()
        self.f_out_t = f_out_t # f_out_t # flow ut som funksjon av tid, fått av Reservoir.FlowOut()
        self.settpunkt = settpunkt
        self.u = pumpe_q_init # Muligens feil
        
        # Arrays til plotting | Kaskade
        self.t_array = np.zeros(t)
        self.h_t_array = np.zeros(t)
        self.f_in_t_array = np.zeros(t)
        self.f_out_t_array = np.zeros(t)
        self.settpunkt_array = np.zeros(t)
        self.u_f_array = np.zeros(t)
        self.u_h_array = np.zeros(t)
        self.e_array = np.zeros(t)
        self.pris_kaskade_array = np.zeros(t)
        self.il_u_i_forrige_array = np.zeros(t)
        self.ul_u_i_forrige_array = np.zeros(t)
        
        # Arrays til plotting | Smartstyring
        self.h_t_array_smart = np.zeros(t)
        self.f_in_t_array_smart = np.zeros(t)
        self.u_f_array_smart = np.zeros(t)
        self.pris_smartstyring_array = np.zeros(t)

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
    
    def TilfeldigForbruk(self):
        pass # do something
        
class Pumpe:
    def __init__(self, K_p, u_min, u_max, u):
        
        self.K_p = K_p # [%] forsterkning
        self.u = u # [mA] pådragssignal
        self.u_max = u_max # [mA]
        self.u_min = u_min # [mA]

    def FlowIn(self):
        flowIn = self.K_p * self.u
        return flowIn # [m^3/s]

class OuterLoopRegulator:
    def __init__(self, settpunkt, prosessverdi, P, I, D, u_man, modus):
        
        self.settpunkt = settpunkt
        self.prosessverdi = prosessverdi
        self.P = P
        self.I = I
        self.D = D
        self.u_man = u_man
        self.modus = modus.upper() # ".upper()" forhindrer syntax error ved store og små bokstaver
        
        self.u_i_forrige = self.u_man
        
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
            if u > 0.033: # 16
                self.u_i_forrige = self.u_i_forrige
            elif u < 0:
                self.u_i_forrige = self.u_i_forrige
            else:   
                self.u_i_forrige = u_i
            
        elif self.modus == "MAN":
            # Manuell drift
            u = self.u_man
            
        else:
            # Feilmelding
            print("Vennligst skriv MAN eller AUTO på kodelinje: 91")
            
        # Begrens pådragssignal til gitte rammer
        u = np.clip(u, 0, 0.033) # u_min, u_max
        return u

class InnerLoopRegulator:
    def __init__(self, settpunkt, prosessverdi, P, I, D, u_man, modus):
        
        self.settpunkt = settpunkt
        self.prosessverdi = prosessverdi
        self.P = P
        self.I = I
        self.D = D
        self.u_man = u_man
        self.modus = modus.upper()
        
        self.u_i_forrige = self.u_man
        
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
            u_i = (self.P / self.I) * self.e + self.u_i_forrige
                
            # Regn ut totalforsterkning
            u = u_p + u_i # + u_d | u_d ikke implementert
                
            #Oppdater u_i_forrige + antiwindup
            if u > u_max:
                self.u_i_forrige = self.u_i_forrige
            elif u < u_min:
                self.u_i_forrige = self.u_i_forrige
            else:   
                self.u_i_forrige = u_i
            
        elif self.modus == "MAN":
            # Manuell drift
            u = self.u_man
            
        else:
            # Feilmelding
            print("Vennligst skriv MAN eller AUTO på kodelinje: 106")
                
        # Begrens pådrag til gitte rammer
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
        PVavvik = (self.prosessverdi * self.måleavvik) / 100
        PVstøy = random.uniform(self.prosessverdi - PVavvik, self.prosessverdi + PVavvik)
        return PVstøy

class Strømningsmåler(Instrument):
    def PVstøy(self):
        PVavvik = (self.prosessverdi * self.måleavvik) / 100
        PVstøy = random.uniform(self.prosessverdi - PVavvik, self.prosessverdi + PVavvik)
        return PVstøy
	
class MiddelVerdiFilter:
	def __init__(self, T_v):
		self.T_v = T_v
		
	def Filtrer(self, vindu):
		summ = Sum(vindu)
		MiddelVerdi = summ / self.T_v
		return MiddelVerdi

#%% Opprett objekter av klassene

mittReservoir = Reservoir(reservoir_h_max, reservoir_h_min, reservoir_radius, reservoir_h_init)
outerLoopRegulator = OuterLoopRegulator(ol_settpunkt, mittReservoir.h, ol_P, ol_I, ol_D, ol_u_man, ol_modus)
innerLoopRegulator = InnerLoopRegulator(outerLoopRegulator.Pådrag(), il_pv_init, il_P, il_I, il_D, il_u_man, il_modus)
minPumpe = Pumpe(k_p, u_min, u_max, innerLoopRegulator.Pådrag())
minDataLagring = DataLagring(t_stop, mittReservoir.h, minPumpe.FlowIn(), mittReservoir.StatiskForbruk(), outerLoopRegulator.settpunkt)
minNivåmåler = Nivåmåler(mittReservoir.h, MåleAvvikNivå)
minStrømningsmåler = Strømningsmåler(minPumpe.FlowIn(), MåleAvvikStrømning)
middelVerdiFilter = MiddelVerdiFilter(TidsIntervall)

#%% Program-loop

# Simulerer fullt innløp
for i in range (f_delay + 1):
    delay_array[i] = np.sqrt(2.8)*C_v2

# Simulerer null delay på måling i startfasen
for h in range (f_meas_delay + 1):
    f_meas_delay_array[h] = np.sqrt(2.8)*C_v2

for sim in range(2):
    mittReservoir.h = reservoir_h_init
    for t in range (t_start, t_stop):
        
        # forsinker innstrømning i tanken med 120 iterasjoner | bare valgt et tall her
        f_in_delayed = delay_array[-1]
        delay_array[1:] = delay_array[0:-1]
        delay_array[0] = minPumpe.FlowIn()
        
        # dh_dt = f_in - f_out / A
        dh_dt = (f_in_delayed - mittReservoir.StatiskForbruk()) / mittReservoir.Areal() # | *60 for minutter istedet for sekunder
        
        # Mitt reservoir.h oppdaterer høyden i tanken per iterasjon
        mittReservoir.h += dh_dt
        
        # Måler nivå med Nivåmåler
        minNivåmåler.prosessverdi = mittReservoir.h
        
        # Filtrerer målt Nivåverdi
        filtrertNivaa = MiddelVerdiFilter.Filtrer(middelVerdiFilter, NivaaVindu)
        NivaaVindu[1:] = NivaaVindu[0:-1]
        NivaaVindu[0] = minNivåmåler.PVstøy()
        
        # Oppdater outer loop regulatoren PV | med støy
        outerLoopRegulator.prosessverdi = filtrertNivaa
        
        # Oppdater outer loop error
        outerLoopRegulator.e = outerLoopRegulator.Error()
        
        # Send outerLoop u til inner loop SP
        innerLoopRegulator.settpunkt = outerLoopRegulator.Pådrag()
        
        # Forsinker strømningsmåling med 12 sekunder
        f_meas_delayed = f_meas_delay_array[-1]
        f_meas_delay_array[1:] = f_meas_delay_array[0:-1]
        f_meas_delay_array[0] = minPumpe.FlowIn()
        
        # Måler strømning med strømningsmåler
        minStrømningsmåler.prosessverdi = f_meas_delayed
        
        # Filtrerer målt Strømningsverdi
        filtrertStromning = MiddelVerdiFilter.Filtrer(middelVerdiFilter, StromningsVindu)
        StromningsVindu[1:] = StromningsVindu[0:-1]
        StromningsVindu[0] = minStrømningsmåler.PVstøy()
        
        # Oppdater sekundær regulator PV
        innerLoopRegulator.prosessverdi = filtrertStromning
        
        # Oppdater inner loop error
        innerLoopRegulator.e = innerLoopRegulator.Error()
        
        # Simulerer kaskaderegulering uten smartstyring
        if sim == 0:
            
            # Generer nytt pådrag til pumpa
            minPumpe.u = innerLoopRegulator.Pådrag()
            
            # Lagring av verdier fra kaskaderegulering
            minDataLagring.h_t_array[t] = outerLoopRegulator.prosessverdi
            minDataLagring.f_in_t_array[t] = innerLoopRegulator.prosessverdi
            minDataLagring.u_f_array[t] = minPumpe.u
            minDataLagring.pris_kaskade_array[t] = minPumpe.u * pumpe_energi_forbruk_per_s_per_mA * strømPrisSekundforSekund[t] # [mA * kWs/mA * Kr/kWs = Kr]
            
            # Lagrer pris
            pris_kaskade += minDataLagring.pris_kaskade_array[t]
        
        # Simulerer kaskaderegulering med smartstyring
        else:
            # Generer nytt pådrag til pumpa dersom smartstyringen tillater det
            if StyringsProfilSekundforSekund[t] == 1:
                minPumpe.u = innerLoopRegulator.Pådrag()
            elif innerLoopRegulator == "man":
                minPumpe.u = innerLoopRegulator.Pådrag()
            else: # Styringsprofilen = 0
                if outerLoopRegulator.prosessverdi < reservoir_lavkutt:
                    for t_m in range (t, t+1800):
                        StyringsProfilSekundforSekund[t_m] = 1
                        #minPumpe.u = innerLoopRegulator.Pådrag()
                elif outerLoopRegulator.prosessverdi > reservoir_høykutt:
                    minPumpe.u = innerLoopRegulator.Pådrag()
                else:
                    minPumpe.u = 0
            
            # Lagring av verdier fra smartstyring  
            minDataLagring.h_t_array_smart[t] = outerLoopRegulator.prosessverdi
            minDataLagring.f_in_t_array_smart[t] = innerLoopRegulator.prosessverdi
            minDataLagring.u_f_array_smart[t] = minPumpe.u
            minDataLagring.pris_smartstyring_array[t] = minPumpe.u * pumpe_energi_forbruk_per_s_per_mA * strømPrisSekundforSekund[t] # [mA * kWs/mA * Kr/kWs = Kr]
            
            # Lagrer pris
            pris_smartstyring += minDataLagring.pris_smartstyring_array[t]
            

        # Lagring av verdier til Datalagringsklassen
        minDataLagring.t_array[t] = t
        #minDataLagring.h_t_array[t] = minNivåmåler.PVstøy()
        #minDataLagring.f_in_t_array[t] = minStrømningsmåler.PVstøy()
        minDataLagring.f_out_t_array[t] = mittReservoir.StatiskForbruk()
        minDataLagring.settpunkt_array[t] = outerLoopRegulator.settpunkt
        #minDataLagring.u_f_array[t] = innerLoopRegulator.Pådrag()
        #minDataLagring.u_f_array[t] = minPumpe.u
        minDataLagring.u_h_array[t] = outerLoopRegulator.Pådrag()
        minDataLagring.e_array[t] = outerLoopRegulator.e
        minDataLagring.il_u_i_forrige_array[t] = innerLoopRegulator.u_i_forrige
        minDataLagring.ul_u_i_forrige_array[t] = outerLoopRegulator.u_i_forrige


#%% plotting

xlim = np.arange(t_start, t_stop, 60*60)

plt.close('all')
plt.figure("Plot")

plt.subplot(5,1,1)
plt.plot(minDataLagring.t_array, minDataLagring.h_t_array, label = "Prosessverdi")
plt.plot(minDataLagring.t_array, minDataLagring.settpunkt_array, 'r', label ='Settpunkt')
plt.xticks(xlim,['00:00','01:00','02:00','03:00', '04:00','05:00','06:00','07:00', '08:00','09:00','10:00',
                 '11:00','12:00','13:00','14:00','15:00', '16:00','17:00','18:00','19:00', '20:00','21:00',
                 '22:00','23:00'])
for i in range (24):
    plt.axvline(x=3600*i, color='black', linestyle='dashed')
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, mittReservoir.h_min, mittReservoir.h_max])
plt.title("Kaskaderegulering")
plt.ylabel("level [m]")


plt.subplot(5,1,2)
plt.plot(minDataLagring.t_array, minDataLagring.u_f_array, label = "Pumpepådrag")
plt.xticks(xlim,['00:00','01:00','02:00','03:00', '04:00','05:00','06:00','07:00', '08:00','09:00','10:00',
                 '11:00','12:00','13:00','14:00','15:00', '16:00','17:00','18:00','19:00', '20:00','21:00',
                 '22:00','23:00'])
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, u_min - 1, u_max + 1]) # +- 1 for å se verdien i plottet
#plt.title("Pumpepådrag")
plt.xlabel("Time [s]")
plt.ylabel("Pådrag [mA]")

plt.subplot(5,1,4)
plt.plot(minDataLagring.t_array, minDataLagring.h_t_array_smart, label = "Prosessverdi")
plt.plot(minDataLagring.t_array, minDataLagring.settpunkt_array, 'r', label ='Settpunkt')
plt.xticks(xlim,['00:00','01:00','02:00','03:00', '04:00','05:00','06:00','07:00', '08:00','09:00','10:00',
                 '11:00','12:00','13:00','14:00','15:00', '16:00','17:00','18:00','19:00', '20:00','21:00',
                 '22:00','23:00'])
for i in range (24):    
    plt.axvline(x=3600*i, color='black', linestyle='dashed')
plt.legend()
plt.grid()
#plt.axis([t_start, t_stop, mittReservoir.h_min, mittReservoir.h_max])
plt.title("Smartstyring")
plt.ylabel("level [m]")

plt.subplot(5,1,5)
plt.plot(minDataLagring.t_array, minDataLagring.u_f_array_smart, label = "Pumpepådrag")
plt.xticks(xlim,['00:00','01:00','02:00','03:00', '04:00','05:00','06:00','07:00', '08:00','09:00','10:00',
                 '11:00','12:00','13:00','14:00','15:00', '16:00','17:00','18:00','19:00', '20:00','21:00',
                 '22:00','23:00'])
plt.legend()
plt.grid()
plt.axis([t_start, t_stop, u_min - 1, u_max + 1]) # +- 1 for å se verdien i plottet
#plt.title("Pumpepådrag")
plt.xlabel("Time [s]")
plt.ylabel("Pådrag [mA]")

plt.show()

print("Du sparer: ", (pris_kaskade - pris_smartstyring), " $ Kroner $ på å ta i bruk smartstyring WeTheBest")
print("Dette tilsvarer ", BesparelseProsent(pris_kaskade, pris_smartstyring), "i prosent")
print("h_init for neste simulering skal være: ", minDataLagring.h_t_array_smart[-1])