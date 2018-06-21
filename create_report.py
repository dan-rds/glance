from plumbum import local
from plumbum.cmd import echo, nslookup, sudo
import scraping
import os
import sys

def get_nics():
      inters = local["ls"]("/sys/class/net").encode("ascii")
      interfaces =  inters.split('\n')
      net_arr = []
      for i in interfaces[:-1]:
	      output = local['ifconfig'](i).encode('ascii')
              nic_fields = {'name':i}
	      nic_fields['ip'] = scraping.get_between('inet addr:', '  B|  M', output)
              try:
                    dns_lookup = nslookup(nic_fields["ip"])
                    dns_server_name = d_split("= ", ".\n", dns_lookup)
                    nic_fields["dns server"] = dns_server_name
              except:
                    pass
              nic_fields['mac'] = scraping.get_between('HWaddr ', '  \n', output)
              
              try:
                nic_fields['speed'] = local['cat']('/sys/class/net/'+ i +'/speed').encode("ascii").strip()
              except:
                nic_fields['speed'] = "NA"  
                
#              net_node = Node("NIC", **nic_fields)
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
            import re
            gpu_arr = gpu_info.strip().split(", ")
            gpu_fields["name"] = gpu_arr[0]
            gpu_fields['pciid'] = gpu_arr[1]
            gpu_fields['bios version'] = gpu_arr[2]
            gpu_fields['serial'] = gpu_arr[3]
            gpu_fields['memory'] = gpu_arr[4]
 #           gpu_node = Node("GPU", **gpu_fields)
            gpus.append(gpu_fields)
      return gpus

def d_split(start, end, string_cmd):
      return string_cmd.split(start)[1].split(end)[0].encode("ascii").strip()

def get_cpus():
      
      cpu_fields = {}
      cpus = []
      cpu_info = local["lscpu"]().encode("ascii")
      soc_count = int(d_split("Socket(s):", "\n", cpu_info))
      #cores_in_soc = int(d_split("Core(s) per socket:", "\n", cpu_info))
      cpu_fields["model"] = d_split("Model name:", "\n", cpu_info)
      cpu_fields["cores"] = int(d_split("CPU(s):", "\n", cpu_info))/soc_count
      cpu_fields["clock"] = d_split("CPU max MHz:", "\n", cpu_info)
      cpu_fields["architecture"] = d_split("Architecture:", "\n", cpu_info)
      cpu_fields["threads per core"] = d_split("Thread(s) per core:", "\n", cpu_info)
      for c in range(soc_count):
            cpu_fields["socket"] = c
            cpus.append(cpu_fields.copy())
            #cpu_node = Node("CPU", **cpu_fields)
      return cpus

def get_mem():
      mem_fields = {}
      mem_info = local["cat"]("/proc/meminfo")
      mem_info = d_split("MemTotal:", "\n", mem_info)
      mem_fields["total"] = mem_info
#      mem_node = Node("Memory", **mem_fields)
      return mem_fields

def get_disks():
      
      all_disks = sudo["/usr/local/sbin/megacli"]('-pdlist -a0').split("\n\n") 
      n=0
      disk_array = []
#      print all_disks[1]
      for x in all_disks:
            if "Port status: Active" in x and "Media Type: Hard Disk Device" in x:
                  try:#print x
                        disk_info = {}
                        disk_info["id"] = d_split("evice Id:", "\n", x)
                        disk_info["firmware"] = d_split("Firmware Level:", "\n", x)
                        disk_info["size"] = d_split("Raw Size:", "\n", x)
                        disk_info["serial"] = d_split("Inquiry Data:", "\n", x)
                        disk_array.append(disk_info)
                        n+=1
                        
                  except:
                        pass
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

nic_array = get_nics()
gpu_array = get_gpus()
cpu_array = get_cpus()
mem_array = get_mem()
sys_array = get_sys()

sys_array.update({"GPU(s)":gpu_array})
sys_array.update({"NICs":nic_array})
sys_array.update({"CPU":cpu_array})
sys_array.update({"Memory":mem_array})
if 'h' not in sys_array['hostname']:
      disk_array = get_disks()
      sys_array.update({"Disks": disk_array})
      
import yaml
import datetime

today = str(datetime.date.today())
name  = sys_array["hostname"] +'_'
network = sys_array["network"]
with open("reports/" + network +"/"+ name + today +'.yaml', 'w') as outfile:
      yaml.dump({"device":sys_array}, outfile, default_flow_style=False)

