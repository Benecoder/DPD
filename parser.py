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
    trigger = (content.logger.values[1:]-content.logger.values[:-1])+7.0
    start_marks = (trigger > 0.1).nonzero()[0]+1
    end_marks = (trigger < 0.1).nonzero()[0]
    


    #selects the best measurments
    tolerance = 5 #measurments
    area_of_intrest  = np.zeros(content.shape[0])
    quality = np.zeros(content.shape[0])
    cover_column = pd.Series(index =content.index)

    for measurment in range(len(start_marks)):
        best_score = 1
        
        measurment_length = end_marks[measurment]-start_marks[measurment]
        
        #if the measurment is shorter than 110 seconds
        if measurment_length < 110/5:
            cover = 't' #transparent cover
            aoi_length = 90/5
        else:
            cover = 'd' #dark cover
            if measurment_length < 200/5:
                aoi_length = 180/5
            else:
                aoi_length = 300/5
                
        
        for i in range(start_marks[measurment]-tolerance,end_marks[measurment]+tolerance-aoi_length):
            p,cov = np.polyfit(np.arange(aoi_length),content.CO2.values[i:i+aoi_length],1,cov = True)
            if cov[1][0]**2 < best_score:
                best_score = cov[1][0]**2
                best_index = i
                best_slope = p[0]

        if best_score != 1:
            area_of_intrest[best_index:best_index+aoi_length+1] = 1
            cover_column[best_index:best_index+aoi_length+1] = cover
            if cover == 'd' and best_slope < 0:
                quality[best_index:best_index+aoi_length+1] = 2
            else:
                quality[best_index:best_index+aoi_length+1] = 1

    return area_of_intrest,cover_column,quality

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
def write_file(content,area_of_intrest,cover_column,quality):
    
    print('Writing the final file...')

    result = pd.DataFrame(index = content.index)
    result['date'] = [x.date() for x in content.timestamp]
    result['time'] = [x.time() for x in content.timestamp]
    result['PAR'] = content.PAR
    result['CO2'] = content.CO2
    result['temperature'] = content.temp
    result['chamber'] = cover_column
    result['Logger'] = content.logger
    result['AoI'] = area_of_intrest
    result['quality'] = quality
    result['H2O'] = content.H2O

    writer = pd.ExcelWriter('result.xlsx')
    result.to_excel(writer,'Sheet1')
    writer.save()

if __name__  == '__main__':
    content = read_file(sys.argv[1])
    area_of_intrest,cover_column,quality = find_aoi(content)
 #   vis(content,area_of_intrest)
 
    #write_file(content,area_of_intrest,cover_column,quality)
    