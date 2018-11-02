"""
   DOS class to support petal controller based illumination systems
   (for the CI, the Sky Camera etc)
   The code is based on the illuminator.py and petal.py software

   Version History
   04/22/2018     KH     Initial version
                         
"""
import time, os, sys, re
import threading
import Pyro4
import datetime

import DOSlib.logger as Log
from DOSlib.PML import SUCCESS, FAILED
from DOSlib.advertise import Seeker
from DOSlib.util import raise_error

class Fiducials():
    def __init__(self, device, controller_type = 'simulator', service = 'PetalControl', device_options = {}):
        """
        Initialize fiducials class
        device is the DOS device name of the BBB controller
        service is the name of the DOS advertiser service used
        device_options configure the fipos controller (CanBus, CanIDs, Relative_Levels, Default_Duty)
        """
        # Defaults
        CanIDs = [784, 1475]
        CanBus = ['can0' for i in range(len(CanIDs))]
        RelLevel = [1.0 for i in range(len(CanIDs))] 
        Duty = [5.0 for i in range(len(CanIDs))] 

        # Log functions
        for level in ['msg', 'debug', 'info', 'warn', 'error']:
            if hasattr(Log, level):
                setattr(self,level, getattr(Log, level))

        # default settings
        self.hardware = 'fiposled' if str(controller_type).lower() in ['hardware', 'fiposled', 'bbb'] else str(controller_type).lower()
        self.petal_controller = device
        config = {'service' : service,
                  'CanBus' : device_options.get('CanBus', CanBus),
                  'CanIDs' : device_options.get('CanIDs', CanIDs),
                  'Relative_Levels' : device_options.get('Relative_Levels', RelLevel),
                  'Default_Duty' : device_options.get('Default_Duty', Duty),
                  'controller': device_options.get('controller','')}

        self.info('fiducials: device %s, controller %s, Config: %r' % (self.petal_controller, self.hardware, config))
        
        # Connect to the controller
        print('89753 config')
        print(config)
        print('89754 config')
        try:
            if str(self.hardware).lower() == 'simulator':
                self.controller = SimulatorLED(self.petal_controller,config)
            elif str(self.hardware).lower() == 'fiposled':
                self.controller = FiposLED(self.petal_controller, config)
            else:
                raise_error('fiducials: Invalid controller_type', level='ERROR', function='init')
        except Exception as e:
            raise_error('fiducials: Exception connecting to LED controller: %s' % str(e), level='ERROR', function='init')

        # Turn fiducials off
        self.info('fiducials: Turning fiducials off')
        self.controller.turn_off()
        
        # get status
        self.info('fiducials: device status: %r' % self.controller.status())
        
    def status(self):
        if not self.controller:
            raise_error('No LED controller connected', level='WARN', function = 'status')
        return self.controller.status()
    
    def turn_on(self, level = None):
        if not self.controller:
            raise_error('No LED controller connected', level='WARN', function='turn_on')
        self.info('turn_on: turning fiducials on')
        self.controller.turn_on(level = level)

    def turn_off(self):
        if not self.controller:
            raise_error('No LED controller connected', level='WARN', function='turn_off')
        self.info('turn_off: turning fiducials off')
        self.controller.turn_off()

    def level(self, level, set_default = False):
        if not self.controller:
            raise_error('No LED controller connected', level='WARN', function='level')
        self.info('level: setting level to %r (set_default = %r)' % (level, set_default))
        self.controller.level(level, set_default = set_default)


######################################
#
# This is the FIPOS_LED class 
#
######################################

class FiposLED(object):
    """
    This class interfaces with the LED DOS application.
    It contains a limited number of functions that correspond to PML functions.
    -Initializes the LEDs
    -status: creates the led_info, which is held in the variable self.controller
    -turn_on, turn_off
    -set: set current (==duty for fipos_LEDs)
    """
    
    def __init__(self, device, config):
        # Log functions
        for level in ['msg', 'debug', 'info', 'warn', 'error']:
            if hasattr(Log, level):
                setattr(self,level, getattr(Log, level))

        self.petal_controller = device
        self.pcomm = None
        self.CanBus = config['CanBus']
        self.CanIDs = config['CanIDs']
        self.Relative_Levels = config['Relative_Levels']
        self.Default_Duty = config['Default_Duty']

        try:
            self.pcomm=FiposComm(device,controller = config["controller"])
        except Exception as e:
            raise_error('FiposComm: Cannot connect to device %s' % self.petal_controller)
        self.controller = {'devices' : self.CanIDs, 'state' : ['off' for i in range(len(self.CanIDs))], 
                           'level' : [0.0 for i in range(len(self.CanIDs))], 'default' : self.Default_Duty}
 
    def get_posfid_info(self):
        """
        Retrieves CAN ids found on the canbus with corresponding sids and software versions.
        """
        try:
            return self.pcomm.call_device('get_posfid_info',self.CanBus)
        except Exception as e:
            return 'FAILED: Can not read devices. Exception: %s' % str(e)

    def status(self):
        """
        Get led status
        """        
        actual_levels = self.pcomm.call_device('get_fid_status')
        if len(actual_levels) != len(self.controller['devices']):
            raise_error('status: petal controller returns incorrect number of items', level='ERROR')
        state = []
        level = []
        for i in range(len(self.controller['devices'])):
            id = self.controller['devices'][i]
            if str(id) in actual_levels:
                value = actual_levels[str(id)]
            else:
                self.error('get_fid_status does not return can id %r' % id)
                continue
            if(-1==value):
                state.append('unknown')
                level.append(0.0)
            elif(0==value):    
                state.append('off')
                level.append(0.0)
            else:
                state.append('on')
                try:
                    v = float(value)
                except Exception as e:
                    raise_error('status: Exception converting actual level: %s' % str(e))
                level.append(float(int(v/float(self.Relative_Levels[i]))))
            self.controller['level'] = level
            self.controller['state'] = state
        return self.controller
        
    def turn_on(self, level = None):
        """
        Turn on the LEDs by setting the duty to the default value
        """
        return self.level(level if level != None else self.Default_Duty)
        
    def turn_off(self):
        """
        Disable the LED channel
        """
        return self.level(0)

    def level(self, percent_duty, set_default = False):
        """
        Set the LED value
        """
        if not isinstance(percent_duty, list):
            percent_duty = [percent_duty for i in range(len(self.CanIDs))]
        if set_default == True:
            self.Default_Duty = percent_duty
            self.controller['default'] = percent_duty
        try:
            return self.pcomm.call_device('set_fiducials', self.CanBus, self.CanIDs, percent_duty)
        except Exception as e:
            raise_error('Exception setting level: %s'% str(e), level='ERROR', function= 'level')
        
            
######################################
#
# This is the simulator class for the illuminator hardware
# A similar class has to be written for the real thing
#
######################################
class SimulatorLED(object):
    """
    This class interfaces with the LED DOS application.
    It contains a limited number of functions that correspond to PML functions.
    -Initializes the LEDs
    -status: creates the led_info, which is held in the variable self.controller
    -turn_on, turn_off
    -set: set brightness (==duty for fipos_LEDs)
    """
    
    def __init__(self, device, config={}):
        self.petal_controller = device
        self.pcomm = None
        self.CanIDs = config.get('CanIDs', [1,2])
        self.CanBus = config.get('CanBus', ['can0' for i in range(len(self.CanIDs))])
        self.Relative_Levels = config.get('Relative_Levels', [1.0 for i in range(len(self.CanIDs))])
        self.Default_Duty = config.get('Default_Duty',  [5 for i in range(len(self.CanIDs))])
        self.controller = {'devices' : self.CanIDs, 'state' : ['off' for i in range(len(self.CanIDs))], 
                           'level' : [0.0 for i in range(len(self.CanIDs))], 'default' : self.Default_Duty}
 
    def status(self):
        """
        Get led status
        """
        return self.controller

    def turn_on(self, level = None):
        """
        Turn on the LEDs by setting the duty to the default value
        """
        return self.level(self.Default_Duty)
        
    def turn_off(self, level = None):
        """
        Disable the LED channel
        """
        return self.level(0)

    def level(self, value, set_default = False):
        """
        Set the LED value
        """
        on_flag = False
        if isinstance(value,list):
                for value_i in value:
                        if value_i > 0.00001:
                                on_flag = True
        else:
                if value > 0.00001:
                        on_flag = True
        if on_flag is False:
            self.controller['state'] = ['off' for i in range(len(self.CanIDs))]
            self.controller['level'] = [0.0  for i in range(len(self.CanIDs))]
        else:
            self.controller['state'] = ['on'  for i in range(len(self.CanIDs))]
            if isinstance(value, list):
                if len(value) == len(self.CanIDs):
                    self.controller['level'] = value
                else:
                    print(len(value),len(self.CanIDs))
                    raise_error('Incorrect list length', level='ERROR')
            else:
                self.controller['level'] = [value  for i in range(len(self.CanIDs))]
            if set_default == True:
                self.controller['default'] = self.controller['level']

#################################################################################
class FiposComm(object):
    """
    Handles communication between the fiducials class and the petal controller
    """

    def __init__(self, device, **options):
        """
        Find the petal controller (device) and connect to it
        Options include the fipos settings for LED control
        """
        # Log functions
        for level in ['msg', 'debug', 'info', 'warn', 'error']:
            if hasattr(Log, level):
                setattr(self,level, getattr(Log, level))

        self.petal_controller = device
        # Setup Seeker
        self.seeker_thread = None
        self.repeat = threading.Event()
        self.repeat.clear()
        self.found_controller = threading.Event()
        self.found_controller.clear()
        self.stype = '-dos-'
        self.service = options.get('service', 'PetalControl')
        self.device = {}
        delay = options.get('delay', 15.0)
        # Did we get controller information or should we seek?
        print('89755')
        print(options)
        print('89756')
        print(options['controller'])
        if 'controller' in options and isinstance(options['controller'], dict):
            print('89757')
            self.device = {'connected2instance': 'EXTERN',
                           'device_instance': '',
                           'last_updated': '',
                           'node': options['controller'].get('ip', '140.254.79.198'),
                           'service': self.service,
                           'stype': self.stype,
                           'uid' : '81df0e9a-9409-11e8-b17c-b0d5cc1ef486',
                           }
            print('89757a')
            print('897575'+str(options['controller']))
            if 'port' in options['controller']:
                print('89758')
                self.device['pyro_uri'] = 'PYRO:%s@%s:%s' % (self.petal_controller,
                                                             str(self.device['node']),
                                                             str(options['controller']['port']))
                print(self.device['pyro_uri'])
        else:
            # Setup DOS Seeker
            self.seeker = Seeker(self.stype, self.service, found_callback = self._found_dev)
            # Start Seeker thread
            self.repeat.set()
            self.delay = 0.5
            self.seeker_thread = threading.Thread(target=self._repeat_seeker)
            self.seeker_thread.setDaemon(True)
            self.seeker_thread.start()
            self.info('Seeker thread is now running. Delay %s' % str(self.delay))
            # wait briefly for seeker to find all devices
            self.info('Waiting for device %s' % self.petal_controller)
            self.found_controller.wait(timeout = delay + 1.0)
            self.delay = 10.0

        # Make sure we have a device to connect to
        start = time.time()
        while self.device == {} and delay<(time.time() - start):
            self.device['proxy'] = Pyro4.Proxy(self.device['pyro_uri'])
            self.info('Now connected to device %s' % self.device)
            break
            
        if self.device == {}:
            raise_error('fipos_comm: Timeout connecting to controller %s' % (self.petal_controller), level='ERROR', function='init')

    def is_connected(self):
        """
        Returns the status of the found_controller flag.
        """
        return self.found_controller.is_set()
    
    # Internal callback and utility functions
    def _repeat_seeker(self):
        while self.repeat.is_set():
            self.seeker.seek()
            time.sleep(self.delay)

    def _found_dev(self, dev):
        for key in dev:
            if dev[key]['service'] == self.service:   # Found a petal controller
                # Extract unit number and compare to self.petal_controller
                if key == self.petal_controller:
                    # Found the matching petal controller
                    if 'name' not in self.device or self.device['name'] != key:
                        self.info('_found_dev: Found new device %s' % str(key))
                        self.device['name'] = key
                    # update proxy information?
                    if 'uid' in self.device and self.device['uid'] != dev[key]['uid']:
                        self.info('_found_dev: Device %s rediscovered.' % key)
                        if 'proxy' in self.device:     # remove potentially stale info
                            del self.device['proxy']
                    self.device.update(dev[key])   # make a copy
                    self.found_controller.set()
                        
    def call_device(self, cmd, *args, **kwargs):
        """
        Call remote function
        Input:  cmd   = function name
                args, kwargs are passed to the remove function
        Returns: return value received from remote function
        """
        try:
            return getattr(self.device['proxy'],cmd)(*args, **kwargs)
        except:
            if 'pyro_uri' in self.device:
                try:
                    self.device['proxy'] = Pyro4.Proxy(self.device['pyro_uri'])
                    return getattr(self.device['proxy'],cmd)(*args, **kwargs)
                except Exception as e:
                    raise RuntimeError('call_device: Exception for command %s. Message: %s' % (str(cmd),str(e)))
            # Failed to get status from device
            raise RuntimeError('call_device: remote device not reachable %s' % '' if 'name' not in self.device else self.device)

