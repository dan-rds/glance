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
from beeprint import pp
import os
import sys
import re


shit_i_care_about = ["name", "mac", "model", "serial", "speed", "make", "diskID", "amount", "ip", "clock", "cores"];

def double_split(start, end, string_cmd):
      return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()

def get_nics():
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      net_arr = []

      for i in interfaces[:-1]:
              output = local['ifconfig'](i).encode('ascii')
              nic_fields = {'name': i}
#	      nic_fields['ip'] = double_split('inet addr:', '  ', output)
              nic_fields['stroke'] = 1
              nic_fields['type'] = "nic"
              
              try:
                    nic_fields['ip'] = double_split('inet addr:', '  ', output)
                    dns_lookup = nslookup(nic_fields["ip"])
                    dns_server_name = double_split("= ", ".\n", dns_lookup)
                    nic_fields["dns server"] = dns_server_name
              except:
                    pass
              try:
                    nic_fields['mac'] = double_split('HWaddr ', '  \n', output)
              except:
                    pass
              try:
                nic_fields['speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()
                nic_fields['stroke'] = int(nic_fields["speed"])/100
              except:
                nic_fields['speed'] = "NA"
              row = []
              for k,v in nic_fields.iteritems():
                    if k in shit_i_care_about:
                          row.append(k.title()+ ": "+ str(v))
              nic_fields["tt_info"] = row
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
            gpu_fields['pciid'] = gpu_arr[1]
            gpu_fields['stroke'] = 1
            gpu_fields['node_type'] = "leaf"
            gpu_fields["type"] = "gpu"
            gpu_fields['bios version'] = gpu_arr[2]
            gpu_fields['serial'] = gpu_arr[3]

            
            row = []
            for k,v in gpu_fields.iteritems():
                  if k in shit_i_care_about:
                        row.append(k.title()+ ": "+ str(v))
            gpu_fields["tt_info"] = row
            gpus.append(gpu_fields)
         
      return gpus

def get_cpus():
      
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
            row = []
            for k,v in cpu_fields.iteritems():
                if k in shit_i_care_about:
                    row.append(k.title()+ ": "+ str(v))
            cpu_fields["tt_info"] = row
            cpus.append(cpu_fields.copy())
      return cpus

def get_mem():
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = double_split("MemTotal:", "\n", mem_info)
      mem_fields["tt_info"] = "Memory: " + mem_info
      mem_fields["name"] = "Memory"
      mem_fields["stroke"] = 1

      return mem_fields

def get_disks():
      
      all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n") 
      disk_array = []

      for x in all_disks[:-1]:
            if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
                  try:
                        disk_fields = {}
                        disk_fields["diskID"] = double_split("evice Id:", "\n", x)
                        disk_fields["name"] = "d" + disk_fields["diskID"]
                        disk_fields['stroke'] = 1
                        disk_fields['type'] = "disk"
                        disk_fields["firmware"] = double_split("Firmware Level:", "\n", x)
                        disk_fields["size"] = double_split("Raw Size:", "\n", x)
                        disk_fields["serial"] = double_split("Inquiry Data:", "\n", x)

                        row = []
                        for k,v in disk_fields.iteritems():
                            if k in shit_i_care_about:
                                row.append(k.title()+ ": "+ str(v))
                        disk_fields["tt_info"] = row
                        disk_array.append(disk_fields)

                  except:
                         print "ERROR IN DISK READ\n", x
                         
      
      return disk_array
     
def get_sys():
      sys_fields = {}
      host_name = local["hostname"]().encode("ascii").strip()
      sys_fields["hostname"] = host_name
      sys_fields["bios version"] = double_split("Version:", "\n", sudo["dmidecode"]())
      sys_fields["vendor"] = double_split("Vendor:", "\n", sudo["dmidecode"]())
      sys_fields["type"] = "computer"
      sys_fields['stroke'] = 1
      sys_fields["network"] = local["/home/obs/bin/whereami"]().encode("ascii").strip().title()
      task_type = ''
      if 'c' in host_name:
            task_type = 'COMPUTE'
      elif 's' in host_name:
            task_type = 'STORAGE'
      else:
            task_type = 'HEAD' 
      sys_fields["type"] = task_type
      row = []
      for k,v in sys_fields.iteritems():
          row.append(k.title()+ ": "+ str(v))

      return sys_fields


nic_info_dict = get_nics()
nic_info_dict = sorted(nic_info_dict, key=itemgetter('stroke')) #looks better in tree

gpu_info_dict = get_gpus()
cpu_info_dict = get_cpus()
mem_info_dict = get_mem()
sys_info_dict = get_sys()

sys_info_dict["children"]=[]
sys_info_dict["children"].append({"name": "GPUs","stroke":1, "children":gpu_info_dict})
sys_info_dict["children"].append({"name": "NICs","stroke":1, "children":nic_info_dict})
sys_info_dict["children"].append({"name": "CPUs", "stroke":1,"children":cpu_info_dict})
sys_info_dict["children"].append(mem_info_dict)

if 'h' not in sys_info_dict['hostname']:  #Head nodes dont have megacli >:(
      disk_info_dict = get_disks()
      sys_info_dict["children"].append({"name": "Disks", "stroke":1,"children": disk_info_dict}) 
      

name  = sys_info_dict["hostname"] 
network = sys_info_dict["network"] 
with open( "tree_data/" + network + "/tree_" + name +'.json', 'w') as outfile:
      json.dump(sys_info_dict, outfile, indent=4)

