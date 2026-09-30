#!/usr/bin/env python3
"""Probe Vulkan instance creation without Isaac, robot state or control."""
import ctypes as c
import json
import os


class Application(c.Structure):
    _fields_ = [('sType', c.c_uint32), ('pNext', c.c_void_p),
                ('pApplicationName', c.c_char_p), ('applicationVersion', c.c_uint32),
                ('pEngineName', c.c_char_p), ('engineVersion', c.c_uint32),
                ('apiVersion', c.c_uint32)]


class InstanceInfo(c.Structure):
    _fields_ = [('sType', c.c_uint32), ('pNext', c.c_void_p), ('flags', c.c_uint32),
                ('pApplicationInfo', c.POINTER(Application)),
                ('enabledLayerCount', c.c_uint32), ('ppEnabledLayerNames', c.c_void_p),
                ('enabledExtensionCount', c.c_uint32), ('ppEnabledExtensionNames', c.c_void_p)]


def main():
    lib = c.CDLL('libvulkan.so.1')
    lib.vkCreateInstance.argtypes = [c.POINTER(InstanceInfo), c.c_void_p,
                                   c.POINTER(c.c_void_p)]
    lib.vkCreateInstance.restype = c.c_int32
    lib.vkDestroyInstance.argtypes = [c.c_void_p, c.c_void_p]
    app = Application(sType=0, pApplicationName=b'physical-exec-driver-probe',
                      apiVersion=(1 << 22) | (1 << 12))
    info = InstanceInfo(sType=1, pApplicationInfo=c.pointer(app))
    instance = c.c_void_p()
    result = lib.vkCreateInstance(c.byref(info), None, c.byref(instance))
    print(json.dumps({'vkCreateInstance': result,
                      'requested_api': '1.1', 'icd': os.environ.get('VK_ICD_FILENAMES'),
                      'robot_actions': 0, 'isaac_qualified': False}))
    if result == 0:
        lib.vkDestroyInstance(instance, None)
    return 0 if result == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
