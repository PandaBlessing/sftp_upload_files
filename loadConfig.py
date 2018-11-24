#!/usr/bin/python
# coding:utf-8

import json


def load_json():
    with open('config.json', encoding='utf-8') as f:
        setting = json.load(f)
        return setting
