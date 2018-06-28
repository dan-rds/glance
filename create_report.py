'''
-------------------------------------
create_report.py

The basic structure is as follows:
  * Each type of hardware has its own method
    typically this means callng one large command and spliting it a ton.
  * This data are stored in a dictionary and returned.
  * Each of these hardware types are inserted into the larger system.
  * The resulting dictionary is written to a file in ./reports/<network name>/

    by Daniel Richards (ddrichar@ucsc.edu)
       on 6-23-2018

P.S. After working with files whose naming conventions I wouldn't wish on my
worst enemy, I wrote these programs with VERY specific naming.  
--------------------------------------
'''
from plumbum import local
from plumbum.cmd import echo, nslookup, sudo
from operator import itemgetter
import yaml
import json
import datetime
import os
import sys
import re
import csv

def double_split(start, end, string_cmd):
      return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()

def format_table(dic):
      output = {}
      for k, v in dic.iteritems():
            new_key = k.title() if len(k) >4 else k.upper
            while '  ' in v:
                      v = v.replace('  ', ' ')
            output[k] = v
      return output

def get_nics():
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      net_arr = []
      for i in interfaces[:-1]:
	      output = local['ifconfig'](i).encode('ascii')
              nic_fields = {'name':i, "ip":' ', "dns_server": " ", "mac": ' ', "speed": ' '}
              try:
                    nic_fields['ip'] = double_split('inet addr:', '  ', output)
                    dns_lookup = nslookup(nic_fields["ip"])
                    dns_server_name = double_split("= ", ".\n", dns_lookup)
                    nic_fields["dns_server"] = dns_server_name
              except:
                    pass
              try:
                    nic_fields['mac'] = double_split('HWaddr ', '  \n', output)
              except:
                   pass
              try:
                nic_fields['speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()
              except:
                nic_fields['speed'] = "NA"  
                
              net_arr.append(nic_fields)

      return net_arr
            
def get_gpus():
      gpu_count = local["lspci"]().count("VGA")
      #BEWARE DANIEL this doesnt reflect true gpu count remember the ASPEED device
      gpus = []
      for gpu_num in range(0, gpu_count-1):
            gpu_fields = {}
            arg_arr = ['-i', str(gpu_num),
                       '--query-gpu=gpu_name,gpu_bus_id,vbios_version,serial,memory.total',
                       '--format=csv,noheader,nounits']
            gpu_info=local.get("nvidia-smi").run(arg_arr)[1].encode("ascii")
            gpu_arr = gpu_info.strip().split(", ")
            gpu_fields["name"] = gpu_arr[0]
            gpu_fields['pciid'] = gpu_arr[1]
            gpu_fields['bios version'] = gpu_arr[2]
            gpu_fields['serial'] = gpu_arr[3]
            gpu_fields['memory'] = gpu_arr[4]

            gpus.append(gpu_fields)
      return gpus


def get_cpus():
      
      cpu_fields = {}
      cpus = []
      cpu_info = local["lscpu"]().encode("ascii")
      soc_count = int(double_split("Socket(s):", "\n", cpu_info))
      cpu_fields["model"] = double_split("Model name:", "\n", cpu_info)
      cpu_fields["cores"] = int(double_split("CPU(s):", "\n", cpu_info))/soc_count
      cpu_fields["clock"] = double_split("CPU max MHz:", "\n", cpu_info)
      cpu_fields["architecture"] = double_split("Architecture:", "\n", cpu_info)
      cpu_fields["threads per core"] = double_split("Thread(s) per core:", "\n", cpu_info)
      for socket_index in range(soc_count):
            cpu_fields["socket"] = socket_index
            cpus.append(cpu_fields.copy())

      return cpus

def get_mem():
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = double_split("MemTotal:", "\n", mem_info)
      mem_fields["total"] = mem_info

      return mem_fields

def get_disks():
      all_disks =  []
      try:
            all_disks = sudo["/usr/local/bin/megacli"]('-pdlist -a0').split("\n\n")
      except:
            all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n")
#      all_disks = sudo["/usr/local/bin/megacli"]('-pdlist -a0').split("\n\n") 
      n=0
      disk_array = []

      for x in all_disks:
            if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
                  try:
                        disk_info = {}
                        disk_info["id"] = double_split("evice Id:", "\n", x)
                        disk_info["firmware"] = double_split("Firmware Level:", "\n", x)
                        disk_info["size"] = double_split("Raw Size:", "[|\n", x)
                        disk_info["serial"] = double_split("Inquiry Data:", "\n", x)
                        disk_array.append(disk_info)
                        n+=1
                        
                  except:
                        pass
      return disk_array

def get_sys():
      sys_fields = {}
      host_name = local["hostname"]().encode("ascii").strip()
      sys_fields["hostname"] = host_name
      sys_fields["bios version"] = double_split("Version:", "\n", sudo["dmidecode"]())
      sys_fields["vendor"] = double_split("Vendor:", "\n", sudo["dmidecode"]())
      sys_fields["network"] = local["/home/obs/bin/whereami"]().encode("ascii").strip().title() # Matt's script
      task_type = ''
      if 'c' in host_name:
            task_type = 'COMPUTE'
      elif 's' in host_name:
            task_type = 'STORAGE'
      else:
            task_type = 'HEAD' 
      sys_fields["type"] = task_type

      return sys_fields


def write_arr_to_csv(arr, hw_class, network, name):
  if arr == None or len(arr) <1:
    return
  if type(arr) != list:
      arr = [arr]
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



nic_info_dict = get_nics()
gpu_info_dict = get_gpus()
cpu_info_dict = get_cpus()
mem_info_dict = get_mem()

print mem_info_dict
sys_info_dict = get_sys()
copy_sys = sys_info_dict.copy()

sys_info_dict.update({"GPU(s)":gpu_info_dict})
sys_info_dict.update({"NICs":nic_info_dict})
sys_info_dict.update({"CPU":cpu_info_dict})
sys_info_dict.update({"Memory":mem_info_dict})
disk_info_dict = {}
if 'h' not in sys_info_dict['hostname']: #Head nodes dont have megacli >:(
      disk_info_dict = get_disks()
      sys_info_dict.update({"Disks": disk_info_dict})
      


today = str(datetime.date.today())
name  = sys_info_dict["hostname"] 
network = sys_info_dict["network"]

with open("reports/" + network +"/"+ name +'_'+ today +'.yaml', 'w') as outfile:
      yaml.dump({"device":sys_info_dict}, outfile, default_flow_style=False)


write_arr_to_csv(nic_info_dict, "NICs", network, name)
write_arr_to_csv(cpu_info_dict, "CPUs", network, name)
write_arr_to_csv(gpu_info_dict, "GPUs", network, name)
write_arr_to_csv(disk_info_dict, "Disks", network, name)
write_arr_to_csv(mem_info_dict, "Memory", network, name)
write_arr_to_csv(copy_sys, "SYS", network, name)


