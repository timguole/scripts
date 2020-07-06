'''A very very simple HPE iLO utility.

With class "iLO", you can connect to a server's iLO port and query basic
information about the server, like CPU count, memory capacity, DIMM count,
temperatures. There are some pre-defined resource names with which you can
call iLO.get_system(), iLO.get_chassis(), iLO.get_manager(). And there is
also the iLO.raw_get() which you can call with uri and keys directly (Refer
to the HPE iLO RESTful API doc for details about uri and property names).

The basic usage pattern is:
>>> from ilo import iLO
>>> i = iLO(https_ip, user, password)
>>> i.login()
>>> cpu_count = i.get_system(iLO.CPU_COUNT)
>>> nics = i.get_system(iLO.NICS)
>>> for nic in nics:
>>>     nic_id = i.get_id(nic)
>>>        nic_mac = i.get_system(iLO.NIC_MAC, extra = {'nic': nic_id})
>>>        print(nic_mac)
>>> print("CPU Count: {}".format(cpu_count))
>>> i.logout()
'''

import signal
import re
import redfish


class iLO:
    '''Get HP Server Info via iLO '''

    _prefix = '/rest/v1'

    # Resource names for systems
    SN = 'sn'
    SKU = 'sku'
    MODEL = 'model'
    NAME = 'name'
    SYSTEM_HEALTH = 'system_health'
    CPU_FAMILY = 'cpu_family'
    CPU_COUNT = 'cpu_count'
    CPU_HEALTH = 'cpu_health'
    MEM_HEALTH = 'mem_health'
    MEM_GB = 'mem_gb'
    DIMMS = 'dimms'
    DIMM_MB = 'dimm_mb'
    DIMM_RANK = 'dimm_rank'
    DIMM_HEALTH = 'dimm_health'
    DIMM_TYPE = 'dimm_type'
    STORAGE_HEALTH = 'storage_health'
    ARRAY_CONTROLLERS = 'array_controllers'
    ARRAY_CONTROLLER_HEALTH = 'array_controller_health'
    DISK_DRIVES = 'disk_drives'
    DISK_DRIVE_HEALTH = 'disk_drive_health'
    DISK_DRIVE_MB = 'disk_drive_mb'
    DISK_DRIVE_SN = 'disk_drive_sn'
    DISK_DRIVE_MODEL = 'disk_drive_model'
    DISK_DRIVE_MEDIA_TYPE = 'disk_drive_media'
    DISK_DRIVE_INTERFACE_TYPE = 'disk_drive_interface'
    LOGICAL_DRIVES = 'logical_drives'
    LOGICAL_DRIVE_HEALTH = 'logical_drive_health'
    NICS = 'nics'
    NIC_MAC = 'nic_mac'
    NIC_IPV4 = 'nic_ipv4'
    NIC_IPV6 = 'nic_ipv6'
    NIC_HEALTH = 'nic_health'
    NIC_NAME = 'nic_name'
    NIC_SN = 'nic_sn'
    NIC_PORT_HEALTH = 'nic_port_health'
    NIC_PORT_SPEED = 'nic_port_speed'
    NIC_PORT_FULLDUPLEX = 'nic_port_fullduplex'
    POWER_STATE = 'power_state'
    POWER_AUTO_ON = 'power_auto_on'

    # map resource name to uri and keys
    # <resource name>: (<uri>, [key1, key2, ...])
    _system_map = {
        SN: ('/Systems/{system}', ['SerialNumber']),
        SKU: ('/Systems/{system}', ['SKU']),
        MODEL: ('/Systems/{system}', ['Model']),
        NAME: ('/Systems/{system}', ['Name']),
        SYSTEM_HEALTH: ('/Systems/{system}', ['Status', 'Health']),
        CPU_FAMILY: ('/Systems/{system}', ['Processors', 'ProcessorFamily']),
        CPU_COUNT: ('/Systems/{system}', ['Processors', 'Count']),
        CPU_HEALTH: ('/Systems/{system}', ['Processors', 'Status', 'HealthRollUp']),
        MEM_HEALTH: ('/Systems/{system}', ['Memory', 'Status', 'HealthRollUp']),
        MEM_GB: ('/Systems/{system}', ['Memory', 'TotalSystemMemoryGB']),
        DIMMS: ('/Systems/{system}/Memory', ['links', 'Member', 'href']),
        DIMM_MB: ('/Systems/{system}/Memory/{dimm}', ['SizeMB']),
        DIMM_RANK: ('/Systems/{system}/Memory/{dimm}', ['Rank']),
        DIMM_HEALTH: ('/Systems/{system}/Memory/{dimm}', ['DIMMStatus']),
        DIMM_TYPE: ('/Systems/{system}/Memory/{dimm}', ['DIMMType']),
        STORAGE_HEALTH: ('/Systems/{system}/SmartStorage', ['Status', 'Health']),
        ARRAY_CONTROLLERS: ('/Systems/{system}/SmartStorage/ArrayControllers', ['links', 'Member', 'href']),
        ARRAY_CONTROLLER_HEALTH: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}', ['Status', 'Health']),
        DISK_DRIVES: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives', ['links', 'Member', 'href']),
        DISK_DRIVE_HEALTH: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['Status', 'Health']),
        DISK_DRIVE_MB: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['CapacityMiB']),
        DISK_DRIVE_SN: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['SerialNumber']),
        DISK_DRIVE_MODEL: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['Model']),
        DISK_DRIVE_MEDIA_TYPE: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['MediaType']),
        DISK_DRIVE_INTERFACE_TYPE: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/DiskDrives/{diskdrive}', ['InterfaceType']),
        LOGICAL_DRIVES: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/LogicalDrives', ['links', 'Member', 'href']),
        LOGICAL_DRIVE_HEALTH: ('/Systems/{system}/SmartStorage/ArrayControllers/{controller}/LogicalDrives/{logicaldrive}', ['Status', 'Health']),
        NICS: ('/Systems/{system}/NetworkAdapters', ['links', 'Member', 'href']),
        NIC_MAC: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'MacAddress']),
        NIC_IPV4: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'IPv4Addresses', 'Address']),
        NIC_IPV6: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'IPv6Addresses', 'Address']),
        NIC_HEALTH: ('/Systems/{system}/NetworkAdapters/{nic}', ['Status', 'Health']),
        NIC_NAME: ('/Systems/{system}/NetworkAdapters/{nic}', ['Name']),
        NIC_SN: ('/Systems/{system}/NetworkAdapters/{nic}', ['SerialNumber']),
        NIC_PORT_HEALTH: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'Status', 'Health']),
        NIC_PORT_SPEED: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'SpeedMbps']),
        NIC_PORT_FULLDUPLEX: ('/Systems/{system}/NetworkAdapters/{nic}', ['PhysicalPorts', 'FullDuplex']),
        POWER_STATE: ('/Systems/{system}', ['PowerState']),
        POWER_AUTO_ON: ('/Systems/{system}', ['Oem', 'Hp', 'PowerAutoOn']),
    }

    # Resource names for chassis
    C_FAN_NAME = 'fan_name'
    C_FAN_N1 = 'fan_n1'
    C_FAN_UNIT = 'fan_unit'
    C_FAN_HEALTH = 'fan_health'
    C_FAN_HEALTHROLLUP = 'fan_healthrollup'
    C_FAN_STATE = 'fan_state'
    C_THERMAL_STATE = 'thermal_state'
    C_THERMAL_HEALTH = 'thermal_health'
    C_THERMAL_HEALTHROLLUP = 'thermal_healthrollup'
    C_TEMP_STATE = 'temp_state'
    C_TEMP_HEALTH = 'temp_health'
    C_TEMP_HEALTHROLLUP = 'temp_healthrollup'
    C_TEMP_CELSIUS = 'temp_celsius'
    C_POWER_SUPPLY_STATE = 'power_supply_state'
    C_POWER_SUPPLY_HEALTH = 'power_supply_health'
    C_POWER_SUPPLY_HEALTHROLLUP = 'power_supply_healthrollup'
    C_POWER_REDUNDANCY_STATE = 'power_redundancy_state'
    C_POWER_REDUNDANCY_HEALTH = 'power_redundancy_health'
    C_POWER_REDUNDANCY_HEALTHROLLUP = 'power_redundancy_healthrollup'

    _chassis_map = {
        C_FAN_NAME: ('/Chassis/{chassis}/Thermal', ['Fans', 'FanName']),
        C_FAN_N1: ('/Chassis/{chassis}/Thermal', ['Fans', 'CurrentReading']),
        C_FAN_UNIT: ('/Chassis/{chassis}/Thermal', ['Fans', 'Units']),
        C_FAN_HEALTH: ('/Chassis/{chassis}/Thermal', ['Fans', 'Status', 'Health']),
        C_FAN_HEALTHROLLUP: ('/Chassis/{chassis}/Thermal', ['Fans', 'Status', 'HealthRollUp']),
        C_FAN_STATE: ('/Chassis/{chassis}/Thermal', ['Fans', 'Status', 'State']),
        C_THERMAL_STATE: ('/Chassis/{chassis}/Thermal', ['Status', 'State']),
        C_THERMAL_HEALTH: ('/Chassis/{chassis}/Thermal', ['Status', 'Health']),
        C_THERMAL_HEALTHROLLUP: ('/Chassis/{chassis}/Thermal', ['Status', 'HealthRollUp']),
        C_TEMP_STATE: ('/Chassis/{chassis}/Thermal', ['Temperatures', 'Status', 'State']),
        C_TEMP_HEALTH: ('/Chassis/{chassis}/Thermal', ['Temperatures', 'Status', 'Health']),
        C_TEMP_HEALTHROLLUP: ('/Chassis/{chassis}/Thermal', ['Temperatures', 'Status', 'HealthRollUp']),
        C_TEMP_CELSIUS: ('/Chassis/{chassis}/Thermal', ['Temperatures', 'ReadingCelsius']),
        C_POWER_SUPPLY_STATE: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Status', 'State']),
        C_POWER_SUPPLY_HEALTH: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Status', 'Health']),
        C_POWER_SUPPLY_HEALTHROLLUP: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Status', 'HealthRollUp']),
        C_POWER_REDUNDANCY_STATE: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Redundancy', 'Status', 'State']),
        C_POWER_REDUNDANCY_HEALTH: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Redundancy', 'Status', 'Health']),
        C_POWER_REDUNDANCY_HEALTHROLLUP: ('/Chassis/{chassis}/Power', ['PowerSupplies', 'Redundancy', 'Status', 'HealthRollUp']),
    }

    # iLO info
    M_NICS = 'm_nics'
    M_NIC_MAC = 'm_nic_mac'

    _manager_map = {
        M_NICS: ('/Managers/{manager}/EthernetInterfaces', ['links', 'Member', 'href']),
        M_NIC_MAC: ('/Managers/{manager}/EthernetInterfaces/{nic}', ['MacAddress']),
    }


    def __init__(self, ilo_host, ilo_user, ilo_password):
        '''Create an iLO object.
        
        Args:
        ilo_host: "https://<iLO_IP>"
        ilo_user: iLO user name
        ilo_password: iLO login password
        '''
        self.cache = {} # cache for uri and response
        self.timeout = 10
        self.rest_obj = None
        self.ilo_host = ilo_host
        self.ilo_user = ilo_user
        self.ilo_password = ilo_password

    def _get_uri(self, path, use_cache = True):
        if (path not in self.cache.keys()) or (not use_cache):
            obj = self.rest_obj.get(path, None).obj
            self.cache[path] = obj
        return self.cache[path]

    def _get_resource_by_keys(self, obj, keys):
        def _find(o, k, v):
            if isinstance(o, list):
                for i in o:
                    _find(i, k, v)
            elif isinstance(o, dict):
                if len(k) == 1:
                    v.append(o[k[0]])
                else:
                    _find(o[k[0]], k[1:], v)

        try:
            values = []
            _find(obj, keys, values)
            return values
        except KeyError:
            return None

    def _get(self, what, uri, keys, extra , use_cache):
        if extra is None:
            extra = {what: '1'}
        elif what not in extra.keys():
            extra[what] = '1'
        uri = iLO._prefix + uri
        uri = uri.format(**extra)
        if '{' in uri:
            raise ValueError('extra args needed')
        r = self._get_uri(uri, use_cache)
        return self._get_resource_by_keys(r, keys)


    def login(self):
        '''Login to iLO.
        
        Call this method right after iLO() and before any iLO.get_xxx().
        '''
        self.rest_obj = redfish.rest_client( \
            base_url = self.ilo_host, \
            username = self.ilo_user, \
            password = self.ilo_password, \
            default_prefix = '/rest/v1')
        self.rest_obj.login(auth = 'session')

    def logout(self):
        '''Logout from iLO.

        Call this method to finish this session
        '''
        if self.rest_obj is not None:
            self.rest_obj.logout()

    def get_system(self, resource, extra = None, use_cache = True):
        '''Get system resources, e.g., CPU status, memory status etc.
        
        Args:
        resource: iLO-defined resource name, e.g., iLO.CPU_COUNT
        extra: extra resource IDs. Some resources need it.
        use_cache: Whether to use response cache. Resources like
            SerialNumber will not change frequently, it is faster to
            get SerialNumber from cache. Resources like fan RPM,
            temperatures change very frequently, data about these
            types of resources in cache is almost invalid.
            Default to True.

        Reource names prefixed by C_ can only be used with get_chassis(),
        M_ by get_manager().

        Return value is a list, even there is just one value. For resource
        collection like NICS, Disk Drives, the return value is a list of
        uri with which you can get the resource id by calling get_id().
        Resource id is useful when you need the "extra".
        '''

        try:
            uri, keys = iLO._system_map[resource]
        except KeyError:
            raise ValueError('Unknown resource name')
        return self._get('system', uri, keys, extra, use_cache)

    def get_chassis(self, resource, extra = None, use_cache = True):
        '''Get chassis resource. See get_system().'''

        try:
            uri, keys = iLO._chassis_map[resource]
        except KeyError:
            raise ValueError('Unknown resource name')
        return self._get('chassis', uri, keys, extra, use_cache)

    def get_manager(self, resource, extra = None, use_cache = True):
        '''Get resource about Manager(iLO). See get_system().'''

        try:
            uri, keys = iLO._manager_map[resource]
        except KeyError:
            raise ValueError('Unknown resource name')
        return self._get('manager', uri, keys, extra, use_cache)

    def raw_get(self, uri, keys, use_cache = True):
        '''Get resource with URI and property names.
        
        Args:
        uri: resource uri
        keys: a list of property names to find the value
        use_cache: same as of get_system()

        e.g.:
        >>> cpu_count = i.raw_get("/rest/v1/Systems/1", ["Processors", "Count"])
        See HPE iLO RESTful doc for valid URI and property names.
        '''

        r = self._get_uri(uri, use_cache)
        return self._get_resource_by_keys(r, keys)

    def get_id(self, uri):
        '''Get resource id.
        
        Args:
        uri: the uri returned by get_system(), get_chassis(), get_manager()

        '''

        r = self._get_uri(uri)
        return self._get_resource_by_keys(r, ['Id'])[0]


if __name__ == '__main__':
    import argparse
    import sys
    import getpass

    ilo = iLO('https://ip', 'user', 'pass')
    ilo.login()

    sn = ilo.get_system(iLO.SN)
    model = ilo.get_system(iLO.MODEL)
    status = ilo.get_system(iLO.SYSTEM_HEALTH)
    cpu_family = ilo.get_system(iLO.CPU_FAMILY)
    cpu_count = ilo.get_system(iLO.CPU_COUNT)
    cpu_health = ilo.get_system(iLO.CPU_HEALTH)
    mem_gb = ilo.get_system(iLO.MEM_GB)
    dimms = ilo.get_system(iLO.DIMMS)
    mb = []
    for dimm in dimms:
        dimm_id = ilo.get_id(dimm)
        e = {'dimm': dimm_id}
        mb.append(ilo.get_system(iLO.DIMM_MB, extra = e)[0])

    acs = ilo.get_system(iLO.ARRAY_CONTROLLERS)
    ac_health = []
    dd_cap = []
    dd_health = []
    for ac in acs:
        ac_id = ilo.get_id(ac)
        ac_health.append(ilo.get_system(iLO.ARRAY_CONTROLLER_HEALTH, extra = {'controller': ac_id})[0])
        hds = ilo.get_system(iLO.DISK_DRIVES, extra = {'controller': ac_id})
        for hd in hds:
            hd_id = ilo.get_id(hd)
            e = {'controller': ac_id, 'diskdrive': hd_id}
            dd_cap.append(ilo.get_system(iLO.DISK_DRIVE_MB,extra = e)[0])
            dd_health.append(ilo.get_system(iLO.DISK_DRIVE_HEALTH,extra = e)[0])
    nics = ilo.get_system(iLO.NICS)
    macs = []
    nic_health = []
    port_health = []
    for nic in nics:
        nic_id = ilo.get_id(nic)
        e = {'nic': nic_id}
        nh = ilo.get_system(iLO.NIC_HEALTH, extra = e)
        nic_health += nh
        ms = ilo.get_system(iLO.NIC_MAC, extra = e)
        macs += ms
        ph = ilo.get_system(iLO.NIC_PORT_HEALTH, extra = e)
        port_health += ph

    fan_name = ilo.get_chassis(iLO.C_FAN_NAME)
    fan_n1 = ilo.get_chassis(iLO.C_FAN_N1)
    fan_unit = ilo.get_chassis(iLO.C_FAN_UNIT)
    fan_health = ilo.get_chassis(iLO.C_FAN_HEALTH)
    temp_celsius = ilo.get_chassis(iLO.C_TEMP_CELSIUS)

    power_health = ilo.get_chassis(iLO.C_POWER_SUPPLY_HEALTH)
    power_rh = ilo.get_chassis(iLO.C_POWER_REDUNDANCY_HEALTH)

    mnmacs = []
    m_nics = ilo.get_manager(iLO.M_NICS)
    for n in m_nics:
        n_id = ilo.get_id(n)
        mnmac = ilo.get_manager(iLO.M_NIC_MAC, extra = {'nic': n_id})
        mnmacs += mnmac

    ilo.logout()

    print('Model: ' + model[0])
    print('SN: ' + sn[0])
    print('Status: ' + status[0])
    print('CPU Family: ' + cpu_family[0])
    print('CPU Count: {}'.format(cpu_count[0]))
    print('CPU Status: ' + cpu_health[0])
    print('Total Mem: {}GB'.format(mem_gb[0]))
    print('DIMMS:')
    print(mb)
    print('Array Controller Status:')
    print(ac_health)
    print('Disk Drives:')
    print(dd_cap)
    print(dd_health)
    print('Network Adapters:')
    print(nic_health)
    print(macs)
    print('Ports:')
    print(port_health)
    print('Fans:')
    print(fan_name)
    print(fan_n1)
    print(fan_unit)
    print(fan_health)
    print('Temperatures:')
    print(temp_celsius)
    print('Power:')
    print(power_health)
    print(power_rh)
    print('iLO:')
    print(mnmacs)

    exit(0)

