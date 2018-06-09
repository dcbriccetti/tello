import tello
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(threadName)s %(message)s')
log = logging.getLogger('Drone app')
log.info('Starting')


t = tello.Tello(command_timeout=5)
try:
    t.take_off()
    t.flip('f')
except Exception as e:
    log.error(e)
t.land()
