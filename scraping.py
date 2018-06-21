from plumbum import local
import re

def pr_sc():
	print("SCRAPING")
def from_cmd(start_delim, end_delim, cmd, *args):
	output = local[cmd](*args)
	ret_array = []
	output = output.split(end_delim)
	for o in output:
		if start_delim in o:
			ret_array = (o.split(start_delim)[1])
        return ret_array

def get_between(start_delim, end_delim, str_cmd):
	output = re.split(end_delim, str_cmd)
	for op in output:
		if start_delim in op:
			return re.split(start_delim, op)[1]
	return False
