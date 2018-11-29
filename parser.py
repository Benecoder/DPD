import pandas as pd
import numpy as np

def comma_to_int(x):
    try:
        return int(float(x.replace(',','.')))
    except ValueError:
        return np.nan

def comma_to_float(x):
    try:
        return float(x.replace(',','.'))
    except ValueError:
        return np.nan
    

#imports the file
content = pd.read_csv('Team_X.txt',
                      delimiter='\t',
                      skiprows = [1,2],
                      index_col = 0,
                      parse_dates = True)

content.columns = ['date','H2O','CO2','temperature','logger','temp2']
content.logger = content.logger.apply(comma_to_int)
content.CO2 = content.CO2.apply(comma_to_float)

#finds the measurments
trigger = content.logger.values[1:]-content.logger.values[:-1]
trigger /= trigger.max()
start_marks = (trigger == 1).nonzero()[0]+1
end_marks = (trigger == -1).nonzero()[0]

"""
#selects the best measurments
import matplotlib.pyplot as plt

measurment_length = 36
focus_areas  = []
for measurment in range(len(start_marks)):
    best_score = 0
    for i in range(start_marks[measurment],end_marks[measurment]-measurment_length):
        p,cov = np.polyfit(np.arange(measurment_length),content.CO2.values[i:i+measurment_length],1,cov = True)
        if cov[1][0]**2 > best_score:
            best_score = cov[1][0]**2
            best_index = i
    if best_score != 0:
        focus_areas.append(best_index)
"""

#building the new file
final_header = ['date','time','PAR','CO2','temperature','logger']

result = pd.DataFrame(index = content.index)
result.index = content.index
result['date'] = [x.date() for x in result.index]
result['time'] = [x.() for x in result.time]