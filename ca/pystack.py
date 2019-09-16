#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 中文字編碼
import os,sys

reload(sys)
sys.setdefaultencoding('utf8')
os.environ["NLS_LANG"] = 'AMERICAN_AMERICA.UTF8'

class Node(object):
    def __init__(self, element=None, next=None):
        self.element = element
        self.next = next

class Stack(object):
    def __init__(self):
        self.stack_pointer = None

    def push(self, element):
        self.stack_pointer = Node(element, self.stack_pointer)

    def pop(self):
        e = self.stack_pointer.element
        self.stack_pointer = self.stack_pointer.next
        return e

    def peek(self):
        return self.stack_pointer.element

    def clear(self):
        sp = self.stack_pointer
        while sp:
            rm = sp
            sp = sp.next
            del rm

    def __len__(self):
        i = 0
        sp = self.stack_pointer
        while sp:
            i += 1
            sp = sp.next
        return i
