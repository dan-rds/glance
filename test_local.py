from plumbum.cmd import grep
try:
	g = grep["blgc00"]("local_group.txt")
except:
	g = None
print g

#grep blh0 csv_data/NICs.csv