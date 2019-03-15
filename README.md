# freebox
Freebox python library plus some utilities for Freebox management

Having recently received a Freebox delta, I just discover that if you do the management of the box from Freebox OS,
there is a risk (that already occured for me) that when rebooting, the Free servers attempts to reconfigure the box from
the free centralized management data.

If, like me, you dont use free website to define port redirections, dhcp static leases and so on, chances are that all these
datas will be erased by this unpredictable process.

The two critical configuration elements already identified are :
 - Port forwarding to allow me to remote SSH or VPN in my lan in case of such problem
 - Static dhcp lease because I use camera that are managed through static lease and if the static lease disappear, they may
 be allocated unpredictable IPs
 
I created the lfreebox.py library and two utilities :
 - save_freebox.py that may be run by hand to create two yaml files with these two information sets,
 - check_and_restore_freebox.py that is run with a cron job every hour to check if there is a need of restoring
   ports forward or static dhcp
   
I also added to the library the possibility to query known nodes on the network and learn some information about reachability
This allows me to know if I'm home

```python
hosts = freebox.get_network_nodes()
if "myPhone" in hosts and hosts["myPhone"]["reachable"]:
  print("I see you !")
