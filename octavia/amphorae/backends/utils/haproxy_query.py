# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import csv
import socket

from oslo_log import log as logging

from octavia.common import constants as consts
from octavia.common import utils as octavia_utils
from octavia.i18n import _

LOG = logging.getLogger(__name__)


class HAProxyQuery(object):
    """Class used for querying the HAProxy statistics socket.

    The CSV output is defined in the HAProxy documentation:

    http://cbonte.github.io/haproxy-dconv/configuration-1.4.html#9
    """

    def __init__(self, stats_socket):
        """Initialize the class

        :param stats_socket: Path to the HAProxy statistics socket file.
        """

        self.socket = stats_socket

    def _query(self, query):
        """Send the given query to the haproxy statistics socket.

        :returns: the output of a successful query as a string with trailing
                  newlines removed, or raise an Exception if the query fails.
        """

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        try:
            sock.connect(self.socket)
        except socket.error as e:
            raise Exception(
                _("HAProxy '{0}' query failed.").format(query)) from e

        try:
            sock.send(octavia_utils.b(query + '\n'))
            data = ''
            while True:
                x = sock.recv(1024)
                if not x:
                    break
                data += x.decode('ascii') if (
                    isinstance(x, bytes)) else x
            return data.rstrip()
        finally:
            sock.close()

    def show_info(self):
        """Get and parse output from 'show info' command."""
        results = self._query('show info')

        dict_results = {}
        for r in results.split('\n'):
            vals = r.split(":", 1)
            dict_results[vals[0].strip()] = vals[1].strip()
        return dict_results

    def show_stat(self, proxy_iid=-1, object_type=-1, server_id=-1):
        """Get and parse output from 'show stat' command.

        :param proxy_iid: Proxy ID (column 27 in CSV output). -1 for all.
        :param object_type: Select the type of dumpable object. Values can
                            be ORed.
                            -1 - everything
                            1 - frontends
                            2 - backends
                            4 - servers
        :param server_id: Server ID (column 28 in CSV output?), or -1
                          for everything.
        :returns: stats (split into an array by newline)

        """

        results = self._query(
            'show stat {proxy_iid} {object_type} {server_id}'.format(
                proxy_iid=proxy_iid,
                object_type=object_type,
                server_id=server_id))
        list_results = results[2:].split('\n')
        csv_reader = csv.DictReader(list_results)
        stats_list = list(csv_reader)
        # We don't want to report the internal prometheus proxy stats
        # up to the control plane as it shouldn't be billed traffic
        return [stat for stat in stats_list
                if "prometheus" not in stat['pxname']]

    def get_pool_status(self):
        """Get status for each server and the pool as a whole.

        :returns: pool data structure
                  {<pool-name>: {
                  'uuid': <uuid>,
                  'status': 'UP'|'DOWN',
                  'members': [<name>: 'UP'|'DOWN'|'DRAIN'|'no check'] }}
        """

        results = self.show_stat(object_type=6)  # servers + pool

        final_results = {}
        for line in results:
            # pxname: pool, svname: server_name, status: status

            # We don't want to report the internal prometheus proxy stats
            # up to health manager as it shouldn't be billed traffic
            if 'prometheus' in line['pxname']:
                continue

            if line['pxname'] not in final_results:
                final_results[line['pxname']] = dict(members={})

            if line['svname'] == 'BACKEND':
                # BACKEND describes a pool of servers in HAProxy
                pool_id, listener_id = line['pxname'].split(':')
                final_results[line['pxname']]['pool_uuid'] = pool_id
                final_results[line['pxname']]['listener_uuid'] = listener_id
                final_results[line['pxname']]['status'] = line['status']
            else:
                # Due to a bug in some versions of HAProxy, DRAIN mode isn't
                # calculated correctly, but we can spoof the correct
                # value here.
                if line['status'] == consts.UP and line['weight'] == '0':
                    line['status'] = consts.DRAIN

                final_results[line['pxname']]['members'][line['svname']] = (
                    line['status'])
        return final_results

    def save_state(self, state_file_path):
        """Save haproxy connection state to a file.

        :param state_file_path: Absolute path to the state file

        :returns: bool (True if success, False otherwise)
        """

        try:
            result = self._query('show servers state')
            # No need for binary mode, the _query converts bytes to ascii.
            with open(state_file_path, 'w', encoding='utf-8') as fh:
                fh.write(result)
            return True
        except Exception as e:
            # Catch any exception - may be socket issue, or write permission
            # issue as well.
            LOG.warning("Unable to save state: %r", e)
            return False
