#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sys

def comma_to_int(x):
    try:
        return int(float(x.replace(',','.')))
    except:
        return -1

def comma_to_float(x):
    try:
        return float(x.replace(',','.'))
    except:
        return 0.0
    
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
    content.logger.values[0]  = -1
    trigger = (content.logger.values[1:]-content.logger.values[:-1])
    trigger = np.sign(trigger)
    start_marks = (trigger == 1).nonzero()[0]+1
    end_marks = (trigger ==  -1 ).nonzero()[0]
    
    #resolves prolonged triggers
    d_end_marks = end_marks[1:]-end_marks[:-1]
    d_start_marks = start_marks[1:]-start_marks[:-1]
    double_end = (d_end_marks == 1).nonzero()[0]
    double_start = (d_start_marks == 1).nonzero()[0]
    end_marks = np.delete(end_marks,double_end)
    start_marks = np.delete(start_marks,double_start)
    
    #resolves initiation conflicts
    if end_marks[0]<start_marks[0]:
        end_marks = end_marks[1:]
    

    #selects the best measurments
    tolerance = 5 #measurments
    area_of_intrest  = np.zeros(content.shape[0])
    quality = np.zeros(content.shape[0])
    cover_column = pd.Series(index =content.index)

    no_measurments = np.min([len(end_marks),len(start_marks)])

    for measurment in range(no_measurments):
        best_score = 1
        
        measurment_length = end_marks[measurment]-start_marks[measurment]
        
        #if the measurment is shorter than 110 seconds
        if measurment_length < 110/5:
            cover = 't' #transparent cover
            aoi_length = int(90/5)
        else:
            cover = 'd' #dark cover
            if measurment_length < 200/5:
                aoi_length = int(180/5)
            else:
                aoi_length = int(300/5)

        #determines the start and end of the logger range, including some tolerance
        start_of_logger_area = start_marks[measurment]-tolerance
        if start_of_logger_area <0:
            start_of_logger_area = 0

        end_of_logger_area = end_marks[measurment]+tolerance-aoi_length
        if end_of_logger_area > content.shape[0]-aoi_length:
            end_of_logger_area = content.shape[0]-aoi_length
            
            
        for i in range(start_of_logger_area,end_of_logger_area):
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

    plt.bar(x,area_of_intrest*500,alpha = 0.5,color = 'green')
    norm_logger = (np.sign(content.logger.values)+1)

    plt.bar(x,norm_logger*250,alpha= 0.4,color = 'yellow')
    plt.ylabel('CO2 [ppm - 400]')
    plt.xlabel('Measurment_index')

    plt.show()


#building the new file
#final header 
def write_file(result_path,content,area_of_intrest,cover_column,quality):
    
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

    writer = pd.ExcelWriter(result_path+'.xlsx')
    result.to_excel(writer,'Sheet1')
    writer.save()
    
def find_names():
    
    if len(sys.argv) == 1:
        print('Requires path to raw file.')
        print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
        raise 
    if len(sys.argv) == 2:
        if sys.argv[1][-4:] == '.txt':
            return sys.argv[1],sys.argv[1][-4:]+'.xlsx'
        else:
            print('Requires txt file')
            print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
            raise 
    if len(sys.argv) > 2:
        if sys.argv[1][-4:] == '.txt' and sys.argv[2][-5:] == '.xlsx':
            return sys.argv[1],sys.argv[2]
        else:
            print('Requires txt file as input path and .xlsx file as output path.')
            print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
            raise

if __name__  == '__main__':
    
    path,result_path = find_names()
    
    
    content = read_file(path)
    area_of_intrest,cover_column,quality = find_aoi(content)
    #vis(content,area_of_intrest)
    write_file(result_path,content,area_of_intrest,cover_column,quality)
    