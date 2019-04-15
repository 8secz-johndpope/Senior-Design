import csv
from statistics import *

csv_list = []
try:
	with open('legitimacy_values.csv', 'r', errors = 'ignore') as legit_file:
	    csv_list = list(csv.reader(legit_file))
except:
	pass
csv_list = [value for pair in csv_list for value in pair]
all_values = csv_list[1::2]
all_values = [float(value) for value in all_values]
positive_values = [value for value in all_values if value>0.15]
negative_values = [value for value in all_values if value<-0.15]
indeterminate_values = [value for value in all_values if -0.15<=value<=0.15]


percentage = len(all_values)/4152
header = 'TEAM LEGITIMACY CHECK STATISTICS'
all_results = str(len(all_values)) + ' of the 4152 (%' + str(round(percentage,4)*100) +') teams of their associated whitepapers in the original databank were checked'
mean_result = 'Mean Rating: ' + str(round(mean(all_values), 4)) + ', Median Rating: ' + str(round(median(all_values), 4)) + ', Variance: ' + str(round(variance(all_values), 4))
pos_results = 'Number of team ratings indicating no suspicion: ' + str(len(positive_values)) + " => %" + str(round(len(positive_values)/len(all_values), 4)*100) + " of all teams"
neg_results = 'Number of team ratings indicating suspicion: ' + str(len(negative_values)) + " => %" + str(round(len(negative_values)/len(all_values),4)*100) + " of all teams"
indeterminate_results = 'Number of indeterminate team ratings: ' + str(len(indeterminate_values)) + " => %" + str(round(len(indeterminate_values)/len(all_values), 4)*100) + " of all teams"
writeout_list = [header, all_results, mean_result, pos_results, neg_results, indeterminate_results]
with open('legitimacy_results.txt', 'w') as file:
	for item in writeout_list:
		file.write(f'{item}\n')