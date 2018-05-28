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
            imperial (bool): If True, speed is MPH and distance is feet.
                             If False, speed is KPH and distance is meters.
            command_timeout (int|float): Number of seconds to wait for a response to a command.
            tello_ip (str): Tello IP.
            tello_port (int): Tello port.

        Raises:
            RuntimeError: If the Tello rejects the attempt to enter command mode.
        """

        self.abort_flag = False
        self.command_timeout = command_timeout
        self.response = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.tello_address = (tello_ip, tello_port)

        self.socket.bind((local_ip, local_port))

        self.receive_thread = threading.Thread(target=self._receive_thread)
        self.receive_thread.daemon = True

        self.receive_thread.start()

        if self.send_command('command') != 'OK':
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
            except Exception:
                break

    def flip(self, direction):
        """Flip.

        Args:
            direction (str): Direction to flip, 'l', 'r', 'f', 'b', 'lb', 'lf', 'rb' or 'rf'.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.send_command('flip %s' % direction)

    def get_battery(self):
        """Return percent battery life remaining.

        Returns:
            int: Percent battery life remaining.

        """

        return self.send_command('battery?')

    def get_flight_time(self):
        """Return the number of seconds elapsed during flight.

        Returns:
            int: Seconds elapsed during flight.
        """

        return int(self.send_command('time?'))

    def get_speed(self):
        """Return the current speed.

        Returns:
            float: Current speed in cm/s.
        """

        return float(self.send_command('speed?'))

    def land(self):
        """Initiate landing.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """

        return self.send_command('land')

    def move(self, direction, distance):
        """Move in a direction for a distance.

        Args:
            direction (str): Direction to move, 'forward', 'back', 'right' or 'left'.
            distance (int|float): Distance to move, in cm.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """

        return self.send_command('%s %s' % (direction, distance))

    def move_backward(self, distance):
        """Move backward for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('back', distance)

    def move_down(self, distance):
        """Move down for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('down', distance)

    def move_forward(self, distance):
        """Move forward for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        return self.move('forward', distance)

    def move_left(self, distance):
        """Move left for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """
        return self.move('left', distance)

    def move_right(self, distance):
        """Move right for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        """
        return self.move('right', distance)

    def move_up(self, distance):
        """Move up for a distance.

        See comments for Tello.move().

        Args:
            distance (int): Distance to move.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.

        """

        return self.move('up', distance)

    def send_command(self, command):
        """Send a command to the Tello and waits for a response.

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
        self.abort_flag = False
        timer = threading.Timer(self.command_timeout, self.set_abort_flag)

        self.socket.sendto(command.encode('utf-8'), self.tello_address)

        timer.start()

        while self.response is None:
            if self.abort_flag:
                raise RuntimeError('No response to command')
            sleep(.01)

        timer.cancel()
        decoded_response = self.response.decode('utf-8')
        self.response = None

        return decoded_response

    def set_abort_flag(self):
        """Set self.abort_flag to True.

        Used by the timer in Tello.send_command() to indicate to that a response
        timeout has occurred.
        """

        self.abort_flag = True

    def set_speed(self, speed):
        """Set speed.

        Args:
            speed (int|float): Speed in cm/s.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """

        return self.send_command('speed %s' % speed)

    def take_off(self):
        """Initiate take-off.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """
        return self.send_command('takeoff')

    def rotate_cw(self, degrees):
        """Rotate clockwise.

        Args:
            degrees (int): Degrees to rotate, 1 to 360.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """
        return self.send_command('cw %s' % degrees)

    def rotate_ccw(self, degrees):
        """Rotate counter-clockwise.

        Args:
            degrees (int): Degrees to rotate, 1 to 360.

        Returns:
            str: Response from Tello, 'OK' or 'FALSE'.
        """
        return self.send_command('ccw %s' % degrees)
