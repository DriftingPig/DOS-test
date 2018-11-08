import time
import Pyro4
import threading
from queue import Queue
import sys
def shutter(spi, spiQueue):
       t_previous = None
       t_next = None
	while(1):
		cmd = spiQueue.get(True)
		spi.nir_shutter(cmd)
                t_previous = t_next
                t_next = time.clock()
                if t_previous is not None;
                     delta_t = t_next - t_previous
                     print(delta_t, "seconds wall time")

if __name__ == "__main__":
	uri5="PYRO:SPECTCON8@140.254.79.216:38916"
	sp5 = Pyro4.Proxy(uri5)
	uri6="PYRO:SPECTCON9@140.254.78.255:35198"
	sp6 = Pyro4.Proxy(uri6)
	uri7="PYRO:SPECTCON10@140.254.79.214:35969" 
	sp7 = Pyro4.Proxy(uri7)
	input('before configure:')
	sp5.configure()
	sp6.configure()
	sp7.configure()
	input('after configure:')
	
	
	SP = [sp5,sp6,sp7]
	sp5_queue = Queue()
	sp6_queue = Queue()
	sp7_queue = Queue()
	sp_queue = [sp5_queue,sp6_queue,sp7_queue]
	for spi in SP: 
        	mi=spi.get('mechanism')
        	if mi['nir_shutter_power'] == 'ON':
                	pass
        	else:
                	spi.power(device = 'nir_shutter',action='on')

        	if mi['nir_shutter_seal'] == 'DEFLATED':
                	pass
        	else:
                	spi.seal(shutter='nir_shutter',action='deflate')

	for i in range(3):
		t = threading.Thread(target=shutter, args=(SP[i],sp_queue[i],))
		t.setDaemon(True)
		t.start()		
	print('test')	
	value = input('Continue? Y/N\n')
	print(value)
	while value != 'N':
		value = input('work order: e.g: 0 1 2\n')
		work_ord = [int(x) for x in value.split()]
		sp_queue[work_ord[0]].put('open')
		sp_queue[work_ord[1]].put('open')
		sp_queue[work_ord[2]].put('open')
		time.sleep(5)
		value = input('Continue closing? Y/N\n')
		sp_queue[work_ord[0]].put('close')
		sp_queue[work_ord[1]].put('close')
		sp_queue[work_ord[2]].put('close')
		value = input('Continue? Y/N\n')
		
	sys.exit()
