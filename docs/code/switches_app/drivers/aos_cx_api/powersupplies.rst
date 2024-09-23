.. image:: ../../../../_static/openl2m_logo.png

==================================
AOS-CX API PowerSupply and Chassis
==================================

The Device.get_subsystems() call is used to get various information about chassis, power supplies and more.
This is returned in *device.subsystems*, a dictionary of objects where the key (name) is the subsystem
type followed by a comma and an ID.

An example of chassis information looks like this:

.. code-block:: python

    subsystems = {
        'chassis,1': {
            'fans': {},
            'interfaces': {},
            'power_supplies': {
                '1/1': {'characteristics': {'instantaneous_power': 132, 'maximum_power': 680}, 'identity': {'airflow': 'F2B', 'description': 'Aruba X372 54VDC 680W PS', 'hardware_rev': '10', 'input_voltage_high': 240, 'input_voltage_low': 100, 'model_number': '0957-2475', 'product_name': 'JL086A', 'serial_number': 'TH33GZ9DBB', 'voltage_type': 'AC'}, 'name': '1/1', 'redundant_psu': [], 'statistics': {'failures': 0, 'warnings': 0}, 'status': 'ok'},
                '1/2': {'characteristics': {'instantaneous_power': 0, 'maximum_power': 0}, 'identity': {'description': 'N/A', 'hardware_rev': 'N/A', 'model_number': 'N/A', 'product_name': 'N/A', 'serial_number': 'N/A'}, 'name': '1/2', 'redundant_psu': [], 'statistics': {'failures': 0, 'warnings': 0}, 'status': 'fault_absent'}},
            'product_info': {
                'base_mac_address': 'ec:67:94:68:42:40',
                'device_version': '4',
                'instance': '1',
                'number_of_macs': '64',
                'part_number': 'JL660A',
                'product_description': '6300M 24-port HPE Smart Rate 1/2.5/5GbE Class 6 PoE and 4-port SFP56 Switch',
                'product_name': '6300M 24SR5 CL6 PoE 4SFP56 Swch',
                'serial_number': 'SG37LMR0LZ',
                'vendor': 'Aruba'
            },
            'resource_utilization': {}
        },

        'chassis,10': {
            'fans': {},
            'interfaces': {},
            'power_supplies': {},
            'product_info': {
                'base_mac_address': '00:00:00:00:00:00',
                'instance': '10',
                'number_of_macs': '0',
                'part_number': '',
                'product_description': '',
                'product_name': '',
                'serial_number': '',
                'vendor': ''
            },
            'resource_utilization': {}
        },

        'chassis,2': {
            etc...


Power Supply info is stored as shown below, where the subsystem type is 'chassis', the id is '1'.

.. code-block:: python

    device.subsystems = {
      'chassis,1':
        {
        'fans': {},
        'interfaces': {},
        'power_supplies':
            {
            '1/1':
                {
                'characteristics':
                    {
                    'instantaneous_power': 131,
                    'maximum_power': 680
                    },
                'identity':
                    {
                    'airflow': 'F2B',
                    'description': 'Aruba X372 54VDC 680W PS',
                    'hardware_rev': '10',
                    'input_voltage_high': 240,
                    'input_voltage_low': 100,
                    'model_number': '0957-2475',
                    'product_name': 'JL086A',
                    'serial_number': 'TH33GZ9DBB',
                    'voltage_type': 'AC'
                    },
                'name': '1/1',
                'redundant_psu': [],
                'statistics':
                    {
                    'failures': 0, 'warnings': 0
                    },
                'status': 'ok'
                },
            '1/2':
                {
                'characteristics':
                    {
                        'instantaneous_power': 0,
                        'maximum_power': 0
                    },
                'identity':
                    {
                    'description': 'N/A',
                    'hardware_rev': 'N/A',
                    'model_number': 'N/A',
                    'product_name': 'N/A',
                    'serial_number': 'N/A'
                    },
                'name': '1/2',
                'redundant_psu': [],
                'statistics':
                    {
                    'failures': 0,
                    'warnings': 0
                    },
                'status': 'fault_absent',
                }
            },


