"""License.

Copyright 2018 Todd Mueller <firstnamelastname@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import socket
import threading
import logging
from time import sleep

log = logging.getLogger('tello')


class Tello:
    """Wrapper to simplify interactions with the Ryze Tello drone."""

    def __init__(self, local_ip='', local_port=8889, command_timeout=.3, tello_ip='192.168.10.1', tello_port=8889):
        """Binds to the local IP/port and puts the Tello into command mode.

        Args:
            local_ip (str): Local IP address to bind.
            local_port (int): Local port to bind.
            command_timeout (int|float): Number of seconds to wait for a response to a command.
            tello_ip (str): Tello IP.
            tello_port (int): Tello port.

        Raises:
            RuntimeError: If the Tello rejects the attempt to enter command mode.
        """
        self.timed_out = False
        self.command_timeout = command_timeout
        self.response = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tello_address = (tello_ip, tello_port)
        self.socket.bind((local_ip, local_port))

        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        if self.send('command') != 'OK':
            raise RuntimeError('Tello rejected attempt to enter command mode')

    def __del__(self):
        """Close the local socket."""
        self.socket.close()

    def _receive_thread(self):
        """Listen for responses from the Tello.

        Runs as a thread, sets self.response to whatever the Tello last returned.
        """
        while True:
            try:
                self.response, ip = self.socket.recvfrom(256)
                log.info(self.response.decode(encoding="utf-8"))
            except Exception as e:
                log.error(e)

    def flip(self, direction):
        """Flip.

        Args:
            direction (str): Direction to flip, 'l', 'r', 'f', 'b', 'lb', 'lf', 'rb' or 'rf'.
        """
        return self.send('flip %s' % direction)

    def battery_percent_remaining(self):
        return self.send('battery?')

    def flight_time_seconds(self):
        return int(self.send('time?'))

    def get_speed(self):
        """Return the current speed in cm/s."""
        return float(self.send('speed?'))

    def land(self):
        return self.send('land')

    def move(self, direction, distance):
        """Move in a direction for a distance.

        Args:
            direction (str): Direction to move, 'forward', 'back', 'right' or 'left'.
            distance (int|float): Distance to move, in cm.
        """

        return self.send('%s %s' % (direction, distance))

    def down(self, distance):
        return self.move('down', distance)

    def up(self, distance):
        return self.move('up', distance)

    def backward(self, distance):
        return self.move('back', distance)

    def forward(self, distance):
        return self.move('forward', distance)

    def left(self, distance):
        return self.move('left', distance)

    def right(self, distance):
        return self.move('right', distance)

    def send(self, command):
        """Send a command to the Tello and wait for a response.

        If self.command_timeout is exceeded before a response is received,
        a RuntimeError exception is raised.

        Args:
            command (str): Command to send.

        Returns:
            str: Response from Tello.

        Raises:
            RuntimeError: If no response is received within self.timeout seconds.
        """
        log.info(command)
        self.timed_out = False
        timer = threading.Timer(self.command_timeout, self._time_out)
        self.socket.sendto(command.encode('utf-8'), self.tello_address)
        timer.start()

        while self.response is None:
            if self.timed_out:
                raise RuntimeError('No response to %s' % command)
            sleep(.01)

        timer.cancel()
        decoded_response = self.response.decode('utf-8')
        self.response = None

        return decoded_response

    def _time_out(self):
        self.timed_out = True

    def set_speed(self, speed):
        """Set speed.

        Args:
            speed (int|float): Speed in cm/s.
        """

        return self.send('speed %s' % speed)

    def take_off(self, delay=5):
        response = self.send('takeoff')
        sleep(delay)
        return response

    def rotate(self, degrees):
        """Rotate counterclockwise when degrees is positive and clockwise when negative.

        Args:
            degrees (int): Degrees to rotate, 1 to 360 or -1 to -360.
        """
        ccw = degrees > 0
        cmd = 'ccw' if ccw else 'cw'
        return self.send('%s %s' % (cmd, degrees if ccw else -degrees))
