""" 
Smart styring

Hva om vi bruker MPC til å predikere vannforbruket sammen med
en algoritme som regner ut hvor mange timer det tar
å fylle delta V?

I denne revisjonen kan vi bruke noen selvdefinerte verdier
for vannforbruk.

La oss si du har et array med forventet vannforbruk i et array(24)
så legger du sammen alt det til en volumverdi og trekker ifra h_o eller h_sp
for å så finne antall timer det tar å fylle deltaV ved 
Pumpekapasitet_max / delta V = x [t]

så ved å bruke nærmeste heltall til x avrundet opp, si den er 4, så finner vi nøyaktig de 4
timene på døgnet det er billigst å fylle.

For at dette skal fungere blir det en av-og-på regulering, dette er svært ugunstig med tanke på levetiden til pumpa
kanskje dette er en mulig løsning om vi introduserer rampetid i en eventuell frekvensomformer eller liknende.

"""
#%% Biblioteker

import numpy as np
import random

#%% Connectionstring (via OPCUA til database)

conString = ""

#%% stuff

# strømpriser fra 17.04.23
#stromPrisArrayDagens = [1.19082, 1.176, 1.16015, 1.14955, 1.15924, 1.2012, 1.34646, 1.96776, 1.79855, 1.58214, 1.46698, 1.27201, 1.17349, 1.13792, 1.08308, 1.05754, 1.07304, 1.12378, 1.17213, 1.17327, 1.17201, 1.16962, 1.16506, 1.1573]

# Strømpriser fra 18.04.23
#stromPrisArrayDagens = [1.16346, 1.12789, 1.11694, 1.11911, 1.1109, 1.12834, 1.19789, 1.54816, 1.71121, 1.37599, 1.17349, 1.13553, 1.05776, 0.98639, 0.93576, 0.91353, 0.92995, 1.04294, 1.11318, 1.13917, 1.15662, 1.15502, 1.14556, 1.09163]

# Strømpriser fra 19.04.23
#stromPrisArrayDagens = [1.12651, 1.07856, 1.10026, 1.09413, 1.11583, 1.16822, 1.21993, 1.27186, 1.4413, 1.1722, 1.04628, 0.90867, 0.85844, 0.8498, 0.84173, 0.85287, 0.88537, 0.9173, 1.04572, 1.17811, 1.21106, 1.21106, 1.1922, 1.11935]

# Strømpriser fra 20.04.23
#stromPrisArrayDagens = [1.1112, 1.05054, 1.07519, 1.05535, 1.07989, 1.1206, 1.17221, 1.20787, 1.19744, 1.11659, 1.07829, 1.07324, 1.0471, 0.99572, 0.98575, 0.96327, 1.02325, 1.11143, 1.12748, 1.1581, 1.20581, 1.20168, 1.17657, 1.14916]

# Strømpriser fra 21.04.23
#stromPrisArrayDagens = [1.10491, 1.0597, 1.04966, 1.07238, 1.05555, 1.09834, 1.23039, 1.30121, 1.36072, 1.19602, 1.06016, 0.93271, 0.8484, 0.81023, 0.79454, 0.804, 0.94229, 1.05013, 1.12117, 1.17676, 1.19245, 1.1951, 1.18276, 1.10941]

# Strømpriser fra 22.04.23
#stromPrisArrayDagens = [1.11596, 1.07256, 1.03775, 1.04947, 1.02649, 1.07929, 1.12245, 1.15344, 1.11433, 1.00444, 0.89235, 0.57916, 0.42772, 0.52125, 0.66027, 0.69601, 0.87134, 1.0085, 1.11398, 1.19544, 1.20832, 1.1785, 1.14508, 1.1329]

# Strømpriser fra 23.04.23
stromPrisArrayDagens = [1.18649, 1.10039, 1.0722, 1.01336, 1.00928, 1.02187, 1.01674, 1.06089, 1.05693, 1.04855, 0.95185, 0.58194, 0.42699, 0.39682, 0.39274, 0.58148, 0.9614, 1.08664, 1.18183, 1.27818, 1.28086, 1.28074, 1.28051, 1.23728]

totalpris = 0
for pris in stromPrisArrayDagens:
    totalpris += pris
    
#%%

dagensForbruk = np.zeros(24)
totalForbruk = 0
"""
for i in range (24):
    dagensForbruk[i] = np.sqrt(2.8)*0.005
    totalForbruk += dagensForbruk[i]    
"""

# Det er mulig å legge til delta_V_0 for å få med seg avviket mellom settpunkt og prosessverdi i et døgnsskifte


# delta_V_0 = (ol_settpunkt - h_init)*math.pi*reservoir_radius**2
totalForbruk = 608.2 # m^3/h, fant dette ved å sette pådraget til pumpa til 0 og simulere et døgn


#%%

pumpeKapasitet = 0.033 # m^3/h
pumpeQ_time = pumpeKapasitet*3600

#%% stuff

antallTimer = totalForbruk / pumpeQ_time

antallTimerAvrundet = int(np.ceil(antallTimer))

#%% Papz

laveste_pris = sorted(stromPrisArrayDagens)[:antallTimerAvrundet]

laveste_pris_index = [stromPrisArrayDagens.index(val) for val in laveste_pris]

#%%

styringsProfilArray = np.zeros(24)

for indexer in laveste_pris_index:
    styringsProfilArray[indexer] = 1





    









    