from plumbum import local
from plumbum.cmd import echo, nslookup, sudo
import scraping
from beeprint import pp
import os
import sys
shit_i_care_about = ["name", "mac", "model", "serial", "speed", "make", "diskID", "amount", "ip", "clock", "cores"];
def get_nics(nic_tooltip_info):
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      net_arr = []
      for i in interfaces[:-1]:
	      output = local['ifconfig'](i).encode('ascii')
              nic_fields = {'name':i}
	      nic_fields['ip'] = scraping.get_between('inet addr:', '  B|  M', output)
              nic_fields['stroke'] = 1
              nic_fields['type'] = "nic"
              
              try:
                    dns_lookup = nslookup(nic_fields["ip"])
                    dns_server_name = d_split("= ", ".\n", dns_lookup)
                    nic_fields["dns server"] = dns_server_name
              except:
                    pass
              nic_fields['mac'] = scraping.get_between('HWaddr ', '  \n', output)
              
              try:
                nic_fields['speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()
                nic_fields['stroke'] = int(nic_fields["speed"])/100
              except:
                nic_fields['speed'] = "NA"
              row = []
              for k,v in nic_fields.iteritems():
                    if k in shit_i_care_about:
                          row.append(k.title()+ ": "+ str(v))
              net_arr.append(nic_fields)
              nic_rows.append(row)
      return net_arr
            
def get_gpus(gpu_tooltip_info):
      gpu_count = local["lspci"]().count("VGA")
      #BEWARE DANIEL this doesnt reflect true gpu count remember the ASPEED device
      gpus = []
      for gpu_num in range(0, gpu_count-1):
            gpu_fields = {}
            arg_arr = ['-i', str(gpu_num),
                       '--query-gpu=gpu_name,gpu_bus_id,vbios_version,serial,memory.total',
                       '--format=csv,noheader,nounits']
            gpu_info=local.get("nvidia-smi").run(arg_arr)[1].encode("ascii")
            import re
            
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
 #           gpu_node = Node("GPU", **gpu_fields)
            gpus.append(gpu_fields)
            row = []
            for k,v in gpu_fields.iteritems():
                  if k in shit_i_care_about:
                        row.append(k.title()+ ": "+ str(v))
            gpu_tooltip_info.append(row)
      return gpus

def d_split(start, end, string_cmd):
      return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()

def get_cpus(cpu_tooltip_info):
      
      cpu_fields = {}
      cpus = []
      cpu_info = local["lscpu"]().encode("ascii")
      soc_count = int(d_split("Socket(s):", "\n", cpu_info))
      #cores_in_soc = int(d_split("Core(s) per socket:", "\n", cpu_info))
      cpu_fields["model"] = d_split("Model name:", "\n", cpu_info)
      cpu_fields["name"] = cpu_fields["model"]
      cpu_fields["cores"] = int(d_split("CPU(s):", "\n", cpu_info))/soc_count
      cpu_fields["clock"] = d_split("CPU max MHz:", "\n", cpu_info)
      cpu_fields["architecture"] = d_split("Architecture:", "\n", cpu_info)
      cpu_fields["threads per core"] = d_split("Thread(s) per core:", "\n", cpu_info)
      cpu_fields['stroke'] = 1
      cpu_fields['type'] = "cpu"
      for c in range(soc_count):
            cpu_fields["socket"] = c
            cpus.append(cpu_fields.copy())
            row = []
                for k,v in cpu_fields.iteritems():
                    if k in shit_i_care_about:
                          row.append(k.title()+ ": "+ str(v))
            cpu_tooltip_info.append(row)
            #cpu_node = Node("CPU", **cpu_fields)
      return cpus

def get_mem():
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = d_split("MemTotal:", "\n", mem_info)
      mem_fields["total"] = mem_info
      mem_fields["name"] = "Memory"
      mem_fields["stroke"] = 1
      #mem_node = Node("Memory", **mem_fields)
      return mem_fields

def get_disks():
      
      all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n") 
      n=0
      disk_array = []
#      print all_disks[1]
      for x in all_disks:
            if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
                  try:
                        disk_info = {}
                        disk_info["diskID"] = d_split("evice Id:", "\n", x)
                        disk_info["name"] = "d" + disk_info["diskID"]
                        disk_info['stroke'] = 1
                        disk_info['type'] = "disk"
                        disk_info["firmware"] = d_split("Firmware Level:", "\n", x)
                        disk_info["size"] = d_split("Raw Size:", "\n", x)
                        disk_info["serial"] = d_split("Inquiry Data:", "\n", x)
                        #print disk_info
                        disk_array.append(disk_info)
                        n+=1
                  except:
                         print "ERROR IN DISK READ\n", x
                         
      
      return disk_array
      #      disk_fields = {}
      #      n+=1
      #      print x
     #       print"--------------------------------"
#      print all_disks.count('Size: '), n
def get_sys():
      sys_info = {}
      host_name = local["hostname"]().encode("ascii").strip()
      sys_info["hostname"] = host_name
      sys_info["bios version"] = d_split("Version:", "\n", sudo["dmidecode"]())
      sys_info["vendor"] = d_split("Vendor:", "\n", sudo["dmidecode"]())
      sys_info["type"] = "computer"
      sys_info['stroke'] = 1
      sys_info["network"] = local["/home/obs/bin/whereami"]().encode("ascii").strip().title()
      task_type = ''
      if 'c' in host_name:
            task_type = 'COMPUTE'
      elif 's' in host_name:
            task_type = 'STORAGE'
      else:
            task_type = 'HEAD' 
      sys_info["type"] = task_type
    #  print sys_info
      return sys_info
nic_rows = []
nic_array = get_nics(nic_rows)
for i in nic_rows:
      print i

from operator import itemgetter
nic_array = sorted(nic_array, key=itemgetter('stroke'))


gpu_array = get_gpus()
cpu_array = get_cpus()
mem_array = get_mem()
sys_array = get_sys()

sys_array["children"]=[]
sys_array["children"].append({"name": "GPUs","stroke":1, "children":gpu_array})
sys_array["children"].append({"name": "NICs","stroke":1, "children":nic_array})
sys_array["children"].append({"name": "CPUs", "stroke":1,"children":cpu_array})
sys_array["children"].append(mem_array)
if 'h' not in sys_array['hostname']:
      disk_array = get_disks()
      sys_array["children"].append({"name": "Disks", "stroke":1,"children": disk_array}) #.update({"Disks": disk_array})
      
import yaml
import json

name  = sys_array["hostname"] +'_'
network = sys_array["network"] 
with open( "tree_data/" + network + "/tree_" + name +'.yml', 'w') as outfile:
      json.dump(sys_array, outfile, indent=4)

