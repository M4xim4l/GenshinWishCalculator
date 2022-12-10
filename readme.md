# Genshin Impact Gatcha Statistics

In this repo, we use a Monte Carlo Simulation in Numpy to estimate various statistics for Genshin Impact's Gatcha system. 
We calculate the probability of ending up at an exact constellation for one specific banner 4* or 5* after N pulls 
(1st column) and also the probability of getting at least constellation X after N pulls (2nd column). The third column
contains the average number of drawn copies for a specific character after N pulls.
The simulation always assumes that we start from 0 pity without a guaranteed 50/50 win.

The individual rates are taken from [Hoyolab](https://www.hoyolab.com/article/497840). In particular, the average
chance of getting a 5* character before entering soft-pity at pull 74 is always 0.051. Starting at pull 74, soft pity
starts and linearly increases the chances of getting a 5* at each pull by 6% until we get a guaranteed 5* at 90 pulls.
For 4* characters, a similar soft pity system starts at 9 pulls after not getting at least a single 4* or 5* and results
in the well known guarantee for getting a 4* character every 10 pulls. For both 4* and 5* characters, the simulation
also takes into account that at least every other character is guaranteed to be from the banner. 

To run the simulation simply run:

> python calculate_wish_stats.py

The script will output Tables containing Tables containing both the probabilities of getting exactly constellation N
and at least constellation N after a certain number of pulls. For example, the probabilities of getting a specific 
constellation after N pulls are:

5* - Probability of getting exactly constellation X

 Pulls |   C0   |   C1   |   C2   |   C3   |   C4   |   C5   |   C6   
-------|--------|--------|--------|--------|--------|--------|--------
   50  | 0.1376 | 0.0103 | 0.0005 | 0.0000 | 0.0000 | 0.0000 | 0.0000 
  100  | 0.5461 | 0.0792 | 0.0059 | 0.0004 | 0.0000 | 0.0000 | 0.0000 
  150  | 0.5493 | 0.2058 | 0.0332 | 0.0034 | 0.0003 | 0.0000 | 0.0000 
  200  | 0.4241 | 0.4289 | 0.1259 | 0.0190 | 0.0019 | 0.0002 | 0.0000 
  250  | 0.1312 | 0.5099 | 0.2824 | 0.0656 | 0.0097 | 0.0011 | 0.0001 
  300  | 0.0509 | 0.3681 | 0.3847 | 0.1553 | 0.0350 | 0.0053 | 0.0007 
  350  | 0.0000 | 0.1829 | 0.4205 | 0.2819 | 0.0926 | 0.0188 | 0.0033 
  400  | 0.0000 | 0.0465 | 0.3290 | 0.3775 | 0.1832 | 0.0517 | 0.0121 
  450  | 0.0000 | 0.0134 | 0.1867 | 0.3711 | 0.2794 | 0.1129 | 0.0364 
  500  | 0.0000 | 0.0000 | 0.0734 | 0.2943 | 0.3459 | 0.1973 | 0.0890 
  550  | 0.0000 | 0.0000 | 0.0176 | 0.1792 | 0.3425 | 0.2784 | 0.1823 
  600  | 0.0000 | 0.0000 | 0.0038 | 0.0849 | 0.2695 | 0.3222 | 0.3196 
  650  | 0.0000 | 0.0000 | 0.0000 | 0.0285 | 0.1728 | 0.3125 | 0.4863 
  700  | 0.0000 | 0.0000 | 0.0000 | 0.0068 | 0.0889 | 0.2503 | 0.6539 
  750  | 0.0000 | 0.0000 | 0.0000 | 0.0011 | 0.0360 | 0.1667 | 0.7961 
  800  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0107 | 0.0916 | 0.8977 
  850  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0025 | 0.0416 | 0.9559 
  900  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0004 | 0.0149 | 0.9847 
  950  | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0040 | 0.9960 
  1000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0009 | 0.9991 
  1050 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0001 | 0.9999 
  1080 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 


The results are also summarized in a plot and saved to 'simulation_results.png':

![](simulation_results.png)

By default, we simulate 1.5 million trials of 1080 pulls. 
Running the script with default arguments has a peak memory consumption larger than 20GB. To reduce this, you can
simply run the simulation with less trials.

> python calculate_wish_stats.py --trials N --chain_length M

The project dependencies are given in 'requirements.txt'. To install them from the included file, simply use:

> pip install -r requirements.txt


