import fancontrol
import micropython

micropython.alloc_emergency_exception_buf(100)

F = fancontrol.Controller("192.168.1.240")
F.start_fancontrol()
