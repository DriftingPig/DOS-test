import time
import Pyro4
import threading
from queue import Queue
import sys
def shutter(spi, spiQueue):
	while(1):
		cmd = spiQueue.get(True)
		spi.nir_shutter(cmd)

if __name__ == "__main__":
	uri5="PYRO:SPECTCON5@140.254.79.249:35436"
	sp5 = Pyro4.Proxy(uri5)
	uri6="PYRO:SPECTCON6@140.254.79.216:34761"
	sp6 = Pyro4.Proxy(uri6)
	uri7="PYRO:SPECTCON7@140.254.79.240:40502" 
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
		sp_queue[0].put('open')
		sp_queue[1].put('open')
		sp_queue[2].put('open')
		time.sleep(5)
		sp_queue[0].put('close')
		sp_queue[1].put('close')
		sp_queue[2].put('close')
		value = input('Continue? Y/N\n')
		
	sys.exit()
