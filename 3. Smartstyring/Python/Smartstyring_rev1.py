""" 
Smart styring

Notater:
Første revisjon hvor vi av og på "styrer" (regulerer) pumpepådraget til å være på ved en viss strømpris

"""
#%% Biblioteker

import numpy as np
import random

#%% Connectionstring (via OPCUA til database)

conString = ""

#%% Variabler

# Opprette tomme arrays for dagens og morgendagens strømpris
timer = 24
stromPrisArrayDagens = np.zeros(timer)
stromPrisArrayiMorgen = np.zeros(timer)
styringsProfilArray = np.zeros(timer)

# Pådragssignal som er 0 eller 1
u_off = 0
u_on = 1
u = 0

# Metode som regner gjennomsnittspris iløpet av dagen
def gjennomsnitt(arr):
    total = 0
    for i in arr:
        total += i
    return total/(timer)

#%% fyll strømprisArray med verdier | her skal det jo egentlig være en connection til OPC tags som vi
#   skriver til med strømpris API
"""
for i in range(timer):
    # Random strømpris [øre/Kwh]
    strompris = random.uniform(124, 137)
    
    # Legg tilfeldig strømpris inn i array
    stromPrisArrayDagens[i] = strompris
"""
#%% Ekte verdier fra 23.02.2023

# Hardkodet inn prisene fra 23.02.2023
#stromPrisArrayDagens = [1.12818, 1.10563, 1.10004, 1.0949, 1.09052, 1.10836, 1.11526, 1.14044, 1.18795, 1.22659, 1.20207, 1.21192, 1.20021, 1.18565, 1.16945, 1.1724, 1.20404, 1.24706, 1.25122, 1.21499, 1.14066, 1.13431, 1.10004, 1.06567]

# Strømpris fra 24.02.2023
#stromPrisArrayDagens = [0.94703, 0.86263, 0.8632, 0.81192, 0.78588, 0.87359, 0.96428, 1.02344, 1.06741, 0.9934, 0.90112, 0.87839, 0.83042, 0.83887, 0.86857, 0.88216, 0.95537, 0.97809, 0.99945, 1.01396, 1.00836, 1.00493, 1.01464, 0.95582]

# Strømpris fra 18.04.2023
#stromPrisArrayDagens = [1.16346, 1.12789, 1.11694, 1.11911, 1.1109, 1.12834, 1.19789, 1.54816, 1.71121, 1.37599, 1.17349, 1.13553, 1.05776, 0.98639, 0.93576, 0.91353, 0.92995, 1.04294, 1.11318, 1.13917, 1.15662, 1.15502, 1.14556, 1.09163]

# Strømpris fra 19.04.2023
#stromPrisArrayDagens = [1.12651, 1.07856, 1.10026, 1.09413, 1.11583, 1.16822, 1.21993, 1.27186, 1.4413, 1.1722, 1.04628, 0.90867, 0.85844, 0.8498, 0.84173, 0.85287, 0.88537, 0.9173, 1.04572, 1.17811, 1.21106, 1.21106, 1.1922, 1.11935]

# Strømpris fra 20.04.2023
#stromPrisArrayDagens = [1.1112, 1.05054, 1.07519, 1.05535, 1.07989, 1.1206, 1.17221, 1.20787, 1.19744, 1.11659, 1.07829, 1.07324, 1.0471, 0.99572, 0.98575, 0.96327, 1.02325, 1.11143, 1.12748, 1.1581, 1.20581, 1.20168, 1.17657, 1.14916]


# Strømpris fra 19.04.2023
#stromPrisArrayDagens = [1.12651, 1.07856, 1.10026, 1.09413, 1.11583, 1.16822, 1.21993, 1.27186, 1.4413, 1.1722, 1.04628, 0.90867, 0.85844, 0.8498, 0.84173, 0.85287, 0.88537, 0.9173, 1.04572, 1.17811, 1.21106, 1.21106, 1.1922, 1.11935]

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

#%% Regn ut gjennomsnitt 

gj = gjennomsnitt(stromPrisArrayDagens)

#%"% løkke som skrur av og på pådragssignal

for t in range (timer):
    if stromPrisArrayDagens[t] < gj:
        u = u_on
        styringsProfilArray[t] = u
    else:
        pass

#%% Lag en funksjon som du kan kalle på for å fylle i arrayet
"""
def StyringsProfil(array):
    for t in range(array):
        if strømPrisArrayDagens[t] < gj:
            styringsProfilArray[t] = 1
        else:
            pass   
"""
    











    