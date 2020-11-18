# What is this script about? #

- This script is to demonstrate the ability of advertising a BGP route from YaBGP to perform simple Traffic Engineering.
- The script leverages sFlow traffic flows to find the Top Talker a.k.a TopFlow.
- Once the TopFlow is found, the script prompsts the user to enter an alternative segment-list for the TopFlow so the traffic gets 'engineered'

# How to run the demo? #

 - inputs.yaml - Update this file with the right inputs as per your lab infrastructure.
 - install sflow_rt on your VM. This lab_vm IP is what is specified as "sflow_rt_ip" in the inputs.yaml file.

# Resources #

- sFlow RT: https://sflow-rt.com/
- YaBGP : https://github.com/smartbgp/yabgp

# Example : Execution of the Script #

In my current setup, I am learning 5 unique prefixes from a remote BGP peer. Each prefix is associated with a BGP Ext community value.
For example, 182.1.5.0/24 prefix has a color value of 500:

```
PE1-ghb265#show ip bgp 182.1.5.0/24
BGP routing table information for VRF default
Router identifier 10.2.2.7, local AS number 65001
BGP routing table entry for 182.1.5.0/24
 Paths: 2 available
  65003
    10.0.0.5 from 10.0.0.5 (12.12.12.12)
      Origin IGP, metric 0, localpref 100, IGP metric 40, weight 0, tag 0
      Received 02:45:16 ago, valid, internal, best
      Extended Community: Color:CO(00):500
      Rx SAFI: Unicast
      Tunnel RIB eligible
  65003
    20.2.1.2 from 7.1.1.5 (12.12.12.12)
      Origin IGP, metric 0, localpref 100, IGP metric -, weight 0, tag 0
      Received 02:45:16 ago, invalid, internal
      Extended Community: Color:CO(00):500
      Rx SAFI: Unicast
PE1-ghb265#
```

PE1 will be using the SR tunnel to send traffic to these destinations:


```
PE1-ghb265#show ip route | grep 182 -A 2
 B I      182.1.1.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.2.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.3.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.4.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.5.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13

```

Running the script:

```
sureshk@sureshk srte-demo % python yabgp-adv-policy.py

Congestion Event Detected: Linerate on Et5/1 > 85 percent
....

Identifying the top-flow...
....

The top flow is destined to the prefix 182.1.1.0 and has color 100
Enter the alternate segment list for top-talker (provide spaces between labels): '960003 960004 960002 960005'
sureshk@sureshk srte-demo %
```

Turns out, the TopFlow in my example is destined to 182.1.1.0/24 prefix. This prefix has a color of 100. So my script prompted me for a new segment list and programmed it on PE1 via BGP-SRTE.


New Entry on the Arista Router:
```
PE1-ghb265#show bgp sr-te detail
BGP routing table information for VRF default
Router identifier 10.2.2.7, local AS number 65001
BGP routing table entry for Endpoint: 10.0.0.5, Color: 100, Distinguisher: 1002
 Paths: 1 available
  65000
    10.10.51.1 from 172.20.48.143 (172.17.0.3)
      Origin IGP, metric -, localpref 100, weight 0, received 00:02:24 ago, valid, external, best
      Community: no-advertise
      Rx SAFI: SR TE Policy
      Tunnel encapsulation attribute: SR Policy
         Preference: 100
         Binding SID: 991105
         Segment List: Label Stack: [960003 960004 960002 960005], Weight: 1
PE1-ghb265#
```
```
PE1-ghb265#show ip route | grep 182 -A 2
 B I      182.1.1.0/24 [200/0] via SR-TE Policy 10.0.0.5, color 100
                               via SR-TE tunnel index 9, weight 1
                                  via 10.10.51.1, Port-Channel901, label 960003 960004 960002 960005
 B I      182.1.2.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.3.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.4.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
 B I      182.1.5.0/24 [200/0] via 10.0.0.5/32, IS-IS SR tunnel index 13
                                  via 10.10.51.1, Port-Channel901, label 960005
```
