from DOSlib.application import Application
from fiducials import *
from DOSlib.util import raise_error
import sys
class CIFIDS(Application):
	commands = ['select_device','set_fid_on','set_fid_off','duty_cycle','get_fid_status']
	defaults = {'device':'PC61',
		    'controller_type':'simulator',
		    'service':'PetalControl',
		    'CanIDs' : [4840, 4841, 4842, 4843 ,4844 ,4845, 4846, 4847, 4848, 4849,4850, 4851, 4852, 4853, 4854, 4855, 4856, 4857, 4858, 4859, 4870, 4871, 4872, 4873],
		   }
	
	def init(self):
		self.CanIDs = self.config['CanIDs']
		canbus = ['can0' for i in range(len(self.CanIDs))]
		RelLevel = [0.0 for i in range(len(self.CanIDs))]
		Duty = [100.0 for i in range(len(self.CanIDs))]
		self.device = self.config['device']
		self.controller_type = self.config['controller_type']
		self.service = self.config['service']
		self.device_options = {'CanBus':canbus,
					'CanIDs':self.CanIDs,
					'Relative_Levels' : RelLevel,
					'Default_Duty' : Duty,
					'controller': {'ip':'140.254.79.198',
                                                       'port':'33951'}
					}
		self.fiducials = None
		self.info('Currently no device')
		#self.fiducials = Fiducials(controller_type = self.controller_type, service = self.service,device_options = self.device_options)
		
	def select_device(self, controller_name = None):
		if not controller_name:
			controller_name = self.device
		self.fiducials = Fiducials(controller_name, controller_type = self.controller_type, service = self.service,device_options = self.device_options)
		self.info('device selected: %s', controller_name)
		return 'SUCCESS'

	def set_fid_on(self):
		if not self.fiducials:
			raise_error('no fiducials selected', level='ERROR', function = 'set_fiducials_on')
		print(len(self.device_options['Default_Duty']))
		self.fiducials.turn_on(level = self.device_options['Default_Duty'])		
		return 'SUCCESS'

	def set_fid_off(self):
		if not self.fiducials:
			raise_error('no fiducials selected', level='ERROR', function = 'set_fiducials_off')
		self.fiducials.turn_off()
		return 'SUCCESS'

	def duty_cycle(self, level,set_default = False):
		if not self.fiducials:
			raise_error('no fiducials selected', level='ERROR', function = 'duty_cycle')
		if not isinstance(level,list):
			level = [level for i in range(len(self.CanIDs))]
		self.fiducials.level(level, set_default = set_default)
		return 'SUCCESS'

	def get_fid_status(self):
		if not self.fiducials:
			raise_error('no fiducials selected', level='ERROR', function = 'get_fid_status')
		status = self.fiducials.status()
		self.info("fiducials: device %s, state %s, level %s, default_duty %s" % (status['devices'], status['state'], status['level'], status['default']))
		return 'SUCCESS' 

	def main(self):
		while not self.shutdown_event.is_set():
			time.sleep(5)
		print('exiting..')

if __name__ == '__main__':
	try:
		CIFIDS_App = CIFIDS()
		CIFIDS_App.run()
	except Exception as e:
		print('Exception running application: %s' % str(e))
	print('Good bye')
	sys.exit()
