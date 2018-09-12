# wpa_util
python toolkit for wpa_supplicant suits 

## Based on wpa_cli
wpa_util provides high level wifi managment python interface based on wpa_cli, componet of famous linux wireless tool wpa_supplicant.
In order to use this you need ensure wpa_supplicant has been installed correctly on you platform.

# Who need it
wpa_util solves wireless network management problem on the non-standards linux distribution or mature mobile os such as android/ios.

# Quick Start
* To scan wireless networks
```python
import wpa_util
scan_r = wpa_util.WifiUtil.scan_network()
```
* To add a new wifi connection
```python
wpa_util.WifiUtil.add_network(ssid, password)
```

The ptyhon version is required 3.5+

# Contribution
Issues or PR are welcomed to be submitted, I will reply as soon as I can.
