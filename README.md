# Envoy2Emoncms

install emoncms on a sever for example a raspberry pi

run the following commands on a raspberry py

# Prerequisites
```sh
# Install python
apt-get install python
apt-get -y install python-pip

# Update pip
pip install --upgrade pip
```

# Upgrading
In case of upgrading please backup your config file (better safe then sorry).

# Install on rasberian
```sh 
cd /var/tmp
git clone -b master https://github.com/EdwinBontenbal/Envoy2Emoncms.git

cd Envoy2Emoncms/
cp Envoy2Emoncms.py /usr/local/bin/Envoy2Emoncms.py
cp Envoy2EmoncmsWatchdog.sh /usr/local/bin/Envoy2EmoncmsWatchdog.sh

mkdir /etc/Envoy2Emoncms
cp Envoy2Emoncms_default.cfg /etc/Envoy2Emoncms/Envoy2Emoncms.cfg 
vi /etc/Envoy2Emoncms/Envoy2Emoncms_default.cfg
- change alle options marked <.....> 
- add translation list if you want to translate your serial numbers to human readable names 
  [translationlist]
  121611023770 = Arr1_L1
  121611017098 = Arr1_L2
  .... more here ...
  121611023036 = Arr1_L3
``` 

add to crontab
```sh 
crontab -e
```
add
```sh 
* * * * *       /usr/local/bin/Envoy2EmoncmsWatchdog.sh
```

set logrotate
``` sh
cd /etc/logrotate.d
vi Envoy2Emoncms
```
add
``` sh
/var/log/Envoy2Emoncms_Watchdog.log /var/log/Envoy2Emoncms.log {
        daily
        rotate 7
        compress
}
```

Now change the settings in the file DSMR2Emoncms.py
``` sh
vi /etc/DSMR2Emoncms/DSMR2Emoncms.cfg
privateKey = <YOUR APIKEY OF EMONCMS INSTANCE> 
emon_host  = <YOUR IP OF EMONCMS INSTANCE>
```
