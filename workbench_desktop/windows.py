import json
import os
import subprocess
import time
import uuid
import platform
import utils
os.environ["COMSPEC"] = 'powershell'


class Windows:

    def __init__(self):
        self.snapshot = dict()
        self.desktop = True

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

        cmd = ['Get-CimInstance -ClassName Win32_systemenclosure | select SerialNumber | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()
        if proc.returncode >= 0:
            output_json = json.loads(output)
            device_info['serialNumber'] = output_json['SerialNumber']
        else:
            device_info['serialNumber'] = -1

        cmd = [
            'Get-CimInstance -ClassName Win32_ComputerSystem | select Manufacturer, SystemFamily, SystemSKUNumber | '
            'ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)
            device_info['manufacturer'] = output_json['Manufacturer']
            device_info['sku'] = output_json['SystemSKUNumber']
            device_info['model'] = output_json['SystemFamily']
        else:
            device_info['serialNumber'] = -1

        cmd = ['Get-CimInstance -ClassName Win32_PortableBattery | select Availability | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            if len(output.decode('utf8')) == 0:
                self.desktop = True
                device_info['type'] = 'Desktop'
                device_info['chassis'] = 'Tower'
            else:
                self.desktop = False
                device_info['type'] = 'Laptop'
                device_info['chassis'] = 'Netbook'

        return device_info

    # obtain Motherboard related information
    @staticmethod
    def motherboard(components):
        motherboard = dict()

        cmd = [
            'Get-CimInstance -ClassName Win32_BaseBoard | select Manufacturer, Product, SerialNumber | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)

            motherboard['type'] = 'Motherboard'
            motherboard['manufacturer'] = output_json['Manufacturer']
            motherboard['model'] = output_json['Product']
            motherboard['serialNumber'] = output_json['SerialNumber']
        else:
            motherboard['type'] = 'Motherboard'
            motherboard['serialNumber'] = -1

        components.append(motherboard)

    # obtain CPU related information
    @staticmethod
    def processor(components):
        cpu = dict()

        cmd = [
            'Get-CimInstance -ClassName Win32_Processor | select Name, MaxClockSpeed, AddressWidth, NumberOfCores, '
            'NumberOfLogicalProcessors | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)

            cpu['type'] = 'Processor'

            if output_json['Name'].find('Intel') != -1:
                cpu['manufacturer'] = 'Intel Corp.'
            elif output_json['Name'].find('AMD') != -1:
                cpu['manufacturer'] = 'AMD'
            else:
                cpu['manufacturer'] = 'other'

            cpu['model'] = output_json['Name'].strip()
            cpu['speed'] = output_json['MaxClockSpeed'] / 1000
            cpu['address'] = output_json['AddressWidth']
            cpu['cores'] = output_json['NumberOfCores']
            cpu['threads'] = output_json['NumberOfLogicalProcessors']
            cpu['serialNumber'] = None
        else:
            cpu['type'] = 'Processor'
            cpu['serialNumber'] = -1

        components.append(cpu)

    # obtain RAM information
    def memory(self, components):
        cmd = [
            'Get-CimInstance -ClassName Win32_PhysicalMemory | select Manufacturer, Capacity, ConfiguredClockSpeed, '
            'PartNumber | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)
            if type(output_json) == list:
                for dimm in output_json:
                    ram_json = {'type': 'RamModule'}
                    if self.desktop:
                        ram_json['format'] = 'DIMM'
                    else:
                        ram_json['format'] = 'SODIMM'
                    ram_json['size'] = dimm['Capacity'] / 1024 / 1024
                    ram_json['manufacturer'] = dimm['Manufacturer']
                    ram_json['speed'] = dimm['ConfiguredClockSpeed']
                    ram_json['interface'] = None
                    ram_json['serialNumber'] = None
                    components.append(ram_json)
            else:
                ram_json = {'type': 'RamModule'}
                if self.desktop:
                    ram_json['format'] = 'DIMM'
                else:
                    ram_json['format'] = 'SODIMM'
                ram_json['size'] = output_json['Capacity'] / 1024 / 1024
                ram_json['manufacturer'] = output_json['Manufacturer']
                ram_json['speed'] = output_json['ConfiguredClockSpeed']
                ram_json['interface'] = None
                ram_json['serialNumber'] = None
                components.append(ram_json)
                
        else:
            ram_json = {'type': 'RamModule', 'serialNumber': -1}
            components.append(ram_json)

    # obtain Disks information
    @staticmethod
    def disk(components):
        cmd = ['smartctl -j --scan']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)
            count_disk = 0
            for disk in output_json['devices']:
                if disk['type'] == 'ata' and disk['name'].find('/dev/sd') != -1:
                    cmd = ['Get-Disk -Number ' + str(count_disk) + ' | select Model, Size, SerialNumber | ConvertTo-JSON']
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            stdin=subprocess.PIPE)
                    output, errors = proc.communicate()
                    proc.wait()
                    disk_info_json = json.loads(output)

                    disk_json = {'model': disk_info_json['Model'],
                                 'serialNumber': disk_info_json['SerialNumber'].strip(), 'interface': 'ATA'}
                    size_gb = int(disk_info_json['Size'])
                    size_gb = int(size_gb / 1000 / 1000)
                    if size_gb != 0:
                        disk_json['size'] = size_gb

                    cmd = ['smartctl -j --all ' + disk['name']]
                    start_time_smart = time.time()
                    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                            stdin=subprocess.PIPE)
                    output, errors = proc.communicate()
                    proc.wait()
                    smart_json = json.loads(output)
                    actions = []
                    if proc.returncode == 0:
                        elapsed_time_smart = time.time() - start_time_smart
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
                        results = utils.disk_test()
                        elapsed_time_benchmark_hdd = time.time() - start_time_benchmark_hdd
                        benchmark['type'] = 'BenchmarkDataStorage'
                        benchmark['writeSpeed'] = (1048576 / float(results['write'])) / 1000000
                        benchmark['readSpeed'] = (1048576 / float(results['read'])) / 10000000
                        benchmark['elapsed'] = elapsed_time_benchmark_hdd
                        actions.append(benchmark)
                        disk_json['actions'] = actions
                        components.append(disk_json)
                        count_disk = count_disk + 1
                        os.remove("testfile")
                    else:
                        smart = {'type': 'TestDataStorage',
                        'length': 'Short', 'status': 'Completed with error'}
                        actions.append(smart)
                        benchmark = {}
                        start_time_benchmark_hdd = time.time()
                        results = utils.disk_test()
                        elapsed_time_benchmark_hdd = time.time() - start_time_benchmark_hdd
                        benchmark['type'] = 'BenchmarkDataStorage'
                        benchmark['writeSpeed'] = (1048576 / float(results['write'])) / 1000000
                        benchmark['readSpeed'] = (1048576 / float(results['read'])) / 10000000
                        benchmark['elapsed'] = elapsed_time_benchmark_hdd
                        actions.append(benchmark)
                        disk_json['actions'] = actions
                        components.append(disk_json)
                        count_disk = count_disk + 1
                        os.remove("testfile")
        else:
            disk_json = {'type': 'DataStorage', 'serialNumber': -1}
            components.append(disk_json)

    # obtain GPU information
    @staticmethod
    def graphics(components):
        gpu = {}
        cmd = [
            'Get-CimInstance -ClassName Win32_VideoController | select Name, AdapterCompatibility, AdapterRAM | '
            'ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)

            gpu['type'] = 'GraphicCard'
            gpu['manufacturer'] = output_json['AdapterCompatibility']
            gpu['model'] = output_json['Name']
            gpu['memory'] = int(output_json['AdapterRAM'] / 1024 / 1024) * 2
            gpu['serialNumber'] = None
        else:
            gpu['type'] = 'GraphicCard'
            gpu['serialNumber'] = -1
        components.append(gpu)

    # obtain Network Information
    @staticmethod
    def network_interface(components):
        cmd = [
            'Get-CimInstance -ClassName Win32_NetworkAdapter | select Name, Speed, MACAddress, Caption, Manufacturer, '
            'ProductName | ConvertTo-JSON']
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE)
        output, errors = proc.communicate()
        proc.wait()

        if proc.returncode >= 0:
            output_json = json.loads(output)
            for NIC in output_json:
                if NIC['Speed'] is not None and NIC['Caption'].find('Bluetooth') == -1 and NIC['Name'].find(
                        'Virtual') == -1 and NIC['Name'].find('TAP') == -1 and NIC['ProductName'].find('Tunnel') == -1:
                    interface_json = {'type': 'NetworkAdapter', 'manufacturer': NIC['Manufacturer'],
                                      'model': NIC['ProductName'], 'serialNumber': NIC['MACAddress'], 'wireless': False}
                    if NIC['Speed'] / 1000000 > 10000:
                        interface_json['speed'] = int(NIC['Speed'] / 10000000000000000)
                    else:
                        interface_json['speed'] = int(NIC['Speed'] / 1000000)
                    components.append(interface_json)
        else:
            interface_json = {'type': 'NetworkAdapter', 'serialNumber': -1}
            components.append(interface_json)

    # obtain Power supply information (only laptop)
    def power_supply(self, components):
        if not self.desktop:
            cmd = [
                'Get-CimInstance -ClassName Win32_PortableBattery | select Manufacturer, Name, DesignCapacity '
                '| ConvertTo-JSON']
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    stdin=subprocess.PIPE)
            output, errors = proc.communicate()
            proc.wait()
            if proc.returncode >= 0:
                output_json = json.loads(output)
                if isinstance(output_json, dict):
                    battery_json = {'type': 'Battery', 'manufacturer': output_json['Manufacturer'],
                                    'model': output_json['Name'], 'technology': 'LiIon', 'wireless': False,
                                    'size': output_json['DesignCapacity']}
                    components.append(battery_json)
                else:
                    for battery in output_json:
                        battery_json = {'type': 'Battery', 'manufacturer': battery['Manufacturer'],
                                        'model': battery['Name'], 'size': battery['DesignCapacity'],
                                        'serialNumber': None}
                        components.append(battery_json)
            else:
                battery_json = {'type' : 'Battery', 'serialNumber': -1}
                components.append(battery_json)
