<h1>
Usage:
</h1>

<p>This is a python script that is parsing the .txt files, generated by the CO2 sensing device. It automatically finds areas of intrest, classifies the measurments as long/short measurments (i.e. transparent or dark covers) performs some cosmetic formating and exports the result in a .xlsx sheet.</p>

<h2>Formating single files:</h2>
<p>Using a command line tool, select the working directory where the <i>parser.py</i> file is stored. Format the file by typing:</p>

<b>.\parser.py 'path_to_source' [optional: 'path_to_destination' , -v ] </b>

<p>path_to_source should specify the path to the unformated .txt file that is supposed to be formated. Only files with a .txt extension are accepted. If no path_to_destination is provided, the result is stored at the same location that the source files is stored; the name is kept consistent, except for the extension that is changed from .txt to .xlsx. If path_to_destination is given the result file is stored under the given path, provided that the new filnemae has an .xlsx extension. If the <i>-v</i> flag is added, the result is also visualized using matplotlib.</p>

<h2>Formating batches of files:</h2>
<p>All the data that is supposed to be formated needs to be stored in a single directory. Using a command line tool, select the working directory where the <i>parser.py</i> file is stored. Format the files by typing:</p>

<b>.\parser.py 'path_to_directory' [optional: -v] </b>

<p>path_to_directory should specify the path to the directory holding the unformated .txt files that are supposed to be fomated. All the resulting files are named consitently, but have an .xlsx extension. If the programm is for some reson unable to process one of the files it notifies the user, but continous with the next file in line. If the <i>-v</i> flag is added, the result is also visualized using matplotlib.</p>

<h2>Testing wether all necessary libraries are installed.</h2>

<p>All testing file is provided, that checks that all necessary libraries are installed. To run the test, select the directory where the testing file is stored and type:</p>

<b>.\test.py </b>

<p> If there are libraries missing, you can install them for example by using anaconda.</p> 
