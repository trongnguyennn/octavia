..
      Copyright (c) 2016 IBM
      Copyright 2019 Red Hat, Inc. All rights reserved.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.

=============================
Basic Load Balancing Cookbook
=============================

Introduction
============
This document contains several examples of using basic load balancing services
as a tenant or "regular" cloud user.

For the purposes of this guide we assume that the neutron and barbican
command-line interfaces, via the OpenStack client, are going to be used to
configure all features of Octavia. In order to keep these examples short,
we also assume that tasks not directly associated with deploying load balancing
services have already been accomplished. This might include such things as
deploying and configuring web servers, setting up Neutron networks, obtaining
TLS certificates from a trusted provider, and so on. A description of the
starting conditions is given in each example below.

Please also note that this guide assumes you are familiar with the specific
load balancer terminology defined in the :doc:`../../reference/glossary`. For a
description of load balancing itself and the Octavia project, please see:
:doc:`../../reference/introduction`.


Examples
========

Deploy a basic HTTP load balancer
---------------------------------
While this is technically the simplest complete load balancing solution that
can be deployed, we recommend deploying HTTP load balancers with a health
monitor to ensure back-end member availability. See :ref:`basic-lb-with-hm`
below.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers.

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


.. _basic-lb-with-hm:

Deploy a basic HTTP load balancer with a health monitor
-------------------------------------------------------
This is the simplest recommended load balancing solution for HTTP applications.
This solution is appropriate for operators with provider networks that are not
compatible with Neutron floating-ip functionality (such as IPv6 networks).
However, if you need to retain control of the external IP through which a load
balancer is accessible, even if the load balancer needs to be destroyed or
recreated, it may be more appropriate to deploy your basic load balancer using
a floating IP. See :ref:`basic-lb-with-hm-and-fip` below.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTP application on TCP port 80.
* These back-end servers have been configured with a health check at the URL
  path "/healthcheck". See :ref:`http-health-monitors` below.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers, and which
  checks the "/healthcheck" path to ensure back-end member health.

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Create a health monitor on *pool1* which tests the "/healthcheck" path.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer healthmonitor create --delay 5 --max-retries 4 --timeout 10 --type HTTP --url-path /healthcheck pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


.. _basic-lb-with-hm-and-fip:

Deploy a basic HTTP load balancer using a floating IP
-----------------------------------------------------
It can be beneficial to use a floating IP when setting up a load balancer's VIP
in order to ensure you retain control of the IP that gets assigned as the
floating IP in case the load balancer needs to be destroyed, moved, or
recreated.

Note that this is not possible to do with IPv6 load balancers as floating IPs
do not work with IPv6.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTP application on TCP port 80.
* These back-end servers have been configured with a health check at the URL
  path "/healthcheck". See :ref:`http-health-monitors` below.
* Neutron network *public* is a shared external network created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers, and which
  checks the "/healthcheck" path to ensure back-end member health. Further, we
  want to do this using a floating IP.

**Solution**:

1. Create load balancer *lb1* on subnet *private-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Create a health monitor on *pool1* which tests the "/healthcheck" path.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.
6. Create a floating IP address on *public-subnet*.
7. Associate this floating IP with the *lb1*'s VIP port.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id private-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer healthmonitor create --delay 5 --max-retries 4 --timeout 10 --type HTTP --url-path /healthcheck pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1
    openstack floating ip create public
    # The following IDs should be visible in the output of previous commands
    openstack floating ip set --port <load_balancer_vip_port_id> <floating_ip_id>


Deploy a basic HTTP load balancer with session persistence
----------------------------------------------------------
**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTP application on TCP port 80.
* The application is written such that web clients should always be directed to
  the same back-end server throughout their web session, based on an
  application cookie inserted by the web application named 'PHPSESSIONID'.
* These back-end servers have been configured with a health check at the URL
  path "/healthcheck". See :ref:`http-health-monitors` below.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers, persists
  sessions using the PHPSESSIONID as a key, and which checks the "/healthcheck"
  path to ensure back-end member health.

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool which defines session
   persistence on the 'PHPSESSIONID' cookie.
4. Create a health monitor on *pool1* which tests the "/healthcheck" path.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP --session-persistence type=APP_COOKIE,cookie_name=PHPSESSIONID
    openstack loadbalancer healthmonitor create --delay 5 --max-retries 4 --timeout 10 --type HTTP --url-path /healthcheck pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


Deploy a TCP load balancer
--------------------------
This is generally suitable when load balancing a non-HTTP TCP-based service.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an custom application on TCP port 23456
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes requests to the back-end servers.
* We want to employ a TCP health check to ensure that the back-end servers are
  available.

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Create a health monitor on *pool1* which probes *pool1*'s members' TCP
   service port.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol TCP --protocol-port 23456 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol TCP
    openstack loadbalancer healthmonitor create --delay 5 --max-retries 4 --timeout 10 --type TCP pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


Deploy a QoS ruled load balancer
--------------------------------
This solution limits the bandwidth available through the Load Balancer's VIP by
applying a Neutron Quality of Service(QoS) policy to the VIP, so Load Balancer
can accept the QoS Policy from Neutron; Then limits the vip of Load Balancer
incoming or outgoing traffic.

.. note::
   Before using this feature, please make sure the Neutron QoS extension(qos)
   is enabled on running OpenStack environment by command

   .. code-block:: console

      openstack extension list

**Scenario description**:

* QoS-policy created from Neutron with bandwidth-limit-rules by us.
* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer and want to limit the traffic
  bandwidth when web traffic reaches the vip.

**Solution**:

1. Create QoS policy *qos-policy-bandwidth* with *bandwidth_limit* in Neutron.
2. Create load balancer *lb1* on subnet *public-subnet* with the id of
   *qos-policy-bandwidth*.
3. Create listener *listener1*.
4. Create pool *pool1* as *listener1*'s default pool.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack network qos policy create qos-policy-bandwidth
    openstack network qos rule create --type bandwidth_limit --max-kbps 1024 --max-burst-kbits 1024 qos-policy-bandwidth
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet --vip-qos-policy-id qos-policy-bandwidth
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 lb1 --protocol HTTP --protocol-port 80
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id <private_subnet_id> --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id <private_subnet_id> --address 192.0.2.11 --protocol-port 80 pool1


Deploy a load balancer with access control list
-----------------------------------------------
This solution limits incoming traffic to a listener to a set of allowed
source IP addresses. Any other incoming traffic will be rejected.


**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an custom application on TCP port 23456
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes requests to the back-end servers.
* The application on TCP port 23456 is accessible to a limited source IP
  addresses (192.0.2.0/24 and 198.51.100/24).

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1* with allowed CIDRs.
3. Create pool *pool1* as *listener1*'s default pool.
4. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol TCP --protocol-port 23456 --allowed-cidr 192.0.2.0/24 --allowed-cidr 198.51.100/24 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol TCP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


Deploy a non-terminated HTTPS load balancer
-------------------------------------------
A non-terminated HTTPS load balancer acts effectively like a generic TCP load
balancer: The load balancer will forward the raw TCP traffic from the web
client to the back-end servers without decrypting it. This means that the
back-end servers themselves must be configured to terminate the HTTPS
connection with the web clients, and in turn, the load balancer cannot insert
headers into the HTTP session indicating the client IP address. (That is, to
the back-end server, all web requests will appear to originate from the load
balancer.) Also, advanced load balancer features (like Layer 7 functionality)
cannot be used with non-terminated HTTPS.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with a TLS-encrypted web application on TCP port 443.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes requests to the back-end servers.
* We want to employ a TCP health check to ensure that the back-end servers are
  available.

**Solution**:

1. Create load balancer *lb1* on subnet *public-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Create a health monitor on *pool1* which probes *pool1*'s members' TCP
   service port.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTPS --protocol-port 443 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTPS
    openstack loadbalancer healthmonitor create --delay 5 --max-retries 4 --timeout 10 --type HTTPS --url-path /healthcheck pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 443 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 443 pool1


.. _basic-tls-terminated-listener:

Deploy a TLS-terminated HTTPS load balancer
-------------------------------------------
With a TLS-terminated HTTPS load balancer, web clients communicate with the
load balancer over TLS protocols. The load balancer terminates the TLS session
and forwards the decrypted requests to the back-end servers. By terminating the
TLS session on the load balancer, we offload the CPU-intensive encryption work
to the load balancer, and enable the possibility of using advanced load
balancer features, like Layer 7 features and header manipulation.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with regular HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* A TLS certificate, key, and intermediate certificate chain for
  www.example.com have been obtained from an external certificate authority.
  These now exist in the files server.crt, server.key, and ca-chain.crt in the
  current directory. The key and certificate are PEM-encoded, and the
  intermediate certificate chain is multiple PEM-encoded certs concatenated
  together. The key is not encrypted with a passphrase.
* We want to configure a TLS-terminated HTTPS load balancer that is accessible
  from the internet using the key and certificate mentioned above, which
  distributes requests to the back-end servers over the non-encrypted HTTP
  protocol.
* Octavia is configured to use barbican for key management.

**Solution**:

1. Combine the individual cert/key/intermediates to a single PKCS12 file.
2. Create a barbican *secret* resource for the PKCS12 file. We will call
   this *tls_secret1*.
3. Create load balancer *lb1* on subnet *public-subnet*.
4. Create listener *listener1* as a TERMINATED_HTTPS listener referencing
   *tls_secret1* as its default TLS container.
5. Create pool *pool1* as *listener1*'s default pool.
6. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.crt -passout pass: -out server.p12
    openstack secret store --name='tls_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server.p12)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --protocol-port 443 --protocol TERMINATED_HTTPS --name listener1 --default-tls-container=$(openstack secret list | awk '/ tls_secret1 / {print $2}') lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1


Deploy a TLS-terminated HTTPS load balancer with SNI
----------------------------------------------------
This example is exactly like :ref:`basic-tls-terminated-listener`, except that
we have multiple TLS certificates that we would like to use on the same
listener using Server Name Indication (SNI) technology.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with regular HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* TLS certificates, keys, and intermediate certificate chains for
  www.example.com and www2.example.com have been obtained from an external
  certificate authority. These now exist in the files server.crt, server.key,
  ca-chain.crt, server2.crt, server2.key, and ca-chain2.crt in the
  current directory. The keys and certificates are PEM-encoded, and the
  intermediate certificate chains are multiple certs PEM-encoded and
  concatenated together. Neither key is encrypted with a passphrase.
* We want to configure a TLS-terminated HTTPS load balancer that is accessible
  from the internet using the keys and certificates mentioned above, which
  distributes requests to the back-end servers over the non-encrypted HTTP
  protocol.
* If a web client connects that is not SNI capable, we want the load balancer
  to respond with the certificate for www.example.com.

**Solution**:

1. Combine the individual cert/key/intermediates to single PKCS12 files.
2. Create barbican *secret* resources for the PKCS12 files. We will call them
   *tls_secret1* and *tls_secret2*.
3. Create load balancer *lb1* on subnet *public-subnet*.
4. Create listener *listener1* as a TERMINATED_HTTPS listener referencing
   *tls_secret1* as its default TLS container, and referencing both
   *tls_secret1* and *tls_secret2* using SNI.
5. Create pool *pool1* as *listener1*'s default pool.
6. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.crt -passout pass: -out server.p12
    openssl pkcs12 -export -inkey server2.key -in server2.crt -certfile ca-chain2.crt -passout pass: -out server2.p12
    openstack secret store --name='tls_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server.p12)"
    openstack secret store --name='tls_secret2' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server2.p12)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --protocol-port 443 --protocol TERMINATED_HTTPS --name listener1 --default-tls-container=$(openstack secret list | awk '/ tls_secret1 / {print $2}') --sni-container-refs $(openstack secret list | awk '/ tls_secret1 / {print $2}') $(openstack secret list | awk '/ tls_secret2 / {print $2}') -- lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1

Deploy a TLS-terminated HTTPS load balancer with client authentication
----------------------------------------------------------------------
With a TLS-terminated HTTPS load balancer, web clients communicate with the
load balancer over TLS protocols. The load balancer terminates the TLS session
and forwards the decrypted requests to the back-end servers. By terminating the
TLS session on the load balancer, we offload the CPU-intensive encryption work
to the load balancer, and enable the possibility of using advanced load
balancer features, like Layer 7 features and header manipulation.
Adding client authentication allows users to authenticate connections
to the VIP using certificates. This is also known as two-way TLS
authentication.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with a regular HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* A TLS certificate, key, and intermediate certificate chain for
  www.example.com have been obtained from an external certificate authority.
  These now exist in the files server.crt, server.key, and ca-chain.crt in the
  current directory. The key and certificate are PEM-encoded, and the
  intermediate certificate chain is multiple PEM-encoded certificates
  concatenated together. The key is not encrypted with a passphrase.
* A Certificate Authority (CA) certificate chain and optional Certificate
  Revocation List (CRL) have been obtained from an external certificate
  authority to authenticate client certificates against.
* We want to configure a TLS-terminated HTTPS load balancer that is accessible
  from the internet using the key and certificate mentioned above, which
  distributes requests to the back-end servers over the non-encrypted HTTP
  protocol.
* Octavia is configured to use barbican for key management.

**Solution**:

1. Combine the individual cert/key/intermediates to a single PKCS12 file.
2. Create a barbican *secret* resource for the PKCS12 file. We will call
   this *tls_secret1*.
3. Create a barbican *secret* resource for the client CA certificate. We will
   call this *client_ca_cert*.
4. Optionally create a barbican *secret* for the CRL file. We will call this
   *client_ca_crl*.
5. Create load balancer *lb1* on subnet *public-subnet*.
6. Create listener *listener1* as a TERMINATED_HTTPS listener referencing
   *tls_secret1* as its default TLS container, client authentication enabled,
   *client_ca_cert* as the client CA tls container reference, and
   *client_ca_crl* as the client CRL container reference.
7. Create pool *pool1* as *listener1*'s default pool.
8. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.crt -passout pass: -out server.p12
    openstack secret store --name='tls_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server.p12)"
    openstack secret store --name='client_ca_cert' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < client_ca.pem)"
    openstack secret store --name='client_ca_crl' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < client_ca.crl)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --protocol-port 443 --protocol TERMINATED_HTTPS --name listener1 --default-tls-container=$(openstack secret list | awk '/ tls_secret1 / {print $2}') --client-authentication=MANDATORY --client-ca-tls-container-ref=$(openstack secret list | awk '/ client_ca_cert / {print $2}') --client-crl-container=$(openstack secret list | awk '/ client_ca_crl / {print $2}') lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1

Deploy a secure HTTP/2 load balancer with ALPN TLS extension
------------------------------------------------------------
This example is exactly like :ref:`basic-tls-terminated-listener`, except that
we would like to enable HTTP/2 load balancing. The load balancer negotiates
HTTP/2 with clients as part of the TLS handshake via the Application-Layer
Protocol Negotiation (ALPN) TLS extension.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with regular HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* A TLS certificate, key, and intermediate certificate chain for
  www.example.com have been obtained from an external certificate authority.
  These now exist in the files server.crt, server.key, and ca-chain.crt in the
  current directory. The key and certificate are PEM-encoded, and the
  intermediate certificate chain is multiple PEM-encoded certs concatenated
  together. The key is not encrypted with a passphrase.
* We want to configure a TLS-terminated HTTP/2 load balancer that is accessible
  from the internet using the key and certificate mentioned above, which
  distributes requests to the back-end servers over the non-encrypted HTTP
  protocol.
* Octavia is configured to use barbican for key management.

**Solution**:

1. Combine the individual cert/key/intermediates to a single PKCS12 file.
2. Create a barbican *secret* resource for the PKCS12 file. We will call
   this *tls_secret1*.
3. Create load balancer *lb1* on subnet *public-subnet*.
4. Create listener *listener1* as a TERMINATED_HTTPS listener referencing
   *tls_secret1* as its default TLS container, and *h2* ALPN protocol ID and
   *http/1.1* as fall-back protocol should the client not support HTTP/2.
5. Create pool *pool1* as *listener1*'s default pool.
6. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.crt -passout pass: -out server.p12
    openstack secret store --name='tls_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server.p12)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --protocol-port 443 --protocol TERMINATED_HTTPS --alpn-protocol h2 --alpn-protocol http/1.1 --name listener1 --default-tls-container=$(openstack secret list | awk '/ tls_secret1 / {print $2}') lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1

Deploy HTTP and TLS-terminated HTTPS load balancing on the same IP and backend
------------------------------------------------------------------------------
This example is exactly like :ref:`basic-tls-terminated-listener`, except that
we would like to have both an HTTP and TERMINATED_HTTPS listener that use the
same back-end pool (and therefore, probably respond with the exact same
content regardless of whether the web client uses the HTTP or HTTPS protocol
to connect).

Please note that if you wish all HTTP requests to be redirected to HTTPS (so
that requests are only served via HTTPS, and attempts to access content over
HTTP just get redirected to the HTTPS listener), then please see `the example
<l7-cookbook.html#redirect-http-to-https>`__ in the :doc:`l7-cookbook`.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with regular HTTP application on TCP port 80.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* A TLS certificate, key, and intermediate certificate chain for
  www.example.com have been obtained from an external certificate authority.
  These now exist in the files server.crt, server.key, and ca-chain.crt in the
  current directory. The key and certificate are PEM-encoded, and the
  intermediate certificate chain is multiple PEM-encoded certs concatenated
  together. The key is not encrypted with a passphrase.
* We want to configure a TLS-terminated HTTPS load balancer that is accessible
  from the internet using the key and certificate mentioned above, which
  distributes requests to the back-end servers over the non-encrypted HTTP
  protocol.
* We also want to configure a HTTP load balancer on the same IP address as
  the above which serves the exact same content (ie. forwards to the same
  back-end pool) as the TERMINATED_HTTPS listener.

**Solution**:

1. Combine the individual cert/key/intermediates to a single PKCS12 file.
2. Create a barbican *secret* resource for the PKCS12 file. We will call
   this *tls_secret1*.
3. Create load balancer *lb1* on subnet *public-subnet*.
4. Create listener *listener1* as a TERMINATED_HTTPS listener referencing
   *tls_secret1* as its default TLS container.
5. Create pool *pool1* as *listener1*'s default pool.
6. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.
7. Create listener *listener2* as an HTTP listener with *pool1* as its
   default pool.

**CLI commands**:

::

    openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.crt -passout pass: -out server.p12
    openstack secret store --name='tls_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < server.p12)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --protocol-port 443 --protocol TERMINATED_HTTPS --name listener1 --default-tls-container=$(openstack secret list | awk '/ tls_secret1 / {print $2}') lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 80 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 80 pool1
    openstack loadbalancer listener create --protocol-port 80 --protocol HTTP --name listener2 --default-pool pool1 lb1

Deploy a load balancer with backend re-encryption
-------------------------------------------------
This example will demonstrate how to enable TLS encryption from the load
balancer to the backend member servers. Typically this is used with TLS
termination enabled on the listener, but, to simplify the example, we are going
to use an unencrypted HTTP listener. For information on setting up a TLS
terminated listener, see the above section
:ref:`basic-tls-terminated-listener`.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTPS application on TCP port 443.
* A Certificate Authority (CA) certificate chain and optional Certificate
  Revocation List (CRL) have been obtained from an external certificate
  authority to authenticate member server certificates against.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers.

**Solution**:

1. Create a barbican *secret* resource for the member CA certificate. We will
   call this *member_ca_cert*.
2. Optionally create a barbican *secret* for the CRL file. We will call this
   *member_ca_crl*.
3. Create load balancer *lb1* on subnet *public-subnet*.
4. Create listener *listener1*.
5. Create pool *pool1* as *listener1*'s default pool, that is TLS enabled, with
   a Certificate Authority (CA) certificate chain *member_ca_cert* to validate
   the member server certificate, and a Certificate Revocation List (CRL)
   *member_ca_crl* to check the member server certificate against.
6. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack secret store --name='member_ca_cert' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < member_ca.pem)"
    openstack secret store --name='member_ca_crl' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < member_ca.crl)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP --enable-tls --ca-tls-container-ref $(openstack secret list | awk '/ member_ca_cert / {print $2}') --crl-container-ref $(openstack secret list | awk '/ member_ca_crl / {print $2}')
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 443 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 443 pool1

Deploy a load balancer with backend re-encryption and client authentication
---------------------------------------------------------------------------
This example will demostrate how to enable TLS encryption from the load
balancer to the backend member servers with the load balancer being
authenticated using TLS client authentication. Typically this is used with TLS
termination enabled on the listener, but, to simplify the example, we are going
to use an unencrypted HTTP listener. For information on setting up a TLS
terminated listener, see the above section
:ref:`basic-tls-terminated-listener`.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an HTTPS application on TCP port 443.
* A Certificate Authority (CA) certificate chain and optional Certificate
  Revocation List (CRL) have been obtained from an external certificate
  authority to authenticate member server certificates against.
* A TLS certificate and key have been obtained from an external Certificate
  Authority (CA). The now exist in the files member.crt and member.key. The
  key and certificate are PEM-encoded and the key is not encrypted with a
  passphrase (for this example).
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes web requests to the back-end servers.

**Solution**:

1. Combine the member client authentication certificate and key to a single
   PKCS12 file.
2. Create a barbican *secret* resource for the PKCS12 file. We will call
   this *member_secret1*.
3. Create a barbican *secret* resource for the member CA certificate. We will
   call this *member_ca_cert*.
4. Optionally create a barbican *secret* for the CRL file. We will call this
   *member_ca_crl*.
5. Create load balancer *lb1* on subnet *public-subnet*.
6. Create listener *listener1*.
7. Create pool *pool1* as *listener1*'s default pool, that is TLS enabled, with
   a TLS container reference for the member client authentication key and
   certificate pkcs12, also with a Certificate Authority (CA) certificate chain
   *member_ca_cert* to validate the member server certificate, and a
   Certificate Revocation List (CRL) *member_ca_crl* to check the member server
   certificate against.
8. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openssl pkcs12 -export -inkey member.key -in member.crt -passout pass: -out member.p12
    openstack secret store --name='member_secret1' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < member.p12)"
    openstack secret store --name='member_ca_cert' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < member_ca.pem)"
    openstack secret store --name='member_ca_crl' -t 'application/octet-stream' -e 'base64' --payload="$(base64 < member_ca.crl)"
    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol HTTP --protocol-port 80 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol HTTP --enable-tls --ca-tls-container-ref $(openstack secret list | awk '/ member_ca_cert / {print $2}') --crl-container-ref $(openstack secret list | awk '/ member_ca_crl / {print $2}') --tls-container-ref $(openstack secret list | awk '/ member_secret1 / {print $2}')
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 443 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 443 pool1

Deploy a UDP load balancer with a health monitor
------------------------------------------------

This is a load balancer solution suitable for UDP-based services.

**Scenario description**:

* Back-end servers 192.0.2.10 and 192.0.2.11 on subnet *private-subnet* have
  been configured with an application on UDP port 1234.
* Subnet *public-subnet* is a shared external subnet created by the cloud
  operator which is reachable from the internet.
* We want to configure a basic load balancer that is accessible from the
  internet, which distributes requests to the back-end servers.
* We want to employ a UDP health check to ensure that the back-end servers are
  available. UDP health checks may not work correctly if ICMP Destination
  Unreachable (ICMP type 3) messages are blocked by a security rule (see
  :ref:`other-health-monitors`).

**Solution**:

1. Create load balancer *lb1* on subnet *private-subnet*.
2. Create listener *listener1*.
3. Create pool *pool1* as *listener1*'s default pool.
4. Create a health monitor on *pool1* which connects to the back-end servers.
5. Add members 192.0.2.10 and 192.0.2.11 on *private-subnet* to *pool1*.

**CLI commands**:

::

    openstack loadbalancer create --name lb1 --vip-subnet-id public-subnet
    # Re-run the following until lb1 shows ACTIVE and ONLINE statuses:
    openstack loadbalancer show lb1
    openstack loadbalancer listener create --name listener1 --protocol UDP --protocol-port 1234 lb1
    openstack loadbalancer pool create --name pool1 --lb-algorithm ROUND_ROBIN --listener listener1 --protocol UDP
    openstack loadbalancer healthmonitor create --delay 3 --max-retries 2 --timeout 2 --type UDP-CONNECT pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.10 --protocol-port 1234 pool1
    openstack loadbalancer member create --subnet-id private-subnet --address 192.0.2.11 --protocol-port 1234 pool1


.. _health-monitor-best-practices:

Health Monitor Best Practices
=============================
An Octavia health monitor is a process that does periodic health checks on each
back-end member to pre-emptively detect failed members and temporarily
pull them out of the pool.

If the health monitor detects a failed member, it removes it from the pool and
marks the member in ERROR. After you have corrected the member and it is
functional again, the health monitor automatically changes the status of the
member from ERROR to ONLINE, and resumes passing traffic to it.

Always use health monitors in production load balancers. If you do not have a
health monitor, failed members are not removed from the pool. This can lead to
service disruption for web clients.

See also the command, `loadbalancer healthmonitor create <https://docs.openstack.org/python-octaviaclient/latest/cli/index.html#loadbalancer-healthmonitor-create>`_.

.. _all-health-monitors:

Configuration arguments for all health monitors
-----------------------------------------------

All health monitor types for Octavia require the following configurable
arguments:

* ``delay``: Number of seconds to wait between health checks.
* ``timeout``: Number of seconds to wait for any given health check to
  complete. ``timeout`` should always be smaller than ``delay``.
* ``max-retries``: Number of subsequent health checks a given back-end
  server must fail before it is considered *down*, or that a failed back-end
  server must pass to be considered *up* again.


.. _http-health-monitors:

Configuration arguments for HTTP health monitors
------------------------------------------------

In addition to the arguments listed earlier in :ref:`all-health-monitors`, HTTP
health monitor types *also* require the following arguments, which are set by
default:

* ``url-path``: Path part of the URL that should be retrieved from the back-end
  server. By default this is "/".
* ``http-method``: HTTP method that should be used to retrieve the
  ``url-path``. By default this is "GET".
* ``expected-codes``: List of HTTP status codes that indicate an OK health
  check. By default this is just "200".

For a complete list of configuration arguments for Octavia health monitors, see
the command, `loadbalancer healthmonitor create <https://docs.openstack.org/python-octaviaclient/latest/cli/index.html#loadbalancer-healthmonitor-create>`_.

Please keep the following best practices in mind when writing the code that
generates the health check in your web application:

* The health monitor ``url-path`` should not require authentication to load.
* By default the health monitor ``url-path`` should return a HTTP 200 OK status
  code to indicate a healthy server unless you specify alternate
  ``expected-codes``.
* The health check should do enough internal checks to ensure the application
  is healthy and no more. This may mean ensuring database or other external
  storage connections are up and running, server load is acceptable, the site
  is not in maintenance mode, and other tests specific to your application.
* The page generated by the health check should be very light weight:

  * It should return in a sub-second interval.
  * It should not induce significant load on the application server.

* The page generated by the health check should never be cached, though the
  code running the health check may reference cached data. For example, you may
  find it useful to run a more extensive health check via cron and store the
  results of this to disk. The code generating the page at the health monitor
  ``url-path`` would incorporate the results of this cron job in the tests it
  performs.
* Since Octavia only cares about the HTTP status code returned, and since
  health checks are run so frequently, it may make sense to use the "HEAD" or
  "OPTIONS" HTTP methods to cut down on unnecessary processing of a whole page.


.. _other-health-monitors:

Other health monitors
---------------------
Other health monitor types include ``PING``, ``TCP``, ``HTTPS``, ``SCTP``,
``TLS-HELLO``, and ``UDP-CONNECT``.

``PING`` health monitors send periodic ICMP PING requests to the back-end
servers. Obviously, your back-end servers must be configured to allow PINGs in
order for these health checks to pass.

.. warning::

   Health monitors of type ``PING`` only check if the member is reachable and
   responds to ICMP echo requests. It will not detect if your application
   running on that instance is healthy or not. Most pools should use one of
   the other health monitor options. ``PING`` should only be used in specific
   cases where an ICMP echo request is a valid health check.

``TCP`` health monitors open a TCP connection to the back-end server's protocol
port. Your custom TCP application should be written to respond OK to the load
balancer connecting, opening a TCP connection, and closing it again after the
TCP handshake without sending any data.

``HTTPS`` health monitors operate exactly like HTTP health monitors, but with
ssl back-end servers. Unfortunately, this causes problems if the servers are
performing client certificate validation, as HAProxy won't have a valid cert.
In this case, using ``TLS-HELLO`` type monitoring is an alternative.

``SCTP`` health monitors send an INIT packet to the back-end server's port.
If an application is listening on this port, the Operating System should reply
with an INIT ACK packet, but if the port is closed, it replies with an ABORT
packet.
If the health monitor receives an INIT ACK packet, it immediatly closes the
connection with an ABORT packet, and considers that the server is ONLINE.

``TLS-HELLO`` health monitors simply ensure the back-end server responds to
SSLv3 client hello messages. It will not check any other health metrics, like
status code or body contents.

``UDP-CONNECT`` health monitors do a basic UDP port connect. Health monitors
of this type may not work correctly if Destination Unreachable (ICMP type 3) is
not enabled on the member server or is blocked by a security rule. A member
server may be marked as operating status ONLINE when it is actually down.


Intermediate certificate chains
===============================
Some TLS certificates require you to install an intermediate certificate chain
in order for web client browsers to trust the certificate. This chain can take
several forms, and is a file provided by the organization from whom you
obtained your TLS certificate.

PEM-encoded chains
------------------
The simplest form of the intermediate chain is a PEM-encoded text file that
either contains a sequence of individually-encoded PEM certificates, or a PEM
encoded PKCS7 block(s). If this is the type of intermediate chain you have been
provided, the file will contain either ``-----BEGIN PKCS7-----`` or
``-----BEGIN CERTIFICATE-----`` near the top of the file, and one or more
blocks of 64-character lines of ASCII text (that will look like gobbedlygook to
a human). These files are also typically named with a ``.crt`` or ``.pem``
extension.

DER-encoded chains
------------------
If the intermediates chain provided to you is a file that contains what appears
to be random binary data, it is likely that it is a PKCS7 chain in DER format.
These files also may be named with a ``.p7b`` extension.

You may use the binary DER file as-is when building your PKCS12 bundle:

::

   openssl pkcs12 -export -inkey server.key -in server.crt -certfile ca-chain.p7b -passout pass: -out server.p12

... or you can convert it to a series of PEM-encoded certificates:

::

    openssl pkcs7 -in intermediates-chain.p7b -inform DER -print_certs -out intermediates-chain.crt

... or you can convert it to a PEM-encoded PKCS7 bundle:

::

    openssl pkcs7 -in intermediates-chain.p7b -inform DER -outform PEM -out intermediates-chain.crt


If the file is not a PKCS7 DER bundle, either of the two ``openssl pkcs7``
commands will fail.

Further reading
===============
For examples of using Layer 7 features for more advanced load balancing, please
see: :doc:`l7-cookbook`
