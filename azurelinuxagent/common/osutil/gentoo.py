#
# Copyright 2018 Microsoft Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Requires Python 2.6+ and Openssl 1.0+
#

import os
import azurelinuxagent.common.utils.shellutil as shellutil
from azurelinuxagent.common.osutil.default import DefaultOSUtil


class GentooUtil(DefaultOSUtil):

    def __init__(self):
        super(GentooUtil, self).__init__()
        self.jit_enabled = True
        self._is_systemd_manager_cached = None

    @property
    def _is_systemd_manager(self):
        # Avoids circular import.
        if self._is_systemd_manager_cached is None:
            from azurelinuxagent.common.cgroups import CGroups
            self._is_systemd_manager_cached = CGroups.is_systemd_manager
        return self._is_systemd_manager_cached

    def is_dhcp_enabled(self):
        return True

    def start_network(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl start systemd-networkd", chk_err=False)
        else:
            return shellutil.run("rc-service dhcpcd start", chk_err=False)

    def stop_network(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl stop systemd-networkd", chk_err=False)
        else:
            return shellutil.run("rc-service dhcpcd stop", chk_err=False)

    def start_dhcp_service(self):
        return self.start_network()

    def stop_dhcp_service(self):
        return self.stop_network()

    def start_agent_service(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl start waagent", chk_err=False)
        else:
            return shellutil.run("rc-service waaget start", chk_err=False)

    def stop_agent_service(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl stop waagent", chk_err=False)
        else:
            return shellutil.run("rc-service waaget stop", chk_err=False)

    def register_agent_service(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl enable waagent", chk_err=False)
        else:
            return shellutil.run("rc-update add waagent", chk_err=False)

    def unregister_agent_service(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl disable waagent", chk_err=False)
        else:
            return shellutil.run("rc-update delete waagent", chk_err=False)

    def restart_ssh_service(self):
        if self._is_systemd_manager:
            return shellutil.run("systemctl restart sshd", chk_err=False)
        else:
            return shellutil.run("rc-service sshd restart", chk_err=False)

    def get_dhcp_pid(self):
        if self._is_systemd_manager:
            ret = shellutil.run_get_output("pidof systemd-networkd")
        else:
            ret = shellutil.run_get_output("pidof dhcpcd")
        return ret[1] if ret[0] == 0 else None

    def restart_if(self, ifname, retries=3, wait=5):
        """
        Restart an interface by bouncing the link. systemd-networkd observes
        this event, and forces a renew of DHCP.
        """
        retry_limit=retries+1
        for attempt in range(1, retry_limit):
            return_code=shellutil.run("ip link set {0} down && ip link set {0} up".format(ifname))
            if return_code == 0:
                return
            logger.warn("failed to restart {0}: return code {1}".format(ifname, return_code))
            if attempt < retry_limit:
                logger.info("retrying in {0} seconds".format(wait))
                time.sleep(wait)
            else:
                logger.warn("exceeded restart retries")
