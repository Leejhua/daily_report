#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书机器人权限测试工具
用于诊断230013错误的具体原因
"""

import json
import os
import requests
from typing import Dict, Any, Optional

class FeishuPermissionTester:
    def __init__(self):
        self.app_id = os.getenv('FEISHU_APP_ID', 'cli_a827d9eb278b101c')
        self.app_secret = os.getenv('FEISHU_APP_SECRET', 'U2kstRSDlTkWpa6FKUEIUdHM0LfGLxQk')
        self.access_token = None