import uuid
import time
import subprocess
import json
import platform
from dmiparser import DmiParser


class Linux:

    def __init__(self):
        self.snapshot = dict()
        self.desktop = None

    def do_snapshot(self, version):
        self.snapshot['uuid'] = str(uuid.uuid4())
        self.snapshot['type'] = 'Live'
        self.snapshot['software'] = 'WorkbenchDesktop'
        self.snapshot['version'] = version
        self.snapshot['os'] = platform.platform(terse=True).split('-')[0] + " " + \
                              platform.platform(terse=True).split('-')[1]

        device_dict = self.device()

        components = list()
        self.motherboard(components)
        self.processor(components)
        self.memory(components)
        self.disk(components)
        self.graphics(components)
        self.network_interface(components)
        self.power_supply(components)

        self.snapshot['device'] = device_dict
        self.snapshot['components'] = components

        return self.snapshot

    # obtain System related information
    def device(self):
        device_info = dict()

        cmd = ["dmidecode -t 1"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(str(DmiParser(output.decode('utf8'))))

            device_info['serialNumber'] = output_json[0]['props']['Serial Number']['values'][0]
            device_info['sku'] = output_json[0]['props']['SKU Number']['values'][0]
            device_info['manufacturer'] = output_json[0]['props']['Manufacturer']['values'][0]
            try:
                device_info['model'] = output_json[0]['props']['Version']['values'][0]
            except:
                device_info['model'] = output_json[0]['props']['Product Name']['values'][0]

        else:
            device_info['serialNumber'] = -1

        cmd = ["dmidecode -t 3"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(str(DmiParser(output.decode('utf8'))))

            device_info['chassis'] = output_json[0]['props']['Type']['values'][0]

            if device_info['chassis'].find('book') != -1:
                self.desktop = False
                device_info['type'] = 'Laptop'
                device_info['chassis'] = 'Netbook'
            else:
                self.desktop = True
                device_info['type'] = 'Desktop'
                device_info['chassis'] = 'Tower'

        return device_info

    # obtain Motherboard related information
    @staticmethod
    def motherboard(components):
        motherboard = dict()

        cmd = ["dmidecode -t 2"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(str(DmiParser(output.decode('utf8'))))

            motherboard['type'] = 'Motherboard'
            motherboard['manufacturer'] = output_json[0]['props']['Manufacturer']['values'][0]
            motherboard['model'] = output_json[0]['props']['Product Name']['values'][0]
            motherboard['serialNumber'] = output_json[0]['props']['Serial Number']['values'][0]
        else:
            motherboard['type'] = 'Motherboard'
            motherboard["serialNumber"] = -1

        components.append(motherboard)

    # obtain CPU related information
    @staticmethod
    def processor(components):
        cpu = dict()

        cmd = ["dmidecode -t 4"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(str(DmiParser(output.decode('utf8'))))

            cpu['type'] = 'Processor'
            cpu['manufacturer'] = output_json[0]['props']['Manufacturer']['values'][0]
            cpu['model'] = output_json[0]['props']['Version']['values'][0]
            cpu['address'] = 64
            cpu['speed'] = float(output_json[0]['props']['Current Speed']['values'][0].split(' ')[0]) / 1000
            cpu['cores'] = int(output_json[0]['props']['Core Count']['values'][0])
            cpu['threads'] = int(output_json[0]['props']['Thread Count']['values'][0])
            cpu['serialNumber'] = None
        else:
            cpu['type'] = 'Processor'
            cpu['serialNumber'] = -1

        components.append(cpu)

    # obtain RAM information
    @staticmethod
    def memory(components):
        cmd = ["dmidecode -t 17"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()
        output_json = json.loads(str(DmiParser(output.decode('utf8'))))

        if proc.returncode >= 0:
            for dimm in output_json:
                if dimm['props']['Size']['values'][0] != 'No Module Installed':
                    ram = {'type': 'RamModule',
                           'speed': int(dimm['props']['Speed']['values'][0].split(' ')[0]),
                           'interface': dimm['props']['Type']['values'][0],
                           'format': dimm['props']['Form Factor']['values'][0],
                           'serialNumber': dimm['props']['Serial Number']['values'][0],
                           'manufacturer': dimm['props']['Manufacturer']['values'][0]}

                    if int(dimm['props']['Size']['values'][0].split(' ')[0]) > 128:
                        ram['size'] = int(dimm['props']['Size']['values'][0].split(' ')[0])
                    else:
                        ram['size'] = int(dimm['props']['Size']['values'][0].split(' ')[0]) * 1024
                    components.append(ram)
        else:
            ram = {'type': 'RamModule', 'serialNumber': -1}
            components.append(ram)

    # obtain Disks information
    @staticmethod
    def disk(components):
        cmd = ["lsblk -J"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()
        output_json = json.loads(str(output.decode('utf8')))

        if proc.returncode >= 0:
            for disk in output_json['blockdevices']:
                if disk['name'].find('loop') == -1:
                    cmd = ["smartctl --all -j /dev/" + disk['name']]
                    start_time_smart = time.time()
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    output, errors = proc.communicate()
                    proc.wait()

                    if proc.returncode >= 0:
                        smart_json = json.loads(str(output.decode('utf8')))
                        elapsed_time_smart = time.time() - start_time_smart

                        disk_json = {}

                        if smart_json.get("smart_family"):
                            if smart_json["model_family"].find("SSD") == -1:
                                disk_json["type"] = "HardDrive"
                            else:
                                disk_json["type"] = "SolidStateDrive"
                        else:
                            if smart_json["model_name"].find("SSD") == -1:
                                disk_json["type"] = "HardDrive"
                            else:
                                disk_json["type"] = "SolidStateDrive"

                            disk_json['model'] = smart_json['model_name']
                            disk_json['serialNumber'] = smart_json['serial_number']
                            disk_json['size'] = smart_json['user_capacity']['bytes'] / 1024 / 1024

                            actions = []
                            try:
                                smart = {'type': 'TestDataStorage', 'powerCycleCount': smart_json['power_cycle_count'],
                                         'length': 'Short',
                                         'status': 'Completed without error', 'elapsed': elapsed_time_smart}
                            except:
                                smart = {'type': 'TestDataStorage', 'powerCycleCount': 0,
                                         'length': 'Short', 'status': "Can't evaluate SMART",
                                         'elapsed': elapsed_time_smart}
                            try:
                                smart['lifetime'] = smart_json['ata_smart_self_test_log']['standard']['table'][0][
                                    "lifetime_hours"]
                            except:
                                smart['lifetime'] = 0
                            actions.append(smart)

                            benchmark = {}
                            start_time_benchmark_hdd = time.time()
                            cmd = ["dd if=/dev/" + disk['name'] + " of=/dev/null bs=1M count=256 oflag=dsync"]
                            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            output, errors = proc.communicate()
                            proc.wait()
                            output = output.decode('utf8')
                            if proc.returncode >= 0:
                                value = float(output.split()[-2].replace(',', '.'))
                                if value < 20.0:
                                    value = value * 1000.0
                                benchmark['readSpeed'] = value
                            else:
                                benchmark['readSpeed'] = None

                            cmd = ["dd if=/dev/" + disk['name'] + " of=/dev/" + disk[
                                'name'] + "bs=1M count=256 oflag=dsync"]
                            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                            output, errors = proc.communicate()
                            proc.wait()
                            output = output.decode('utf8')
                            if proc.returncode >= 0:
                                value = float(output.split()[-2].replace(',', '.'))
                                if value < 20.0:
                                    value = value * 1000.0
                                benchmark['writeSpeed'] = value
                            else:
                                benchmark['writeSpeed'] = None

                            elapsed_time_benchmark_hdd = time.time() - start_time_benchmark_hdd
                            benchmark['elapsed'] = elapsed_time_benchmark_hdd
                            benchmark['type'] = 'BenchmarkDataStorage'
                            actions.append(benchmark)
                            disk_json['actions'] = actions

                            components.append(disk_json)
                    else:
                        disk_json = {'type': 'DataStorage', 'serialNumber': -1}
                        components.append(disk_json)

        else:
            disk_json = {'type': 'DataStorage', 'serialNumber': -1}
            components.append(disk_json)

    # obtain GPU information
    @staticmethod
    def graphics(components):
        gpu = {}

        cmd = ["lspci | grep VGA | cut -d "":"" -f3"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            gpu['type'] = 'GraphicCard'
            if output.decode('utf8').strip().find('NVIDIA') != -1:
                gpu['manufacturer'] = 'NVIDIA Corporation'
            elif output.decode('utf8').strip().find('AMD') != -1:
                gpu['manufacturer'] = 'AMD'
            else:
                gpu['manufacturer'] = 'Intel Corp.'
            gpu['model'] = output.decode('utf8').strip()
            gpu['memory'] = None
            gpu['serialNumber'] = None
        else:
            gpu['type'] = 'GraphicCard'
            gpu['serialNumber'] = -1

        components.append(gpu)

    # obtain Network Information
    @staticmethod
    def network_interface(components):
        cmd = ["ip -j a"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(str(output.decode('utf8')))
            for nic in output_json:
                if nic['ifname'].find('vir') == -1 and nic['ifname'].find('docker') == -1 and nic['ifname'].find(
                        'lo') == -1:
                    interface = {'type': 'NetworkAdapter', 'serialNumber': nic['address'], 'speed': nic['txqlen'],
                                 'model': None, 'manufacturer': None, 'wireless': False}

                    components.append(interface)
        else:
            interface = {'type': 'NetworkAdapter', 'serialNumber': -1}
            components.append(interface)

    # obtain Power supply information (only laptop)
    def power_supply(self, components):
        if not self.desktop:
            cmd = ["dmidecode -t 22"]
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, errors = proc.communicate()
            proc.wait()

            if proc.returncode >= 0:
                output_json = json.loads(str(DmiParser(output.decode('utf8'))))
                for battery in output_json:
                    battery_json = {'type': 'Battery', 'manufacturer': battery['props']['Manufacturer']['values'][0],
                                    'size': int(battery['props']['Design Capacity']['values'][0].split(' ')[0]),
                                    'model': None, 'serialNumber': None}
                    components.append(battery_json)
            else:
                battery_json = {'type': 'Battery', 'serialNumber': -1}
                components.append(battery_json)