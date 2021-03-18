import json
import platform
import plistlib
import subprocess
import time
import uuid


class MacOS:

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

        components = list()

        device_dict = self.device(components)
        self.memory(components)
        self.disk(components)
        self.graphics(components)
        self.network_interface(components)
        self.power_supply(components)

        self.snapshot['device'] = device_dict
        self.snapshot['components'] = components

        return self.snapshot

    # obtain System related information
    def device(self, components):
        device_info = dict()

        cmd = ["system_profiler -xml SPHardwareDataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            device_info['serialNumber'] = output_json[0]['_items'][0]['serial_number']
            device_info['manufacturer'] = 'Apple'
            device_info['model'] = output_json[0]['_items'][0]['machine_name']
            device_info['sku'] = output_json[0]['_items'][0]['machine_model']

            if device_info['model'].find("Book") != -1:
                device_info['type'] = 'Laptop'
                device_info['chassis'] = 'Netbook'
                self.desktop = False
            else:
                device_info['type'] = 'Desktop'
                device_info['chassis'] = 'Tower'
                self.desktop = True

            cpu = dict()

            cmd = ["sysctl -n hw.cpufrequency"]
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, errors = proc.communicate()
            proc.wait()

            cpu['type'] = 'Processor'

            if output_json[0]['_items'][0]['cpu_type'].find('Intel') != -1:
                cpu['manufacturer'] = 'Intel Corp.'
            elif output_json[0]['_items'][0]['cpu_type'].find('AMD') != -1:
                cpu['manufacturer'] = 'AMD'
            else:
                cpu['manufacturer'] = 'other'

            cpu['model'] = output_json[0]['_items'][0]['cpu_type']
            cpu['speed'] = int(output) / 1000000000
            cpu['address'] = 64
            cpu['cores'] = output_json[0]['_items'][0]['number_processors']
            cpu['threads'] = cpu['cores'] * 2

            components.append(cpu)
        else:
            device_info['serialNumber'] = -1

        return device_info

    # obtain RAM information
    def memory(self, components):
        cmd = ["system_profiler -xml SPMemoryDataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            for dimm in output_json[0]['_items'][0]['_items']:
                ram = dict()
                ram['type'] = 'RamModule'
                if self.desktop:
                    ram['format'] = 'DIMM'
                else:
                    ram['format'] = 'SODIMM'

                memory_split = dimm['dimm_size'].split(' ')
                ram['size'] = int(memory_split[0]) * 1024
                ram['model'] = None
                ram['serialNumber'] = dimm['dimm_serial_number']
                memory_split = dimm['dimm_speed'].split(' ')
                ram['speed'] = int(memory_split[0])
                ram['interface'] = None
                components.append(ram)
        else:
            ram = {'type': 'RamModule', 'serialNumber': -1}
            components.append(ram)

    # obtain Disks information
    @staticmethod
    def disk(components):
        cmd = ["system_profiler -xml SPSerialATADataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            for disk in output_json[0]['_items']:
                if disk['_items'][0].get('size') is not None:
                    cmd = ["smartctl --all -j " + disk['_items'][0]['bsd_name'] + ""]
                    start_time_smart = time.time()
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    output, errors = proc.communicate()
                    proc.wait()
                    if proc.returncode >= 0:
                        smart_json = json.loads(output)
                        elapsed_time_smart = time.time() - start_time_smart
                        disk_json = dict()
                        disk_json['type'] = 'DataStorage'
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
                                     'length': 'Short', 'status': "Can't evaluate SMART", 'elapsed': elapsed_time_smart}
                        try:
                            smart['lifetime'] = smart_json['ata_smart_self_test_log']['standard']['table'][0][
                                "lifetime_hours"]
                        except:
                            smart['lifetime'] = 0
                        actions.append(smart)

                        benchmark = {}
                        start_time_benchmark_hdd = time.time()
                        cmd = ["purge && dd if=/dev/zero bs=1024k of=tstfile count=256"]
                        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        output, errors = proc.communicate()
                        proc.wait()
                        if proc.returncode >= 0:
                            output = output.decode()
                            value = float(output.split()[-2].replace(',', '.').replace("(", ""))
                            benchmark['writeSpeed'] = value / 1000000.0
                        else:
                            benchmark['writeSpeed'] = None

                        cmd = ["dd if=tstfile bs=1024k of=/dev/null count=256 && rm tstfile && purge"]
                        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        output, errors = proc.communicate()
                        proc.wait()
                        if proc.returncode >= 0:
                            output = output.decode()
                            value = float(output.split()[-2].replace(',', '.').replace("(", ""))
                            benchmark['readSpeed'] = value / 10000000.0
                        else:
                            benchmark['readSpeed'] = None
                        benchmark['type'] = 'BenchmarkDataStorage'
                        elapsed_time_benchmark_hdd = time.time() - start_time_benchmark_hdd
                        benchmark['elapsed'] = elapsed_time_benchmark_hdd
                        actions.append(benchmark)
                        disk_json['actions'] = actions
                        components.append(disk_json)
                    else:
                        disk_json['type'] = 'DataStorage'
                        disk_json['serialNumber'] = -1
                        components.append(disk_json)
        else:
            disk_json = {'type': 'DataStorage', 'serialNumber': -1}
            components.append(disk_json)

        cmd = ["system_profiler -xml SPNVMeDataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            for disk in output_json[0]['_items']:
                if disk['_items'][0].get('size') is not None:
                    cmd = ["smartctl --all -j " + disk['_items'][0]['bsd_name'] + ""]
                    start_time_smart = time.time()
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    output, errors = proc.communicate()
                    proc.wait()
                    if proc.returncode >= 0:
                        smart_json = json.loads(output)
                        elapsed_time_smart = time.time() - start_time_smart
                        disk_json = dict()
                        disk_json['type'] = 'DataStorage'
                        if smart_json['device']['name'].find('Hard') != -1:
                            disk_json['type'] = 'HardDrive'
                        else:
                            disk_json['type'] = 'SolidStateDrive'

                        disk_json['model'] = smart_json['model_name']
                        disk_json['serialNumber'] = smart_json['serial_number']
                        disk_json['size'] = smart_json['user_capacity']['bytes'] / 1024 / 1024

                        actions = []

                        smart = {'type': 'TestDataStorage', 'powerCycleCount': smart_json['power_cycle_count'],
                                 'length': 'Short', 'status': 'Completed without error', 'elapsed': elapsed_time_smart}
                        actions.append(smart)

                        benchmark = {}
                        start_time_benchmark_hdd = time.time()
                        cmd = ["purge && dd if=/dev/zero bs=1024k of=tstfile count=256"]
                        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        output, errors = proc.communicate()
                        proc.wait()
                        if proc.returncode >= 0:
                            output = output.decode()
                            value = float(output.split()[-2].replace(',', '.').replace("(", ""))
                            benchmark['writeSpeed'] = value / 1000000.0
                        else:
                            benchmark['writeSpeed'] = None
                        cmd = ["dd if=tstfile bs=1024k of=/dev/null count=256 && rm tstfile && purge"]
                        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        output, errors = proc.communicate()
                        proc.wait()
                        if proc.returncode >= 0:
                            output = output.decode()
                            value = float(output.split()[-2].replace(',', '.').replace("(", ""))
                            benchmark['readSpeed'] = value / 10000000.0
                        else:
                            benchmark['readSpeed'] = None
                        benchmark['type'] = 'BenchmarkDataStorage'
                        elapsed_time_benchmark_hdd = time.time() - start_time_benchmark_hdd
                        benchmark['elapsed'] = elapsed_time_benchmark_hdd
                        actions.append(benchmark)
                        disk_json['actions'] = actions
                        components.append(disk_json)
                    else:
                        disk_json['type'] = 'DataStorage'
                        disk_json['serialNumber'] = -1
                        components.append(disk_json)
        else:
            disk_json['type'] = 'DataStorage'
            disk_json['serialNumber'] = -1
            components.append(disk_json)

    # obtain GPU information
    @staticmethod
    def graphics(components):
        cmd = ["system_profiler -xml SPDisplaysDataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            for gpu in output_json[0]['_items']:
                gpu_json = dict()
                gpu_json['type'] = 'GraphicCard'
                if gpu['_name'].find('NVidia') != -1:
                    gpu_json['manufacturer'] = 'NVIDIA Corporation'
                elif gpu['_name'].find('AMD') != -1:
                    gpu_json['manufacturer'] = 'AMD'
                else:
                    gpu_json['manufacturer'] = 'Intel Corp.'
                gpu_json['model'] = gpu['sppci_model']
                gpu_split = gpu['_spdisplays_vram'].split(' ')
                gpu_json['memory'] = gpu_split[0]

                components.append(gpu_json)
        else:
            gpu_json = {'type': 'GraphicCard', 'serialNumber': -1}
            components.append(gpu_json)

    # obtain Network Information
    @staticmethod
    def network_interface(components):
        cmd = ["system_profiler -xml SPNetworkDataType"]
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = plistlib.loads(output)

            for net in output_json[0]['_items']:
                if net.get('Ethernet') is not None:
                    interface_json = {'type': 'NetworkAdapter', 'serialNumber': net['Ethernet']['MAC Address'],
                                      'speed': None, 'model': None, 'manufacturer': None, 'wireless': False}
                    components.append(interface_json)
        else:
            interface_json = {'type': 'NetworkAdapter', 'serialNumber': -1}
            components.append(interface_json)

    # obtain Power supply information (only laptop)
    def power_supply(self, components):
        if not self.desktop:
            cmd = ["system_profiler -xml SPPowerDataType"]
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output, errors = proc.communicate()
            proc.wait()

            if proc.returncode >= 0:
                output_json = plistlib.loads(output)

                for battery in output_json[0]['_items']:
                    if battery.get('sppower_battery_charge_info') is not None:
                        battery_json = {'type': 'Battery', 'serialNumber': battery['sppower_battery_model_info'][
                            'sppower_battery_serial_number'], 'manufacturer': battery['sppower_battery_model_info'][
                            'sppower_battery_manufacturer'],
                                        'model': battery['sppower_battery_model_info']['sppower_battery_device_name'],
                                        'size': battery['sppower_battery_charge_info']['sppower_battery_max_capacity']}
                        components.append(battery_json)
            else:
                battery_json = {'type': 'Battery', 'serialNumber': -1}
                components.append(battery_json)
