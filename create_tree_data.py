'''-------------------------------------
create_tree_data.py

Creates a JSON file with similar components as the reports. However, 
the tree date includes specific information, allowing the JSON file
(stored in ./tree_data) to be used to make a tree in d3 with minimal js.

    by Daniel Richards (ddrichar@ucsc.edu)
       on 6-23-2018
--------------------------------------
'''
from plumbum import local
from plumbum.cmd import echo, nslookup, sudo
from operator import itemgetter
import yaml
import json
import os
import sys
import re
import csv


csv_fields = {"Name": ' ', "Classification": ' ', "Make":' ', 'Model':' ', "Speed/Capacity": ' ', "Serial Number": ' ', "Path": ' ', 'Other':' '}

def flatten(old):
  new = {}
  for k,v in old.iteritems():
    if type(v) == str and 'gbt' in v.lower():
      v = 'GBT'
    if v != 'Tt_Info':
      new[k.title()] = v
  return new

def double_split(start, end, string_cmd):
    try:
        return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()
    except:
        return ' '

def write_arr_to_csv(arr, hw_class, network, name):
  if len(arr) <1:
    return
  for i in arr:
    #print i
    i["Path"] = network + " --> " + name
  with open("csv_data/" + hw_class + "_table_" + network + "_" + name +'.csv', 'wb') as f:  # Just use 'w' mode in 3.x
      w = csv.DictWriter(f, arr[0].keys())
      w.writeheader()
      for r in arr:
        try:
            w.writerow(r)
        except:
          pass

def add_tree_specific_fields(input_dict)
    hw_info = input_dict.copy()
    tooltip = []
    for k,v in hw_info.iteritems():
        tooltip.append(k.title()+ ": "+ str(v))
    hw_info["tt_info"] = tooltip
    hw_info['stroke'] = int(hw_info["speed"])/100 if "speed" in hw_info.keys() else 1


def get_nics():
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      nic_array = []

      for i in interfaces[:-1]:
              output = local['ifconfig'](i).encode('ascii')
              nic_fields = {}

              nic_fields['IP'] = double_split('inet addr:', '  ', output)
                  if nic_fields['IP'] != ' ':
                      dns_lookup = nslookup(nic_fields["IP"])
                      dns_server_name = double_split("= ", ".\n", dns_lookup)
                      nic_fields["DNS Server"] = dns_server_name
              nic_fields['MAC'] = double_split('HWaddr ', '  \n', output)
              try:
                  nic_fields['Speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()
              except:
                  nic_fields['Speed'] = "0"
              nic_array.append(nic_fields)

      return {"Name": "NICs", "children": nic_array}
            
def get_gpus():
      gpu_count = local["lspci"]().count("VGA") #BEWARE this doesn't reflect true gpu count remember the ASPEED device in lspci
      gpu_array = []

      for gpu_num in range(0, gpu_count-1):
            gpu_fields = {}
            arg_arr = ['-i', str(gpu_num),
                       '--query-gpu=gpu_name,gpu_bus_id,vbios_version,serial,memory.total',
                       '--format=csv,noheader,nounits']
            gpu_info = local.get("nvidia-smi").run(arg_arr)[1].encode("ascii")
         
            gpu_arr = gpu_info.strip().split(", ")
            gpu_fields["Name"] = gpu_arr[0]
            gpu_fields['PCIID'] = gpu_arr[1]
            gpu_fields["type"] = "gpu"
            gpu_fields['Vios Version'] = gpu_arr[2]
            gpu_fields['Serial'] = gpu_arr[3]
            gpu_fields['Memory'] = gpu_arr[4]

            gpu_array.append(gpu_fields)
         
      return {"Name": "GPUs", "children": gpu_array}

def get_cpus():
      
      cpu_fields = {}
      cpu_array = []
      cpu_info = local["lscpu"]().encode("ascii")
      soc_count = int(double_split("Socket(s):", "\n", cpu_info))

      cpu_fields["Model"] = double_split("Model name:", "\n", cpu_info)
      cpu_fields["Name"] = cpu_fields["model"]
      cpu_fields["Cores"] = int(double_split("CPU(s):", "\n", cpu_info))/soc_count
      cpu_fields["Clock"] = double_split("CPU max MHz:", "\n", cpu_info)
      cpu_fields["Architecture"] = double_split("Architecture:", "\n", cpu_info)
      cpu_fields["Threads Per Core"] = double_split("Thread(s) per core:", "\n", cpu_info)

      for soc in range(soc_count):
            cpu_fields["Socket"] = soc
            cpu_array.append(cpu_fields.copy())

      return {"Name": "CPUs", "children": cpu_array}

def get_mem():
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = double_split("MemTotal:", "\n", mem_info)

      return {"Name": "Memory", "Total": mem_info}

def get_disks():
      
      all_disks =  []
      try:
        all_disks = sudo["/usr/local/bin/megacli"]('-pdlist -a0').split("\n\n")
      except:
        all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n")      
      disk_array = []
      
      for x in all_disks[:-1]:
          if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
              try:
                    disk_fields = {}
                    disk_fields["diskID"] = double_split("evice Id:", "\n", x)
                    disk_fields["Name"] = "Disk: " + disk_fields["diskID"]
                    disk_fields["Firmware"] = double_split("Firmware Level:", "\n", x)
                    disk_fields["Size"] = double_split("Raw Size:", "\n", x)
                    disk_fields["Serial"] = double_split("Inquiry Data: ", "\n", x)
    
                    disk_array.append(disk_fields)
              except:
                     print "ERROR IN DISK READ\n", x

      return {"Name": "Disks", "children": disk_array}

def get_sys(observatory, host):
      sys_fields = {}
      host[0] = local["hostname"]().encode("ascii").strip()
      sys_fields["Hostname"] = host[0] 
      sys_fields["Bios Version"] = double_split("Version:", "\n", sudo["dmidecode"]())
      sys_fields["Vendor"] = double_split("Vendor:", "\n", sudo["dmidecode"]())
      obs_name = local["/home/obs/bin/whereami"]().encode("ascii").strip().title()
      if(obs_name == 'gbt'):
          obs_name = obs_name.upper()
      observatory[0] = obs_name
      sys_fields["network"] = obs_name

      task_type = ''
      if 'c' in host[0]:    # I know, not elegant
            task_type = 'COMPUTE'
      elif 'h' in host[0]:
            task_type = 'HEAD'
      else:
            task_type = 'STORAGE' 

      return {"Name": "System", "children": sys_fields}


nic_info_dict = get_nics()
nic_info_dict = sorted(nic_info_dict, key=itemgetter('stroke')) #looks better in tree

gpu_info_dict = get_gpus()
cpu_info_dict = get_cpus()
mem_info_dict = get_mem()
sys_info_dict = get_sys()

sys_info_dict["children"] = []
sys_info_dict["children"].append(gpu_info_dict)
sys_info_dict["children"].append(nic_info_dict)
sys_info_dict["children"].append(cpu_info_dict)
sys_info_dict["children"].append(mem_info_dict)

disk_array = []
if 'h' not in sys_info_dict['Hostname']:  #Head nodes dont have megacli >:(
      disk_info_dict = get_disks(disk_array)
      sys_info_dict["children"].append(disk_info_dict) 

name  = sys_info_dict["Hostname"] 
network = sys_info_dict["Network"]
print name, network
with open( "tree_data/" + network + "/tree_" + name +'.json', 'w') as outfile:
      json.dump(sys_info_dict, outfile, indent=4)




