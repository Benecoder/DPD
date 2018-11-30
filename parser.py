#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sys

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
    
def read_file(path):
    
    print('Reading the file...')
    
    #imports the file
    content = pd.read_csv(path,
                          delimiter='\t',
                          skiprows = [1,2],
                          index_col = False)

    content.columns = ['timestamp','Volt','PAR','CO2','temp','logger','H2O']
    
    content.timestamp = pd.to_datetime(content.timestamp)
    content.logger = content.logger.apply(comma_to_int)
    content.CO2 = content.CO2.apply(comma_to_float)
    
    return content

def find_aoi(content):
    
    print('finding the areas of interest...')
    
    #finds the measurments
    trigger = content.logger.values[1:]-content.logger.values[:-1]
    trigger /= trigger.max()
    start_marks = (trigger == 1).nonzero()[0]+1
    end_marks = (trigger == -1).nonzero()[0]


    #selects the best measurments
    measurment_length = 36
    area_of_intrest  = np.zeros(content.shape[0])
    for measurment in range(len(start_marks)):
        best_score = 0
        for i in range(start_marks[measurment],end_marks[measurment]-measurment_length):
            p,cov = np.polyfit(np.arange(measurment_length),content.CO2.values[i:i+measurment_length],1,cov = True)
            if cov[1][0]**2 > best_score:
                best_score = cov[1][0]**2
                best_index = i
        if best_score != 0:
            area_of_intrest[best_index:best_index+measurment_length] = 1
            
    return area_of_intrest

#visualizing
def vis(content,area_of_intrest):
    
    print('Visualizing...')
    
    import matplotlib
    import matplotlib.pyplot as plt

    x = np.arange(content.shape[0])

    plt.plot(x,content.CO2.values-400,color = 'black')

    plt.bar(x,area_of_intrest*50,alpha = 0.5,color = 'green')

    norm_logger = (content.logger.values+7)
    norm_logger /= np.max(norm_logger)
    plt.bar(x,norm_logger*50,alpha= 0.4,color = 'yellow')

    plt.ylabel('CO2 [ppm - 400]')
    plt.xlabel('Measurment_index')

    plt.show()
    


#building the new file
#final header 
def write_file(content,area_of_intrest):
    
    print('Writing the final file...')

    result = pd.DataFrame(index = content.index)
    result['date'] = [x.date() for x in content.timestamp]
    result['time'] = [x.time() for x in content.timestamp]
    result['CO2'] = content.CO2
    result['PAR'] = content.PAR
    result['temp'] = content.temp
    result['logger'] = content.logger
    result['AoI'] = area_of_intrest
    result['H2O'] = content.H2O

    writer = pd.ExcelWriter('result.xlsx')
    result.to_excel(writer,'Sheet1')
    writer.save()

if __name__  == '__main__':
    content = read_file(sys.argv[1])
    area_of_intrest = find_aoi(content)
    #vis(content,area_of_intrest)
    write_file(content,area_of_intrest)
    