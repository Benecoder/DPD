#!/usr/bin/env python3

import pandas as pd
import numpy as np
import sys
import os


#converts incoming strings to integers
def comma_to_int(x):
    try:
        return int(float(x.replace(',','.')))
    except:
        return -1


#converts incoming strings to floats
def comma_to_float(x):
    try:
        return float(x.replace(',','.'))
    except:
        return 0.0
    
#Reads the file
#   Parameters:
#       path:string
#       path to the file that should be read
#   Returns:
#       content:pandas Data Frame
#       Dataframe containing the Data. If nescessary string numbers 
#       have been converted to integer/float.
def read_file(path):
    
    print('Reading the file...')
    
    #imports the file
    content = pd.read_csv(path,
                          delimiter='\t',
                          skiprows = [1,2],
                          index_col = False)

    if content.shape[1] == 7:
        content.columns = ['timestamp','Volt','PAR','CO2','temp','logger','H2O']
    elif content.shape[1] == 6:
        content.columns = ['timestamp','CO2','PAR','temp','logger','H2O']
    else:
        print('Number of columns is unreadble.')


    content.timestamp = pd.to_datetime(content.timestamp)
    content.logger = content.logger.apply(comma_to_int)
    content.CO2 = content.CO2.apply(comma_to_float)

    
    return content



#Finds the areas of interest, by determining the lowest covariance 
#when fitting a linear fit to the areas marked by the logger signal.
#The Algorithm works as follows:
# - Triggers are found, i.e. indicies where the logger signal
#   faises or falls.
# - Starting from the first raising signal, regions between 
#   a raising and a falling edge are marked as logger areas.
# - Based on the length of the logger area the class of measurment
#   and thus the measurment length is determined. 
# - Extending the logger area on both ends by 'tolerance'
#   indicies, a search for the best linear fit is performed.
#   A fit is performed to every possible compact region of 
#   the desired measurment length within the logger area. 
#   The metric used to evaluate the quality of the fit is the
#   offdiagonal entry in the covariance matrix, squared. 
#   The lower the better.
# - A crude measure for the quality of this spicific measurment is
#   introduced. 1 if everything is fine. 2 if the measurment is short
#   thus a dark cover is used, but the CO2 have a negative slope
#   nevertheless.
# - The Results are returned.


#Parameters:
#   content: Pandas Data Frame
#   Data Frame containing the column 'logger' and 'CO2'.
#   tolerance: integer
#   The number of measurments that are included before and after 
#   the logger area, that is originally determined by the logger 
#   Signal.
#Returns:
#   markers: Pandas Data Frame
#   DataFrame with 4 columns. 
#   1. area_of_interest; 1 if part of an aoi, else 0
#   2. cover_column; class of measurment, 'd' if dark cover, 
#   't' if transparent, 
#   3.quality; 1 if good meaurment 2 if critical, (highly faulty classification)
#   4.sec_index; a number counting up for every aoi


def find_aoi(content,tolerance = 5):
    
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
    area_of_interest  = np.zeros(content.shape[0])
    quality = np.zeros(content.shape[0])
    cover_column = pd.Series(' ' for _ in range(content.shape[0]))
    sec_index = np.zeros(content.shape[0])

    
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
            area_of_interest[best_index:best_index+aoi_length+1] = 1
            cover_column[best_index:best_index+aoi_length+1] = cover
            sec_index[best_index:best_index+aoi_length+1] = 5*(np.arange(aoi_length+1)+1)
            if cover == 'd' and best_slope < 0:
                quality[best_index:best_index+aoi_length+1] = 2
            else:
                quality[best_index:best_index+aoi_length+1] = 1

    markers = pd.DataFrame(index = content.index,
                            columns = ['area_of_interest','cover_column',
                                        'quality','sec_index'])
    

    markers['area_of_interest'] = area_of_interest
    markers['cover_column'] = cover_column
    markers['quality'] = quality
    markers['sec_index'] = sec_index
    return markers

#visualizing
#Creates a simple plot of the result weher logger area is marked yellow
#and aoi green.
def vis(content,area_of_interest):
    
    print('Visualizing...')
    
    import matplotlib
    import matplotlib.pyplot as plt

    x = np.arange(content.shape[0])

    plt.plot(x,content.CO2.values-400,color = 'black')

    plt.bar(x,area_of_interest*500,alpha = 0.5,color = 'green')
    norm_logger = (np.sign(content.logger.values)+1)

    plt.bar(x,norm_logger*250,alpha= 0.4,color = 'yellow')
    plt.ylabel('CO2 [ppm - 400]')
    plt.xlabel('Measurment_index')

    plt.show()


#Writes the content and the markes Dataframe into a singe Dataframe
#and creates a .xlsx sheet from it.
#Parameters:
#   result_path: string
#   Path to where the final result should be stored
#   content: pandas Data Frame
#   Data as it is read and formated comming from the read_file function
#   markers: pandas Data Frame
#   Data Frame with the markers as created by the find_aoi function. 
def write_file(result_path,content,markers):
    
    print('Writing the final file...')

    result = pd.DataFrame(index = content.index)
    result['date'] = [x.date() for x in content.timestamp]
    result['time'] = [x.time() for x in content.timestamp]
    result['PAR'] = content.PAR
    result['CO2'] = content.CO2
    result['temperature'] = content.temp
    result['chamber'] = markers.cover_column
    result['Logger'] = content.logger
    result['sec_index'] = markers.sec_index
    result['AoI'] = markers.area_of_interest
    result['quality'] = markers.quality
    result['H2O'] = content.H2O

    writer = pd.ExcelWriter(result_path)
    result.to_excel(writer,'Sheet1')
    writer.save()
    
#determines the names to be used when in single file mode.
#Returns: 
#   path: string
#   Path to where the raw data is stored.
#   return_path: string
#   Path to where the result shopuld be written.
def find_names():
    
    if len(sys.argv) == 1:
        print('Requires path to raw file.')
        print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
        raise 
        
    if sys.argv[2][-5:] == '.xlsx':
        if sys.argv[1][-4:] == '.txt':
            return sys.argv[1],sys.argv[2]
        else:
            print('Requires txt file as input path and .xlsx file as output path.')
            print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
            raise
        
    else:
        if sys.argv[1][-4:] == '.txt':
            return sys.argv[1],sys.argv[1][:-4]+'.xlsx'
        else:
            print('Requires txt file')
            print('Usage: parser.py "path to raw .txt file" ["desired path to result file"]')
            raise 

if __name__  == '__main__':
    
    #If it is passed a directory, every file in the directory with a .txt extension is parsed.
    #When a Problem arises it just screams once and resumes with the next file. 
    #All files are stored with same name but now with an .xlsx extension.
    #Visualizes if last parameter is '-v'.
    if os.path.isdir(sys.argv[1]):

        print('Formating all files in '+str(sys.argv[1])+' directory.')

        for file in os.listdir(sys.argv[1]):
            if file[-4:] == '.txt':

                try:
                    path = sys.argv[1]+'/'+file
                    result_path = sys.argv[1]+'/'+file[:-4]+'.xlsx'

                    print('---- Now focusing on '+str(file)+' -------')

                    content = read_file(path)
                    markers = find_aoi(content)
                    write_file(result_path,content,markers)

                    if sys.argv[-1] == '-v':
                        vis(content,markers.area_of_interest)
                except:
                    print('PROBLEMS WITH FILE: '+str(file))


    else:
        path,result_path = find_names()
        
        content = read_file(path)
        markers = find_aoi(content)

        write_file(result_path,content,markers)
        
        if sys.argv[-1] == '-v':
            vis(content,markers.area_of_interest)













