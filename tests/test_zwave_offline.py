# Offline tests of real firmware Python 2.7 bytecode with fake serial/controller.
import unittest
from zwave.telldus.DeviceNode import DeviceNode
from zwave.base.Node import Node
from zwave.base.Controller import Controller
from telldus import Device

class FakeNode(object):
    generic = Node.GENERIC_TYPE_SWITCH_BINARY
    def __init__(self): self.sent=[]
    def supportCommandClass(self,*a,**k): return False
    def sendMsg(self,*a,**k): self.sent.append((a,k))

class ZWaveOffline(unittest.TestCase):
    def test_real_device_command_mapping(self):
        node=FakeNode()
        device=DeviceNode.__new__(DeviceNode)
        device.node=node
        for action in (Device.TURNON,Device.TURNOFF,Device.UP):
            device._command(action,None,lambda **kw:None,lambda *a:None)
            self.assertEqual(len(node.sent),1)
            node.sent[:]=[]
    def test_real_controller_inclusion_queue(self):
        controller=Controller.__new__(Controller)
        captured=[]
        controller.nodeId=1
        controller.secureInclusion=False
        controller.query=lambda message:captured.append(message)
        controller.isPrimary=lambda:False
        controller.includedSecure=lambda:True
        controller.addNodeToNetwork(193,secure=True)
        self.assertTrue(controller.secureInclusion)
        self.assertEqual(len(captured),1)
        controller.removeNodeFromNetwork(1)
        self.assertEqual(len(captured),2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
