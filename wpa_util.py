import time
import subprocess
import configparser

class WifiUtil():
    ''' Wifi Manage Util Collection '''

    @classmethod
    def get_network(cls, network_id=None, ssid=None):
        ''' return wifi network list if no kwargs
            return dist network if network id or ssid filtered
        '''

        list_network = []
        ok, cmplt_proc = WpaHelper.command(WPA_CMD.LIST_NETWORK)
        if not ok:
            return []

        def load_listn(ln_str):
            ''' load network list string to list

            example string:
            network id / ssid / bssid / flags
            0       HUAWEI-B315-111E        any     [CURRENT]
            1               any     [DISABLED]
            2               any     [DISABLED]
            3               any     [DISABLED]
            4       XMSJ\" psk \"adfa       any     [DISABLED]

            return: list of diction, diction with key(network id, ssid, bssid, flags) and value
            '''

            res = []
            if not ln_str:
                return res

            fields = []
            ln_lines = ln_str.splitlines()
            for line in ln_lines:
                if line.startswith('network id'):
                    # header line
                    items = line.split('/')
                    fields = list(map(str.strip, items))
                else:
                    # body line
                    items = line.split('\t')
                    if not items:
                        continue
                    items_map = map(str.strip, items)
                    new_dict = {}
                    for idx, v in enumerate(items_map):
                        new_dict[fields[idx]] = v
                    res.append(new_dict)
            return res

        list_network = load_listn(cmplt_proc.stdout)
        if network_id:
            # get dest network by id
            return [n for n in list_network if n.get('network id')==network_id]
        elif ssid:
            return [n for n in list_network if n.get('ssid')==ssid]
        else:
            # get network list
            return list_network

    @classmethod
    def add_network(cls, ssid, password):
        network_id = None
        ok, cmplt_proc = WpaHelper.command(WPA_CMD.ADD_NETWORK)
        if ok:
            network_id = cmplt_proc.stdout.splitlines()[0]
            ok = cls.set_network(network_id, ssid, password)
            if not ok:
                cls.del_network(network_id)
                network_id = None

        return network_id

    @classmethod
    def del_network(cls, network_id):
        ok = WpaHelper.command(WPA_CMD.DEL_NETWORK, network_id)
        return ok

    @classmethod
    def set_network(cls, network_id, ssid=None, password=None):
        ok = False
        if ssid:
            ok = WpaHelper.command(WPA_CMD.SET_NETWORK, network_id, 'ssid', '"'+ssid+'"')
        if ok and password:
            ok = WpaHelper.command(WPA_CMD.SET_PASSWORD, network_id, '"'+password+'"')
        
        return ok

    @classmethod
    def enable_network(cls, network_id, enable=True):
        ok = WpaHelper.command(WPA_CMD.ENABLE_NETWORK, network_id, enable)
        return ok

    @classmethod
    def scan_network(cls, wait_time=1.5):
        scan_result = []
        def load_scanr(scanr_str):
            ''' load network scan result string to list

            example string:
            bssid / frequency / signal level / flags / ssid
            e4:a7:c5:8d:11:1e       2442    -35     [WPA2-PSK-CCMP][WPS][ESS]       HUAWEI-B315-111E
            78:11:dc:4c:3e:95       2457    -51     [WPA-PSK-CCMP+TKIP][WPA2-PSK-CCMP+TKIP][WPS][ESS]       HUAWEI
            78:11:dc:4c:3e:96       5745    -71     [WPA-PSK-CCMP+TKIP][WPA2-PSK-CCMP+TKIP][WPS][ESS]       HUAWEI_5G
            88:25:93:86:ec:6a       2432    -70     [WPA-PSK-CCMP][WPA2-PSK-CCMP][ESS]      sumrich-vv120

            return: list of diction, diction with key(bssid, frequency, signal level, flags, ssid) and values
            '''

            res = []
            if not scanr_str:
                return res

            fields = []
            scanr_lines = scanr_str.splitlines()
            for line in scanr_lines:
                if line.startswith('bssid'):
                    # header line
                    items = line.split('/')
                    fields = list(map(str.strip, items))
                else:
                    # body line
                    items = line.split('\t')
                    if not items:
                        continue
                    items_map = map(str.strip, items)
                    new_dict = {}
                    for idx, v in enumerate(items_map):
                        new_dict[fields[idx]] = v
                    res.append(new_dict)
            return res
            
        ok = WpaHelper.command(WPA_CMD.SCAN)
        if ok:
            time.sleep(wait_time)
            ok, cmplt_proc = WpaHelper.command(WPA_CMD.SCAN_RESULT)
            if ok:
                scan_result = load_scanr(cmplt_proc.stdout)
        return ok, scan_result

    @classmethod
    def top_priority(cls, network_id, priority):
        pass
    
    @classmethod
    def conn_status(cls, network_id=None):
        status = {}
        # command check and wpa_supplicant daemon check
        ok = WpaHelper.check_command() and WpaHelper.check_daemon()

        if not ok:
            return ok, status
        
        # wpa_cli status check
        ok, cmplt_proc = WpaHelper.command(WPA_CMD.STATUS)
        if not ok:
            return ok, status

        def parse_status(status_str):
            ''' return wifi status information

            example status_str:
            bssid=e4:a7:c5:8d:11:1e
            freq=2442
            ssid=HUAWEI-B315-111E
            id=0
            mode=station
            pairwise_cipher=CCMP
            group_cipher=CCMP
            key_mgmt=WPA2-PSK
            wpa_state=COMPLETED
            ip_address=192.168.8.100
            p2p_device_address=80:86:f2:15:09:e2
            address=80:86:f2:15:09:e1
            uuid=3b29f8d0-d58d-5e1c-83f5-681b9e44e42c

            return list of key value pairs
            '''

            # to use configparser, we add ['Default'] section to source string
            cparser = configparser.ConfigParser(delimiters='=', comment_prefixes=None)
            status_str = '[{}]\n{}'.format(configparser.DEFAULTSECT, status_str)
            try:
                cparser.read_string(status_str)
            except configparser.Error:
                return {}
            else:
                return dict(cparser.items(configparser.DEFAULTSECT))

        status = parse_status(cmplt_proc.stdout)
        if not status:
            ok = False
        else:
            if status.get('wpa_state') == 'COMPLETED':
                ok = True
            else:
                ok = False

        return ok, status

    @classmethod
    def network_repair(cls):
        ''' wifi network repair interface
        
        The application should call the function repeatly until no messges
        
        return res: repair result True or False
        return msg: reparing message list
        '''

        res, msg = False, []
        
        # 1. check wpa_supplicant middleware installation
        ok = WpaHelper.check_command()
        if not ok:
            msg.append('FOUND: wpa_supplicant middleware not correctly installed')
            try:
                cmplt_proc = subprocess.run('apt install wpa_supplicant -y')
            except BaseException as e:
                msg.append('ERROR: install wpa_supplicant failed!')
                # log the exception
            else:
                if cmplt_proc and cmplt_proc.returncode != 0:
                    msg.append('ERROR: install wpa_supplicant failed!')
                else:
                    msg.append('FIXED: wpa_supplicant installed!')
                    res = True
            return res, msg
        
        # 2. check wpa_supplicant service running status
        ok = WpaHelper.check_daemon()
        if not ok:
            msg.append('FOUND: wpa_supplicant service is not running correctly:{}')
            try:
                # restart wpa_supplicant service
                # TODO: config wpa_supplicant
                cmplt_proc = subprocess.run('systemctl restart wpa_supplicant')
            except BaseException as e:
                msg.append('ERROR: restart wpa_supplicant service failed!')
                # log the excepton
            else:
                if cmplt_proc and cmplt_proc.returncode !=0:
                    msg.append('ERROR: restart wpa_supplicant failed!')
                else:
                    msg.append('FIXED: wpa_supplicant restarted!')
                    res = True
            return res, msg

        # 3. check wpa status
        ok, status = cls.conn_status()
        if not ok:
            msg.append('FOUND: wireless interface status:{}'.format(status.get('wpa_stat')))
        try:
            # TODO: solve status: DISCONNECTED
            pass
        except:
            pass
            msg.append('ERROR: solve wireless connection failed!')
        else:
            res = True
            msg.append('FIXED: wireless connect status COMPLETED!')
        return res, msg
        
        # 4. TODO: check route status
        pass

        # 5. TODO: check ping 8.8.8.8
        pass
        # 6. TODO: check ping dns(www.baidu.com)
        pass

class WPA_CMD():
    LIST_NETWORK = 'list_n'
    ADD_NETWORK = 'add_n'
    DEL_NETWORK = 'remove_n'
    SET_NETWORK = 'set_n'
    SELECT_NETWORK = 'select_n'
    ENABLE_NETWORK = 'enable_n'
    DISABLE_NETWORK = 'disable_n'
    SET_PASSWORD = 'password'

    SCAN = 'scan'
    SCAN_RESULT = 'scan_r'
    PING = 'ping'
    STATUS = 'status'
    IFNAME = 'ifname'
    VERSION = '-v'


class WpaHelper():
    WPA_CLI = 'wpa_cli'
    WPA_SUPPLICANT = 'wpa_supplicant'
    WLP_IFNAME = 'wlp2s0'
    

    @classmethod
    def command(cls, cmd, *args, ifname=None):
        ''' Execute WPA_CLI command and return result '''

        ok = True
        cmplt_proc = None
        if not ifname:
            ifname = cls.WLP_IFNAME
        try:
            # TODO: python3.7 new  kwargs: encoding and capture_output
            cmplt_proc = subprocess.run([cls.WPA_CLI, '-i', ifname, cmd, *args], timeout=1, stdout=subprocess.PIPE)

            if not cmplt_proc or cmplt_proc.returncode != 0:
                ok = False
            if cmplt_proc.stdout:
                cmplt_proc.stdout = cmplt_proc.stdout.decode()
                if 'FAIL' in cmplt_proc.stdout:
                    ok = False
        except (FileNotFoundError, PermissionError, TypeError):
            ok = False
        return ok, cmplt_proc

    @classmethod
    def check_command(cls):
        ''' Check wpa_cli command existence and executive '''

        ok = cls.command(WPA_CMD.VERSION)
        return ok

    @classmethod
    def check_daemon(cls):
        ok, cmplt_proc = cls.command(WPA_CMD.PING)
        if ok and 'PONG' in cmplt_proc.stdout:
            return True
        else:
            return False
    