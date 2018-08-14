# Glance

The Breakthrough Listen computer networks are so large and disparate that even knowing what hardware is plugged into the network is a nontrivial task. To address the issue of hardware monitoring and Inventory, I built Glance.
Glance is a program that examines our computer networks and retrieves relevant hardware information then presents the learned information in three ways:
* An online website with a graphical representation of the network. 
* Archived reports of the systems and hardware in the network.
* Spreadsheets containing more information including serial and model numbers for inventory.

### Prerequisites

Every system will need:
* plumbum (python package)
* nslookup (in dnsutils)

### Installing

Clone this repo onto the head node.
Create a subfolder in tree_data/ and reports/ with the name of the new network.



## Authors

* **Daniel Richards** - [github](https://github.com/dan-rds)

