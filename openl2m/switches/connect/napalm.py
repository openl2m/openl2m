#
# This file is part of Open Layer 2 Management (OpenL2M).
#
# OpenL2M is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with OpenL2M. If not, see <http://www.gnu.org/licenses/>.
#

from switches.connect.classes import *

"""
Basic Napalm connector. This allows us to handle any device supported by
the Napalm Library, at least in read-only mode.
"""


class NapalmConnector(Connector):
    """
    This class implements a "Napalm" connector to get switch information.
    """

    def __init__(self, request=False, group=False, switch=False):
        """
        Initialize the object
        """
        super(Connector, self).__init__(request, group, switch)
        self.name = "NaPalm Library Connector"
        return
