# import sys
# import trace
# import threading
# import time
#
#
# class thread_with_trace(threading.Thread):
#     def __init__(self, *args, **keywords):
#         threading.Thread.__init__(self, *args, **keywords)
#         self.killed = False
#
#     def start(self):
#         self.__run_backup = self.run
#         self.run = self.__run
#         threading.Thread.start(self)
#
#     def __run(self):
#         sys.settrace(self.globaltrace)
#         self.__run_backup()
#         self.run = self.__run_backup
#
#     def globaltrace(self, frame, event, arg):
#         if event == 'call':
#             return self.localtrace
#         else:
#             return None
#
#     def localtrace(self, frame, event, arg):
#         if self.killed:
#             if event == 'line':
#                 raise SystemExit()
#         return self.localtrace
#
#     def kill(self):
#         self.killed = True
#
#
# def func():
#     while True:
#         print('thread running')
#
#
# t1 = thread_with_trace(target=func)
# t1.start()
# time.sleep(2)
# t1.kill()
# t1.join()
# if not t1.isAlive():
#     print('thread killed')
#

#!/usr/bin/env python
# encoding: utf-8

import sys

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    func_line_no = frame.f_lineno
    func_filename = co.co_filename
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    print ( 'Call to %s on line %s of %s from line %s of %s' % \
        (func_name, func_line_no, func_filename,
         caller_line_no, caller_filename))
    return

def b():
    print ('in b()')

def a():
    print ('in a()')
    b()

sys.settrace(trace_calls)
a()
