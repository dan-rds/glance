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

shit_i_care_about = ["name", "mac", "model", "serial", "speed", "make", "diskID", "amount", "ip", "clock", "cores"];
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
      return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()

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
def get_nics(csv_rows):
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      net_arr = []

      for i in interfaces[:-1]:
              row = csv_fields.copy()
              output = local['ifconfig'](i).encode('ascii')
              nic_fields = {'name':i, "ip":' ', "dns_server": " ", "mac": ' ', "speed": ' '}

              # row["Name"] = nic_fields['name']
              nic_fields['stroke'] = 1
              nic_fields['type'] = "nic"
              # row["Classification"] = "Hardware, NIC"
              
              try:
                    nic_fields['ip'] = double_split('inet addr:', '  ', output)
                    # row["Other"] = "ip: " + nic_fields['ip']
                    dns_lookup = nslookup(nic_fields["ip"])

                    dns_server_name = double_split("= ", ".\n", dns_lookup)
                    nic_fields["dns_server"] = dns_server_name
              except:
                    pass
              try:
                    nic_fields['mac'] = double_split('HWaddr ', '  \n', output)
                    # row["Serial Number"] = "MAC: " + nic_fields['mac']
              except:
                    pass
              try:
                nic_fields['speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()

                nic_fields['stroke'] = int(nic_fields["speed"])/100
              except:
                nic_fields['speed'] = "NA"
              # row["Speed/Capacity"] = nic_fields['speed']
              tooltip = []
              csv_rows.append(flatten(nic_fields))
              for k,v in nic_fields.iteritems():
                    if k in shit_i_care_about:
                          tooltip.append(k.title()+ ": "+ str(v))
              nic_fields["tt_info"] = tooltip
              net_arr.append(nic_fields)
              
      return net_arr
            
def get_gpus(csv_rows):
      gpu_count = local["lspci"]().count("VGA")
      #BEWARE DANIEL this doesnt reflect true gpu count remember the ASPEED device
      gpus = []
      for gpu_num in range(0, gpu_count-1):
            
            row = csv_fields.copy()
            gpu_fields = {}
            arg_arr = ['-i', str(gpu_num),
                       '--query-gpu=gpu_name,gpu_bus_id,vbios_version,serial,memory.total',
                       '--format=csv,noheader,nounits']
            gpu_info=local.get("nvidia-smi").run(arg_arr)[1].encode("ascii")
         
            
            gpu_arr = gpu_info.strip().split(", ")
            gpu_fields["name"] = gpu_arr[0]
            gpu_fields['pciid'] = gpu_arr[1]
            gpu_fields['pciid'] = gpu_arr[1]
            gpu_fields['stroke'] = 1
            gpu_fields['node_type'] = "leaf"
            gpu_fields["type"] = "gpu"
            gpu_fields['bios version'] = gpu_arr[2]
            gpu_fields['serial'] = gpu_arr[3]
            gpu_fields['memory'] = gpu_arr[4]

            # row["Name"] = gpu_fields["name"]
            # row["Make"] = "Nvidia"
            # row["Serial Number"] = gpu_fields["serial"]
            # row["Model"] = gpu_fields["name"]
            # row["Classification"] = "Hardware, GPU"
            # row["Speed/Capacity"] = "Memory: " + gpu_fields["memory"]

            csv_rows.append(flatten(gpu_fields))
            tooltip = []
            for k,v in gpu_fields.iteritems():
                  if k in shit_i_care_about:
                        tooltip.append(k.title()+ ": "+ str(v))
            gpu_fields["tt_info"] = tooltip
            gpus.append(gpu_fields)
         
      return gpus

def get_cpus(csv_rows):
      
      cpu_fields = {}
      cpus = []
      cpu_info = local["lscpu"]().encode("ascii")
      soc_count = int(double_split("Socket(s):", "\n", cpu_info))

      cpu_fields["model"] = double_split("Model name:", "\n", cpu_info)
      cpu_fields["name"] = cpu_fields["model"]
      cpu_fields["cores"] = int(double_split("CPU(s):", "\n", cpu_info))/soc_count
      cpu_fields["clock"] = double_split("CPU max MHz:", "\n", cpu_info)
      cpu_fields["architecture"] = double_split("Architecture:", "\n", cpu_info)
      cpu_fields["threads per core"] = double_split("Thread(s) per core:", "\n", cpu_info)
      cpu_fields['stroke'] = 1
      cpu_fields['type'] = "cpu"


      

      for c in range(soc_count):
            cpu_fields["socket"] = c

           # row = csv_fields.copy()
            # row["Name"] = cpu_fields["name"]
            # row["Make"] = cpu_fields["model"].split("[^a-zA-Z0-9_]")[0]
            # row["Serial Number"] = "Unknown"
            # row["Model"] = cpu_fields["name"]
            # row["Classification"] = "Hardware, CPU"
            # row["Speed/Capacity"] = "Clock: " + cpu_fields["clock"]
            # row["Other"] = "Socket: " + str(c)
            csv_rows.append(flatten(cpu_fields))
            tooltip = []
            for k,v in cpu_fields.iteritems():
                if k in shit_i_care_about:
                    tooltip.append(k.title()+ ": "+ str(v))
            cpu_fields["tt_info"] = tooltip
            cpus.append(cpu_fields.copy())
      return cpus

def get_mem(csv_rows):
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = double_split("MemTotal:", "\n", mem_info)
      mem_fields["tt_info"] = "Memory: " + mem_info
      mem_fields["name"] = "Memory"
      mem_fields["stroke"] = 1
      row = csv_fields.copy()
      # row["Name"] = "Memory"
      # row["Classification"] = "Hardware, Memory"
      # row["Speed/Capacity"] = mem_info

      csv_rows.append(flatten(mem_fields))
      return mem_fields

def get_disks(csv_rows):
      
      all_disks =  []
      try:
        all_disks = sudo["/usr/local/bin/megacli"]('-pdlist -a0').split("\n\n")
      except:
        all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n")      
      disk_array = []
      
      for x in all_disks[:-1]:
            if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
                 
                  try:
                        row = csv_fields.copy()

                        disk_fields = {}
                        disk_fields["diskID"] = double_split("evice Id:", "\n", x)
                        disk_fields["name"] = "Disk: " + disk_fields["diskID"]
                        disk_fields['stroke'] = 1
                        disk_fields['type'] = "disk"
                        disk_fields["firmware"] = double_split("Firmware Level:", "\n", x)
                        disk_fields["size"] = double_split("Raw Size:", "\n", x)
                        disk_fields["serial"] = double_split("Inquiry Data: ", "\n", x)

                       
                        name = disk_fields["name"]
                        # row["Name"] = "Hitachi" if 'Hitachi' in name else "Samsung"
                        # row["Classification"] = "Hardware, Disk"
                        # row["Speed/Capacity"] = disk_fields["size"]
                        # row["Serial Number"] = disk_fields["serial"].split(' ')[1]
                        # row["Make"] = disk_fields["serial"].replace("[^a-zA-Z_]", '')
                        csv_rows.append(flatten(disk_fields))
                        tooltip = []
                        for k,v in disk_fields.iteritems():
                            if k in shit_i_care_about:
                                tooltip.append(k.title()+ ": "+ str(v))
                        disk_fields["tt_info"] = tooltip
                        disk_array.append(disk_fields)

                  except:
                         print "ERROR IN DISK READ\n", x
                         
      
      return disk_array

def get_sys(csv_rows ,observatory, host):
      sys_fields = {}
      row = csv_fields.copy()
      host[0] = local["hostname"]().encode("ascii").strip()
      sys_fields["hostname"] = host[0] 
      sys_fields["bios version"] = double_split("Version:", "\n", sudo["dmidecode"]())
      sys_fields["vendor"] = double_split("Vendor:", "\n", sudo["dmidecode"]())
      sys_fields["type"] = "computer"
      sys_fields['stroke'] = 1
      obs_name = local["/home/obs/bin/whereami"]().encode("ascii").strip().title()
      if(obs_name == 'gbt'):
        obs_name = obs_name.upper()
      observatory[0] = obs_name
      sys_fields["network"] = obs_name
      task_type = ''
      if 'c' in host[0]:    # I know, not elegant
            task_type = 'COMPUTE'
      elif 's' in host[0]:
            task_type = 'STORAGE'
      else:
            task_type = 'HEAD' 
      sys_fields["type"] = task_type

      # row["Name"] = host[0]
      # row["Make"] = sys_fields["vendor"]
      # row["Classification"] = "System, " + task_type
      # row["Other"] = "Bios version: " + sys_fields["bios version"]

      csv_rows.append(flatten(sys_fields))

      tooltip = []
      for k,v in sys_fields.iteritems():
        if 'stroke' not in k.lower():
          tooltip.append(k.title()+ ": "+ str(v))
      sys_fields["tt_info"] = tooltip
      return sys_fields

nic_array = []
nic_info_dict = get_nics(nic_array)
nic_info_dict = sorted(nic_info_dict, key=itemgetter('stroke')) #looks better in tree

gpu_array = []
gpu_info_dict = get_gpus(gpu_array)
cpu_array = []
cpu_info_dict = get_cpus(cpu_array)

mem_array = []
mem_info_dict = get_mem(mem_array)

obs =['']
host = ['']
sys_array = []
sys_info_dict = get_sys(sys_array, obs, host)

sys_info_dict["children"]=[]
sys_info_dict["children"].append({"name": "GPUs","stroke":1, "children":gpu_info_dict})
sys_info_dict["children"].append({"name": "NICs","stroke":1, "children":nic_info_dict})
sys_info_dict["children"].append({"name": "CPUs", "stroke":1,"children":cpu_info_dict})
sys_info_dict["children"].append(mem_info_dict)
disk_array = []
if 'h' not in sys_info_dict['hostname']:  #Head nodes dont have megacli >:(
  
      disk_info_dict = get_disks(disk_array)
      sys_info_dict["children"].append({"name": "Disks", "stroke":1,"children": disk_info_dict}) 
      

name  = sys_info_dict["hostname"] 
network = sys_info_dict["network"]
print name, network
with open( "tree_data/" + network + "/tree_" + name +'.json', 'w') as outfile:
      json.dump(sys_info_dict, outfile, indent=4)



# write_arr_to_csv(nic_array, "NICs", network, name)
# write_arr_to_csv(cpu_array, "CPUs", network, name)
# write_arr_to_csv(gpu_array, "GPUs", network, name)
# write_arr_to_csv(disk_array, "Disks", network, name)
# write_arr_to_csv(mem_array, "Memory", network, name)
# write_arr_to_csv(sys_array, "SYS", network, name)




