# hpc-usage
Code to evaluate python package usage on HPC systems using lsof.


`grab-open-files.py` is a python script that looks for python packages opened by different processes on linux HPC systems.
The script runs `lsof` and filters for files located downstream of the 'site-packages' directory, which is where *most* installed python packages are located.
For python packages identified from this filtering, the process id, username and python package are extracted.
The environment of the processes id is then checked for the environment variable 'OPTOUT'. If `OPTOUT=true` this indicates the user has chosen to opt out of the reporting.
This line is therefore skipped and not processed further.
If the user has not opted out, their username is put into a hash function ([SHA-256](https://en.wikipedia.org/wiki/SHA-2)) combined with a [pepper](https://en.wikipedia.org/wiki/Pepper_(cryptography)) 
which is read from an environment variable called 'PEPPER', set by the HPC opperator. This ensures the team using the analysis cannot reverse the hash to recover the users details.
For users that have not opted out, the script will write a text file called `package-report.txt` that contains the process id, psudoanonymised username, python package used and a time stamp for when the sample was taken.
The script will run for $X$ amount of time and sample `lsof` every $N$ seconds, appending the results to `package-report.txt`. The output of this will allow us to see what packages are being used, in what processes and for how long.
