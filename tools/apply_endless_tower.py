#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Endless Tower NPC Chinese Translation Script
Translates all English NPC dialogue in EndlessTower.txt to Chinese.
Outputs GBK-encoded file with backup of original.
"""

import os
import shutil

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_FILE = os.path.join(BASE_DIR, "npc", "instances", "EndlessTower.txt")
BACKUP_DIR = os.path.join(BASE_DIR, "npc_backup_en", "instances")
BACKUP_FILE = os.path.join(BACKUP_DIR, "EndlessTower.txt")

# ============================================================
# Translation dictionary: line_number (1-based) -> new line content
# All indentation is preserved exactly as original.
# ============================================================
translations = {
    # --- Captain Janssen dialogue (alberta NPC) ---
    43:  '\t\tmes "^008800\xd4\xda\xd5\xe2\xc0\xef\xb5\xc8\xd2\xbb\xb5\xc8\xa3\xa1\xa3\xa1";',
    44:  '\t\tmes "\xc4\xe3\xb4\xf8\xc1\xcb\xcc\xab\xb6\xe0\xb6\xab\xce\xf7\xc1\xcb\xa1\xa3\xce\xaa\xca\xb2\xc3\xb4\xb2\xbb\xb0\xd1\xd2\xbb\xd0\xa9\xb6\xab\xce\xf7\xb7\xc5\xcf\xc2\xa3\xac\xc8\xbb\xba\xf3\xd4\xd9\xbb\xd8\xc0\xb4\xa1\xa3^000000";',
    48:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    49:  '\t\tmes "\xcc\xbe\xc6\xf8... \xce\xd2\xb2\xbb\xd6\xaa\xb5\xc0\xce\xd2\xca\xc7\xb7\xf1\xbb\xb9\xc4\xdc\xbb\xd8\xb5\xbd\xba\xa3\xc9\xcf\xba\xbd\xd0\xd0...";',
    54:  '\t\tmes "^0000ff\xc0\xcf\xc8\xcb\xbf\xb4\xc6\xf0\xc0\xb4\xbc\xab\xc6\xe4\xd0\xcb\xb7\xdc\xa3\xac\xb4\xd2\xb4\xd2\xc5\xdc\xbd\xf8\xba\xa3\xd1\xf3\xc9\xcc\xb5\xea\xb6\xa9\xb9\xba\xce\xef\xd7\xca\xa1\xa3\xc4\xe3\xc3\xbb\xca\xb2\xc3\xb4\xca\xc2\xd7\xf6\xa3\xac\xbe\xf6\xb6\xa8\xce\xca\xce\xca\xcb\xfb\xce\xaa\xca\xb2\xc3\xb4\xd5\xe2\xc3\xb4\xd7\xc5\xbc\xb1\xa1\xa3^000000";',
    56:  '\t\tmes "^0000ff\xc0\xcf\xc8\xcb\xcd\xea\xb3\xc9\xb6\xa9\xb5\xa5\xba\xf3\xa3\xac\xcf\xf2\xc4\xe3\xd7\xdf\xc0\xb4\xa1\xa3^000000";',
    58:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    59:  '\t\tmes "\xc4\xe3\xd5\xe2\xc3\xb4\xc7\xe1\xd2\xd7\xbe\xcd\xbd\xd3\xca\xdc\xc1\xcb\xce\xd2\xd5\xe2\xb8\xf6\xc4\xb0\xc9\xfa\xc8\xcb\xb5\xc4\xc7\xeb\xc7\xf3\xa3\xac\xce\xd2\xba\xdc\xb8\xd0\xb6\xaf\xa1\xa3\xc4\xe3\xd2\xbb\xb6\xa8\xca\xc7\xc4\xc7\xd0\xa9\xc9\xc6\xc1\xbc\xb5\xc4\xa1\xa2\xd3\xa2\xd3\xc2\xb5\xc4\xc3\xb0\xcf\xd5\xd5\xdf\xd6\xae\xd2\xbb\xa1\xa3\xc4\xe3\xd3\xd0\xd0\xcb\xc8\xa4\xb3\xf6\xba\xa3\xc2\xc3\xd0\xd0\xc2\xf0\xa3\xbf";',
    62:  '\t\tmes "\xce\xd2\xba\xbd\xd0\xd0\xb9\xfd\xbc\xb8\xb4\xce... \xb5\xab\xcf\xd6\xd4\xda\xcf\xeb\xcf\xeb\xa3\xac\xce\xd2\xb4\xd3\xc0\xb4\xc3\xbb\xd3\xd0\xba\xe1\xb9\xfd\xb4\xf3\xc2\xbd\xa1\xa3";',
    64:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    65:  '\t\tmes "\xb2\xbb\xa3\xac\xd5\xe2\xbe\xcd\xb9\xbb\xc1\xcb\xa1\xa3\xce\xd2\xbf\xc9\xc4\xdc\xd6\xbb\xd3\xd0\xd2\xbb\xcb\xd2\xd0\xa1\xd3\xe6\xb4\xac\xa3\xac\xb5\xab\xce\xd2\xd4\xf8\xbe\xad\xca\xc7\xd6\xb8\xbb\xd3\xd2\xbb\xd6\xa7\xbd\xa2\xb6\xd3\xb5\xc4\xb4\xac\xb3\xa4\xa1\xa3";',
    67:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    68:  '\t\tmes "\xc8\xe7\xb9\xfb\xc4\xe3\xba\xbd\xd0\xd0\xb9\xfd\xbc\xb8\xb4\xce\xbe\xcd\xbb\xe1\xd6\xaa\xb5\xc0\xa3\xac\xc3\xbb\xd3\xd0\xb6\xe0\xc9\xd9\xc8\xcb\xba\xe1\xb9\xfd\xb4\xf3\xc2\xbd\xd2\xd4\xcd\xe2\xb5\xc4\xba\xa3\xd1\xf3\xa1\xa3\xce\xd2\xd2\xb2\xc3\xbb\xd3\xd0\xd5\xf7\xb7\xfe\xba\xa3\xd1\xf3\xa1\xa3";',
    70:  '\t\tmes "^0000ff\xd1\xee\xc9\xad\xcf\xc8\xc9\xfa\xbd\xb2\xc1\xcb\xba\xdc\xbe\xc3\xcb\xfb\xbe\xaa\xcf\xd5\xb5\xc4\xba\xa3\xc9\xcf\xc2\xc3\xd0\xd0\xa1\xa3\xc4\xe3\xd3\xd0\xb5\xc4\xca\xc7\xca\xb1\xbc\xe4\xa3\xac\xd3\xda\xca\xc7\xd7\xf8\xcf\xc2\xc0\xb4\xa3\xac\xbe\xb2\xbe\xb2\xb5\xd8\xcc\xfd\xcb\xfb\xb5\xc4\xb9\xca\xca\xc2\xa1\xa3^000000";',
    72:  '\t\tmes "^0000ff\xcb\xfb\xb5\xc4\xb9\xca\xca\xc2\xd6\xc1\xc9\xd9\xd3\xd0\xd2\xbb\xb0\xeb\xcc\xfd\xc6\xf0\xc0\xb4\xd1\xcf\xd6\xd8\xbf\xe4\xb4\xf3\xa3\xac\xb5\xab\xd3\xd0\xd2\xbb\xbc\xfe\xca\xc2\xd2\xfd\xc6\xf0\xc1\xcb\xc4\xe3\xb5\xc4\xd7\xa2\xd2\xe2\xa3\xba\xcb\xfb\xbc\xe1\xb3\xc6\xba\xa3\xc9\xcf\xb4\xe6\xd4\xda\xd2\xbb\xd7\xf9\xbe\xde\xb4\xf3\xb5\xc4\xcb\xfe\xa3\xac\xb8\xdf\xb5\xc3\xb2\xc1\xb9\xfd\xcc\xec\xbf\xd5\xa1\xa3^000000";',
    76:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    77:  '\t\tmes "\xcb\xf9\xd2\xd4\xce\xd2\xc3\xc7\xd6\xbb\xc4\xdc\xd4\xda\xbd\xa2\xb6\xd3\xb1\xbb\xb4\xdd\xbb\xd9\xba\xf3\xa3\xac\xd4\xda\xc4\xc7\xd7\xf9\xbe\xde\xb4\xf3\xb5\xc4\xcb\xfe\xc5\xd4\xc5\xd7\xc3\xab\xa1\xa3\xd2\xbb\xbf\xaa\xca\xbc\xa3\xac\xce\xd2\xc3\xc7\xd6\xbb\xca\xc7\xb4\xf2\xcb\xe3\xb4\xfd\xb5\xbd\xb1\xa9\xb7\xe7\xd3\xea\xb9\xfd\xc8\xa5\xa3\xac\xb5\xab\xcb\xfc\xb2\xa2\xc3\xbb\xd3\xd0\xcf\xf1\xce\xd2\xc3\xc7\xcf\xa3\xcd\xfb\xb5\xc4\xc4\xc7\xd1\xf9\xbe\xa1\xbf\xec\xbd\xe1\xca\xf8\xa1\xa3";',
    79:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    80:  '\t\tmes "\xce\xd2\xb5\xc4\xb4\xac\xd4\xb1\xc3\xc7\xb6\xbc\xb6\xf6\xc1\xcb\xa3\xac\xc6\xe4\xd6\xd0\xbc\xb8\xb8\xf6\xc8\xcb\xd7\xdf\xbd\xf8\xc1\xcb\xcb\xfe\xc0\xef\xc8\xa5\xd5\xd2\xca\xb3\xce\xef... \xcb\xfb\xc3\xc7\xd4\xd9\xd2\xb2\xc3\xbb\xd3\xd0\xbb\xd8\xc0\xb4\xa1\xa3";',
    83:  '\t\tmes "\xc4\xe3\xce\xaa\xca\xb2\xc3\xb4\xb2\xbb\xba\xcd\xcb\xfb\xc3\xc7\xd2\xbb\xc6\xf0\xbd\xf8\xc8\xa5\xa3\xbf";',
    85:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    86:  '\t\tmes "\xce\xd2\xb5\xc4\xb1\xbe\xc4\xdc\xb8\xe6\xcb\xdf\xce\xd2\xc4\xc7\xd7\xf9\xcb\xfe\xba\xdc\xce\xa3\xcf\xd5\xa1\xa3\xce\xd2\xba\xdc\xba\xc3\xc6\xe6\xa3\xac\xb5\xab\xce\xd2\xb2\xbb\xbb\xe1\xc3\xb0\xc9\xfa\xc3\xfc\xce\xa3\xcf\xd5\xa1\xa3\xce\xd2\xc3\xc7\xb5\xc8\xc1\xcb\xcb\xfb\xc3\xc7\x37\xcc\xec\xa3\xac\xd6\xb1\xb5\xbd\xb1\xa9\xb7\xe7\xd3\xea\xd6\xd5\xd3\xda\xb9\xfd\xc8\xa5\xa3\xac\xb5\xab\xc3\xbb\xd3\xd0\xc8\xcb\xbb\xd8\xc0\xb4\xa1\xa3";',
    88:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    89:  '\t\tmes "\xce\xaa\xc1\xcb\xc9\xfa\xb4\xe6\xa3\xac\xce\xd2\xc3\xc7\xc5\xd7\xc6\xfa\xc1\xcb\xcb\xf9\xd3\xd0\xbb\xf5\xce\xef\xa3\xac\xd6\xbb\xb4\xf8\xd7\xc5\xd4\xda\xcb\xfe\xd6\xdc\xce\xa7\xd5\xd2\xb5\xbd\xb5\xc4\xd2\xbb\xb5\xe3\xcb\xae\xba\xcd\xbf\xc9\xca\xb3\xd3\xc3\xb5\xc4\xd6\xb2\xce\xef\xc0\xeb\xbf\xaa\xc1\xcb\xcb\xfe\xa1\xa3\xb5\xb1\xce\xd2\xc3\xc7\xd6\xd5\xd3\xda\xb5\xbd\xb4\xef\xc2\xbd\xb5\xd8\xca\xb1\xa3\xac\xd6\xbb\xd3\xd0\xce\xd2\xd2\xbb\xb8\xf6\xc8\xcb\xbb\xee\xd7\xc5...";',
    91:  '\t\tmes "^0000ff\xc4\xe3\xbf\xc9\xd2\xd4\xcf\xeb\xcf\xf3\xb5\xbd\xb4\xb9\xcb\xc0\xb5\xc4\xbd\xa2\xb6\xd3\xd4\xda\xd7\xee\xba\xf3\xd2\xbb\xb4\xce\xba\xbd\xd0\xd0\xd6\xd0\xb5\xc4\xb1\xaf\xb2\xd2\xb3\xa1\xbe\xb0\xa3\xac\xbc\xb4\xca\xb9\xcb\xfb\xb2\xbb\xd4\xd9\xb6\xe0\xcb\xb5\xa1\xa3\xd2\xbb\xc1\xb3\xb1\xaf\xc9\xcb\xb5\xc4\xba\xf3\xbb\xda\xc9\xa8\xb9\xfd\xcb\xfb\xb5\xc4\xc1\xb3\xc5\xd3\xa3\xac\xcb\xfb\xb3\xc1\xc4\xac\xc1\xcb\xd2\xbb\xbb\xe1\xb6\xf9\xa3\xac\xc8\xbb\xba\xf3\xcb\xb5\xa3\xba^000000";',
    93:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    94:  '\t\tmes "\xd4\xda\xce\xd2\xcb\xc0\xd6\xae\xc7\xb0\xa3\xac\xce\xd2\xd3\xd0\xd2\xbb\xbc\xfe\xca\xc2\xb1\xd8\xd0\xeb\xd7\xf6\xa1\xa3\xce\xd2\xb1\xd8\xd0\xeb\xc8\xa1\xbb\xd8\xcb\xc0\xd4\xda\xcb\xfe\xc0\xef\xb5\xc4\xb4\xac\xd4\xb1\xb5\xc4\xd2\xc5\xba\xa1\xa3\xac\xb8\xf8\xcb\xfb\xc3\xc7\xd2\xbb\xb8\xf6\xcc\xe5\xc3\xe6\xb5\xc4\xb0\xb2\xd4\xe1\xa1\xa3";',
    96:  '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    97:  '\t\tmes "\xc4\xdc\xd3\xf6\xb5\xbd\xc4\xe3\xd5\xe2\xd1\xf9\xc8\xc8\xd0\xc4\xb5\xc4\xc3\xb0\xcf\xd5\xd5\xdf\xa3\xac\xce\xd2\xbe\xf5\xb5\xc3\xba\xdc\xd0\xd2\xd4\xcb\xa1\xa3\xd3\xd0\xc1\xcb\xc4\xe3\xb8\xf8\xce\xd2\xb5\xc4\xc7\xae\xa3\xac\xce\xd2\xd6\xd5\xd3\xda\xbf\xc9\xd2\xd4\xd4\xd9\xb4\xce\xba\xbd\xd0\xd0\xb5\xbd\xc4\xc7\xd7\xf9\xcb\xfe\xc1\xcb\xa1\xa3";',
    100: '\t\tmes "\xb9\xcd\xd3\xb6\xce\xd2\xb5\xb1\xc4\xe3\xb5\xc4\xb4\xf3\xb8\xb1\xd4\xf5\xc3\xb4\xd1\xf9\xa3\xbf";',
    102: '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    103: '\t\tmes "\xd0\xbb\xd0\xbb\xc4\xe3\xa3\xac\xb5\xab\xc4\xc7\xca\xc7\xd2\xbb\xb8\xf6\xbc\xab\xc6\xe4\xce\xa3\xcf\xd5\xb5\xc4\xb5\xd8\xb7\xbd\xa1\xa3\xce\xd2\xd3\xd0\xce\xd2\xb5\xc4\xd4\xf0\xc8\xce\xd2\xaa\xc2\xc4\xd0\xd0\xa3\xac\xb5\xab\xc4\xe3\xb6\xd4\xce\xd2\xbb\xf2\xcb\xfb\xc3\xc7\xc3\xbb\xd3\xd0\xc8\xce\xba\xce\xd2\xe5\xce\xf1\xa1\xa3\xce\xd2\xb2\xbb\xcf\xa3\xcd\xfb\xc8\xc3\xc4\xe3\xd5\xe2\xd1\xf9\xc4\xea\xc7\xe1\xb5\xc4\xc8\xcb\xce\xfe\xc9\xfc\xd4\xda\xd5\xe2\xd1\xf9\xce\xa3\xcf\xd5\xb5\xc4\xb5\xd8\xb7\xbd\xa1\xa3";',
    106: '\t\tmes "\xb2\xbb...";',
    107: '\t\tmes ".";',
    108: '\t\tmes ".";',
    109: '\t\tmes "\xd7\xf7\xce\xaa\xc3\xb0\xcf\xd5\xd5\xdf\xa3\xac\xb0\xef\xd6\xfa\xd3\xd0\xd0\xe8\xd2\xaa\xb5\xc4\xc8\xcb\xca\xc7\xce\xd2\xb5\xc4\xd4\xf0\xc8\xce\xa1\xa3\xce\xd2\xd2\xb2\xb6\xd4\xc4\xc7\xb8\xf6\xb5\xd8\xb7\xbd\xba\xdc\xba\xc3\xc6\xe6...";',
    111: '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    112: '\t\tmes "\xce\xd2\xb1\xbe\xc0\xb4\xb4\xf2\xcb\xe3\xc1\xa2\xbf\xcc\xb3\xf6\xb7\xa2\xa3\xac\xb5\xab\xbc\xc8\xc8\xbb\xc4\xe3\xbc\xd3\xc8\xeb\xc1\xcb\xa3\xac\xce\xd2\xd3\xa6\xb8\xc3\xb8\xf8\xc4\xe3\xca\xb1\xbc\xe4\xd7\xbc\xb1\xb8\xa1\xa3\xce\xd2\xbb\xe1\xd4\xda\xd5\xe2\xc0\xef\xb5\xc8\xc4\xe3\xd7\xbc\xb1\xb8\xba\xc3\xa1\xa3";',
    114: '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    115: '\t\tmes "...\xba\xc3\xb0\xc9...";',
    116: '\t\tmes "\xbb\xb6\xd3\xad\xc9\xcf\xb4\xac\xa3\xac\xb4\xf3\xb8\xb1\xa1\xa3";',
    120: '\t\tmes "[\xd1\xee\xc9\xad\xb4\xac\xb3\xa4]";',
    121: '\t\tmes "\xce\xd2\xc3\xc7\xcf\xd6\xd4\xda\xb3\xf6\xb7\xa2\xc2\xf0\xa3\xbf";',
}

# I'll build the translations dict using actual Chinese strings encoded to GBK bytes,
# but since the file needs to be written as text with GBK encoding, let me use
# a cleaner approach with actual Unicode strings.

# Clear the byte-based approach and use Unicode strings directly
translations = {}

def t(line_num, content):
    """Register a translation for a given line number."""
    translations[line_num] = content

# ============================================================
# Captain Janssen NPC - alberta (lines 41-203)
# ============================================================

# Line 43-44: Too much stuff warning
t(43, '\t\tmes "^008800在这里等一等！！";')
t(44, '\t\tmes "你带了太多东西了。为什么不把一些东西放下，然后再回来。^000000";')

# Line 48-49: Low level dialogue
t(48, '\t\tmes "[扬森船长]";')
t(49, '\t\tmes "唉... 我不知道我是否还能回到海上航行...";')

# Line 54: Narrative - old man rushing
t(54, '\t\tmes "^0000ff老人看起来极其兴奋，匆匆跑进海洋商店订购物资。你没什么事做，决定问问他为什么这么着急。^000000";')

# Line 56: Narrative - old man walks towards you
t(56, '\t\tmes "^0000ff老人完成订单后，向你走来。^000000";')

# Line 58-59: Janssen touched by your help
t(58, '\t\tmes "[扬森船长]";')
t(59, '\t\tmes "你这么轻易就接受了我这个陌生人的请求，我很感动。你一定是那些善良的、英勇的冒险者之一。你有兴趣出海旅行吗？";')

# Line 61: Player name line - keep as-is (has variable)
# Line 62: Player dialogue
t(62, '\t\tmes "我航行过几次... 但现在想想，我从来没有横过大陆。";')

# Line 64-65: Janssen about his fleet
t(64, '\t\tmes "[扬森船长]";')
t(65, '\t\tmes "不，这就够了。我可能只有一艘小渔船，但我曾经是指挥一支舰队的船长。";')

# Line 67-68: About ocean voyages
t(67, '\t\tmes "[扬森船长]";')
t(68, '\t\tmes "如果你航行过几次就会知道，没有多少人横过大陆以外的海洋。我也没有征服海洋。";')

# Line 70: Narrative - Janssen talked about journeys
t(70, '\t\tmes "^0000ff扬森先生讲了很久他惊险的海上旅行。你有的是时间，于是坐下来，静静地听他的故事。^000000";')

# Line 72: Narrative - tower on the ocean
t(72, '\t\tmes "^0000ff他的故事至少有一半听起来严重夸大，但有一件事引起了你的注意：他坚称海上存在一座巨大的塔，高得擦过天空。^000000";')

# Line 76-77: Anchored at the tower
t(76, '\t\tmes "[扬森船长]";')
t(77, '\t\tmes "所以我们只能在舰队被摧毁后，在那座巨大的塔旁抛锚。一开始，我们只是打算待到暴风雨过去，但它并没有像我们希望的那样尽快结束。";')

# Line 79-80: Crew starving
t(79, '\t\tmes "[扬森船长]";')
t(80, '\t\tmes "我的船员们都饿了，其中几个人走进了塔里去找食物... 他们再也没有回来。";')

# Line 82: Player name line - keep as-is
# Line 83: Player asks why
t(83, '\t\tmes "你为什么不和他们一起进去？";')

# Line 85-86: Instincts told him
t(85, '\t\tmes "[扬森船长]";')
t(86, '\t\tmes "我的本能告诉我那座塔很危险。我很好奇，但我不会冒生命危险。我们等了他们7天，直到暴风雨终于过去，但没有人回来。";')

# Line 88-89: Desperate to survive
t(88, '\t\tmes "[扬森船长]";')
t(89, '\t\tmes "为了生存，我们抛弃了所有货物，只带着在塔周围找到的一点水和可食用的植物离开了塔。当我们终于到达陆地时，只有我一个人活着...";')

# Line 91: Narrative - heartwrenching scene
t(91, '\t\tmes "^0000ff你可以想象到垂死的舰队在最后一次航行中的悲惨场景，即使他不再多说。一脸悲伤的后悔扫过他的脸庞，他沉默了一会儿，然后说：^000000";')

# Line 93-94: Must retrieve remains
t(93, '\t\tmes "[扬森船长]";')
t(94, '\t\tmes "在我死之前，我有一件事必须做。我必须取回死在塔里的船员的遗骸，给他们一个体面的安葬。";')

# Line 96-97: Lucky to meet you
t(96, '\t\tmes "[扬森船长]";')
t(97, '\t\tmes "能遇到你这样热心的冒险者，我觉得很幸运。有了你给我的钱，我终于可以再次航行到那座塔了。";')

# Line 99: Player name line - keep as-is
# Line 100: Player offers to be first mate
t(100, '\t\tmes "雇佣我当你的大副怎么样？";')

# Line 102-103: Janssen warns of danger
t(102, '\t\tmes "[扬森船长]";')
t(103, '\t\tmes "谢谢你，但那是一个极其危险的地方。我有我的责任要履行，但你对我或他们没有任何义务。我不希望让你这样年轻的人牺牲在这样危险的地方。";')

# Line 105: Player name line - keep as-is
# Line 106-109: Player insists
t(106, '\t\tmes "不...";')
t(107, '\t\tmes ".";')
t(108, '\t\tmes ".";')
t(109, '\t\tmes "作为冒险者，帮助有需要的人是我的责任。我也对那个地方很好奇...";')

# Line 111-112: Janssen gives time to prepare
t(111, '\t\tmes "[扬森船长]";')
t(112, '\t\tmes "我本来打算立刻出发，但既然你加入了，我应该给你时间准备。我会在这里等你准备好。";')

# Line 114-116: Welcome aboard
t(114, '\t\tmes "[扬森船长]";')
t(115, '\t\tmes "...好吧...";')
t(116, '\t\tmes "欢迎上船，大副。";')

# Line 120-121: Shall we leave?
t(120, '\t\tmes "[扬森船长]";')
t(121, '\t\tmes "我们现在出发吗？";')

# Line 123: select options
t(123, '\t\tswitch(select("是的，出发吧！:不，我还没准备好...")) {')

# Line 125-126: Pull up anchor
t(125, '\t\t\tmes "[扬森船长]";')
t(126, '\t\t\tmes "那就起锚吧，大副！";')

# Line 132-133: Come back when ready
t(132, '\t\t\tmes "[扬森船长]";')
t(133, '\t\t\tmes "好的，没问题。准备好了再回来。";')

# Line 137-138: Restock goods
t(137, '\t\tmes "[扬森船长]";')
t(138, '\t\tmes "嗯，要再次出海，我们需要补充物资。如果你给我10,000金币，剩下的我来处理。";')

# Line 140: select options
t(140, '\t\tswitch(select("我以后再来。:出发吧，现在！")) {')

# Line 142-143: Don't have money
t(142, '\t\t\tmes "["+.@name$+"]";')
t(143, '\t\t\tmes "对不起，我没有那么多钱。等我攒够了再回来。";')

# Line 145-146: Janssen will wait
t(145, '\t\t\tmes "[扬森船长]";')
t(146, '\t\t\tmes "好的，没问题。我会等你回来的。";')

# Line 150-151: Not enough money
t(150, '\t\t\t\tmes "[扬森船长]";')
t(151, '\t\t\t\tmes "对不起，你没有足够的钱。我至少需要10,000金币来补充我们的物资...";')

# Line 155-156: Excellent, let's go
t(155, '\t\t\t\tmes "[扬森船长]";')
t(156, '\t\t\t\tmes "太好了！现在我们可以出发了。再次起锚吧！";')

# Line 164-165: Are you an adventurer?
t(164, '\t\tmes "[扬森船长]";')
t(165, '\t\tmes "请问，你是冒险者吗？";')

# Line 167-168: Sorry to ask
t(167, '\t\tmes "[扬森船长]";')
t(168, '\t\tmes "很抱歉这样问你，尤其是我们第一次见面，但你能帮我一个忙吗？我长话短说。";')

# Line 170-171: Donate 10000 Zeny
t(170, '\t\tmes "[扬森船长]";')
t(171, '\t\tmes "你能捐^0000ff10,000金币^000000给我吗？这是为了一件对我很重要的事...";')

# Line 173: select options
t(173, '\t\tswitch(select("不行！:当然可以。")) {')

# Line 175-176: Wrong person
t(175, '\t\t\tmes "["+.@name$+"]";')
t(176, '\t\t\tmes "对不起，你找错人了。";')

# Line 178-179: Sorry to bother
t(178, '\t\t\tmes "[扬森船长]";')
t(179, '\t\tmes "我明白了... 抱歉打扰你。我理解一开始就提这样的要求太冒昧了。";')

# Line 182-183: Are you sure?
t(182, '\t\t\tmes "[扬森船长]";')
t(183, '\t\t\tmes "啊？你确定不介意给我那么多钱吗？哇，太感谢了！";')

# Line 186-187: Don't have 10000
t(186, '\t\t\t\tmes "[扬森船长]";')
t(187, '\t\t\t\tmes "...对不起，我觉得你没有10,000金币。谢谢你的好意，但我需要更多。";')

# Line 190-191: Player gives money
t(190, '\t\t\t\tmes "["+.@name$+"]";')
t(191, '\t\t\t\tmes "我不知道你为什么需要这么多钱，但给你吧。你拿去。";')

# Line 193: Donated narrative
t(193, '\t\t\t\tmes "^0000ff你向扬森船长捐赠了10,000金币^000000。";')

# Line 195-196: Thank you so much
t(195, '\t\t\t\tmes "[扬森船长]";')
t(196, '\t\t\t\tmes "太感谢了！现在我可以储备食物和船的材料了。你真善良，非常善良！";')

# ============================================================
# Tower Protection Stone (lines 205-319)
# ============================================================

t(214, '\t\tmes "组建或加入一个超过1人的队伍后再试。";')

t(220, '\t\t\tmes "已确认队伍已组建。你想预约进入无尽之塔吗？";')

t(222, '\t\t\tswitch(select("生成地下城"+.@md_name$+":进入地下城:返回艾尔贝塔:取消")) {')

t(225, '\t\t\t\t\tmes "队伍名称: "+ getpartyname(.@party_id);')
t(226, '\t\t\t\t\tmes "队伍队长: "+strcharinfo(0);')
t(227, '\t\t\t\t\tmes "^0000ff"+.@md_name$+" ^000000- 预约失败！";')

t(230, '\t\t\t\tmes "^0000ff"+.@md_name$+"^000000 - 尝试预约";')
t(231, '\t\t\t\tmes "预约成功后，你需要与后面的NPC对话并选择\'进入地下城\'菜单来进入地下城。";')

t(236, '\t\t\t\tmes "我将把你传送到艾尔贝塔。";')

t(244, '\t\tswitch(select("进入"+.@md_name$+":返回艾尔贝塔:取消")) {')

t(248, '\t\t\tmes "我将把你传送到艾尔贝塔。";')

t(258, '\t\t\tmes "如果你已经生成了地下城，你可以进入。";')

t(260, '\t\t\tswitch(select("进入"+.@md_name$+":返回艾尔贝塔:取消")) {')

t(264, '\t\t\t\tmes "我将把你传送到艾尔贝塔。";')

t(280, '\t\t\tmes "由于塔的后遗效应，你现在无法进入地下城，距离下次进入还剩 " + .@dun_h + "小时 " + .@dun_m + "分钟 " + .@dun_s + "秒。";')

t(282, '\t\t\tmes "这里很危险。让我把你传送到艾尔贝塔。";')

t(291, '\t\tmes "^0000ff与无尽之塔相关的记录和后遗效应已被清除。你可以重新生成并进入无尽之塔。^000000";')

# L_Enter subroutine
t(298, '\t\tmes "发生了未知错误。";')

t(301, '\t\tmes "纪念地下城无尽之塔不存在。";')
t(302, '\t\tmes "队伍队长尚未生成地下城。";')

t(305, '\t\tmes "组建队伍后才能进入地下城。";')

# ============================================================
# Huge Vortex (line 324)
# ============================================================
t(324, '\tmapannounce "e_tower","[ " + strcharinfo(0) + " ]，似乎被一个巨大的漩涡吞噬了",bc_map,"0x00ff99",FW_NORMAL,12;')

# ============================================================
# Administrator Mode (lines 330-354)
# ============================================================
t(332, '\tmes "请输入密码";')

t(336, '\t\tswitch(select("生成净化石:移除净化石:取消")) {')

t(338, '\t\t\tmes "创建持续30分钟的净化石。";')

t(341, '\t\t\tmes "立即销毁净化石";')

t(344, '\t\t\tmes "你已取消。";')

t(351, '\t\tmes "请准确输入密码。";')

# ============================================================
# Purification Stone#et1 (line 358)
# ============================================================
t(358, '\tmes "^0000ff与无尽之塔相关的记录和后遗效应已被清除。你可以重新生成并进入无尽之塔。^000000";')

t(379, '\tmapannounce "e_tower", "净化石将在一分钟后被销毁。",bc_map,"0x00ff99";')

# ============================================================
# Purification Stone#et2 (line 390)
# ============================================================
t(390, '\tmes "^0000ff与无尽之塔相关的记录和后遗效应已被清除。你可以重新生成并进入无尽之塔。^000000";')

# ============================================================
# Immortal Brazier (lines 1191-1218)
# ============================================================
t(1192, '\tmes "- 火盆上刻着一段文字 -";')
t(1193, '\tmes "在此处撒下黑暗之灰的人，将离黑暗霸王纳特·西格更近一步...";')

t(1196, '\tsetarray .@level$[1],"第26层","第51层","第76层";')

t(1198, '\tset .@i, select("第26层:第51层:第76层");')

t(1201, '\t\tmes "-警告-";')
t(1202, '\t\tmes "要传送到"+.@level$[.@i]+"，你需要"+.@i+"个黑暗之灰。";')

t(1215, '\tmapannounce instance_mapname("1@tower"), "注意：驯服怪物不计入击败数。",bc_map,"0xff0000";')

# ============================================================
# Floor Controllers - mapannounce messages
# ============================================================
t(1237, '\t\tmapannounce .@map$, "第1层剩余怪物数 - "+.@mob_dead_num,bc_map,"0x00ff99";')
t(1241, '\tmapannounce instance_mapname("1@tower"), "第1层所有怪物已被击败。",bc_map,"0xffff00";')

# Generic floor controller (1FGate102tower template)
t(1276, '\t\tmapannounce .@map$, "第"+callfunc("F_GetNumSuffix",.@level)+"层剩余怪物数 - "+.@mob_dead_num,bc_map,"0x00ff99";')
t(1281, '\tmapannounce strnpcinfo(4), "第"+callfunc("F_GetNumSuffix",.@level)+"层所有怪物已被击败。",bc_map,"0xffff00";')

# Broadcast Mode1
t(1359, '\tmapannounce instance_mapname("1@tower"), "注意：在任何异常情况下击败怪物，你将无法进入下一层！",bc_map,"0xff0000";')
t(1362, '\tmapannounce instance_mapname("1@tower"), "注意：在任何异常情况下击败怪物，你将无法进入下一层！",bc_map,"0xff0000";')

# Manager Mode1
t(1369, '\tmes "请输入密码。";')
t(1373, '\t\tmes "此NPC管理第1层到第25层的塔。";')
t(1374, '\t\tmes "请输入要开放的层数。";')
t(1375, '\t\tmes "(例如：1F->1, 25F->25)";')
t(1379, '\t\t\tmes "你只能输入1到25之间的数字。";')
t(1382, '\t\t\tmes "*** 第 "+ .@input + " 层正在开放。 ***";')

# Levels 26-50 section
t(1408, '\t\tmapannounce .@map$, "第26层剩余怪物数 - " + .@mob_dead_num,bc_map,"0x00ff99";')
t(1412, '\tmapannounce instance_mapname("2@tower"), "第26层所有怪物已被击败。",bc_map,"0xffff00";')

# Manager Mode2
t(1485, '\tmes "请输入密码。";')
t(1489, '\t\tmes "此NPC管理第26层到第50层的塔。";')
t(1490, '\t\tmes "请输入要开放的层数。";')
t(1491, '\t\tmes "(例如：26F->26, 50F->50)";')
t(1495, '\t\t\tmes "你只能输入26到50之间的数字。";')
t(1498, '\t\t\tmes "*** 第 "+ .@input + " 层正在开放。 ***";')

# Levels 51-75 section
t(1524, '\t\tmapannounce .@map$, "第51层剩余怪物数 - " + .@mob_dead_num,bc_map,"0x00ff99";')
t(1528, '\tmapannounce instance_mapname("3@tower"), "第51层所有怪物已被击败。",bc_map,"0xffff00";')

# Manager Mode3
t(1601, '\tmes "请输入密码。";')
t(1605, '\t\tmes "此NPC管理第51层到第75层的塔。";')
t(1606, '\t\tmes "请输入要开放的层数。";')
t(1607, '\t\tmes "(例如：51F->51, 75F->75)";')
t(1611, '\t\t\tmes "你只能输入51到75之间的数字。";')
t(1614, '\t\t\tmes "*** 第 "+ .@input + " 层正在开放。 ***";')

# Levels 76-99 section
t(1640, '\t\tmapannounce .@map$,"第76层剩余怪物数 - " + .@mob_dead_num,bc_map,"0x00ff99";')
t(1644, '\tmapannounce instance_mapname("4@tower"),"第76层所有怪物已被击败。",bc_map,"0xffff00";')

# Manager Mode4
t(1716, '\tmes "请输入密码。";')
t(1720, '\t\tmes "此NPC管理第76层到第99层的塔。";')
t(1721, '\t\tmes "请输入要开放的层数。";')
t(1722, '\t\tmes "(例如：76F->76, 99F->99)";')
t(1726, '\t\t\tmes "你只能输入76到99之间的数字。";')
t(1729, '\t\t\tmes "*** 第 "+ .@input + " 层正在开放。 ***";')

# ============================================================
# Level 100 - Lucid Crystal#102 (lines 1737-1787)
# ============================================================
t(1739, '\t\tmes "^0000ff当你触碰散发着强光的透明水晶时，一个神秘的声音在房间里回荡。^000000";')

t(1741, '\t\tmes "[神秘的声音]";')
t(1742, '\t\tmes "欢迎来到我的领地，入侵者们。看着你们忍受我设下的所有困难，我很开心。";')

t(1744, '\t\tmes "[神秘的声音]";')
t(1745, '\t\tmes "不幸的是，是时候结束这场表演了。";')

t(1747, '\t\tmes "[神秘的声音]";')
t(1748, '\t\tmes "现在庆祝你们战胜我的左膀右臂诺森还为时过早，因为他还没有被完全消灭！";')

t(1750, '\t\tmes "[神秘的声音]";')
t(1751, '\t\tmes "我将为你们的下一场表演复活他。再次击败他，然后我将欣然接受你们的挑战。";')

t(1753, '\t\tmes "[神秘的声音]";')
t(1754, '\t\tmes "暂时告别了。";')
t(1755, '\t\tmes "再一次，我度过了非常愉快的时光，人类们。期待再次见到你们。";')

t(1757, '\t\tmes "^0000ff声音停止说话后，一股不可抗拒的力量将你举起并传送到了别处。";')

# else branch (in_102tower >= 10)
t(1763, '\t\tmes "^0000ff散发光芒的水晶碎片似乎在召唤你，就像上次一样。^000000";')

t(1765, '\t\tmes "[神秘的声音]";')
t(1766, '\t\tmes "我一定是低估了你们... 我没想到会再次见到你们。";')

t(1768, '\t\tmes "[神秘的声音]";')
t(1769, '\t\tmes "我能闻到你们的汗水，听到你们在战斗中疲惫的喘息。啊~ 人类对胜利的渴望总是让我兴奋。";')

t(1771, '\t\tmes "[神秘的声音]";')
t(1772, '\t\tmes "我现在允许你们来觐见我。来吧，来见黑暗霸王纳特·西格！";')

# ============================================================
# Level 100 - Shadow Dust announcements
# ============================================================
t(1847, '\t\tmapannounce .@map$, "神秘的声音：你们是谁，竟敢闯入我的圣殿？！",bc_map,"0xffff00";')

# ============================================================
# Manager Mode5 (lines 1906-1917)
# ============================================================
t(1908, '\tmes "此NPC管理第100层的水晶。请输入密码。";')
t(1913, '\t\tmes "第100层的水晶已被激活。";')
t(1915, '\t\tmes "请输入正确的密码。";')

# ============================================================
# Level 101 - Life Spring (line 1922)
# ============================================================
t(1922, '\tmes "^0066ff你喝了一口泉水的清水，感觉精力充沛。^000000";')

# ============================================================
# Level 101 - Beeper announcements (Naght Sieger dialogue)
# ============================================================
# 1st Beeper
t(1985, '\tmapannounce instance_mapname("6@tower"),"客人，嗯？我希望你们来这里时已经知道你们将被埋葬在这个地方。如果你们不知道，嗯... 太迟了！",bc_map,"0x00ffcc";')
t(1989, '\tmapannounce instance_mapname("6@tower"),"这就是为什么你们冒险者总是死路一条。",bc_map,"0x00ffcc";')
t(1993, '\tmapannounce instance_mapname("6@tower"),"我可以为你们的勇气鼓掌... 当然，我打算先和你们玩一会儿。",bc_map,"0x00ffcc";')
t(1997, '\tmapannounce instance_mapname("6@tower"),"你知道吗，我喜欢看人类在恐惧中四处奔跑。",bc_map,"0x00ffcc";')
t(2002, '\tmapannounce .@map$,"让我们看看谁跑得最快。你们准备好了吗？",bc_map,"0x00ffcc";')

t(2016, '\t\tmapannounce .@map$,"剩余目标 " + .@mob_dead_num + "个",bc_map,"0x00ff99";')

# 2nd Beeper
t(2028, '\tmapannounce instance_mapname("6@tower"),"嗯，我猜它们对你们来说不算太有挑战性。",bc_map,"0x00ffcc";')
t(2032, '\tmapannounce instance_mapname("6@tower"),"让我们加快一点速度，好吗？",bc_map,"0x00ffcc";')
t(2037, '\tmapannounce .@map$,"我要求返场！",bc_map,"0x00ffcc";')

t(2051, '\t\tmapannounce .@map$,"剩余目标 " + .@mob_dead_num + "个",bc_map,"0x00ff99";')

# 3rd Beeper
t(2063, '\tmapannounce instance_mapname("6@tower"),"是的，这越来越刺激了！",bc_map,"0x00ffcc";')
t(2067, '\tmapannounce instance_mapname("6@tower"),"我会记住你们是少数几个能让我开心的人之一。",bc_map,"0x00ffcc";')
t(2072, '\tmapannounce .@map$,"你们想再来一轮吗？",bc_map,"0x00ffcc";')

t(2086, '\t\tmapannounce .@map$,"剩余目标 " + .@mob_dead_num + "个",bc_map,"0x00ff99";')

# 4th Beeper
t(2098, '\tmapannounce instance_mapname("6@tower"),"好了，是时候让我登场了！",bc_map,"0x00ffcc";')
t(2102, '\tmapannounce instance_mapname("6@tower"),"你们想知道我是谁吗？",bc_map,"0x00ffcc";')
t(2107, '\tmapannounce .@map$,"你们很快就会知道。我的面孔就是死亡！",bc_map,"0x00ffcc";')

# ============================================================
# Lost Soul#102 (lines 2117-2195)
# ============================================================
t(2119, '\t\tmes "你带了太多东西了。为什么不把一些东西放下，然后再回来？";')

t(2122, '\tmes "[迷失的灵魂]";')
t(2123, '\tmes "是你们将我们从邪恶的纳特·西格手中解放出来。";')

t(2125, '\tmes "[迷失的灵魂]";')
t(2126, '\tmes "太感谢了。现在我们可以从这个寒冷黑暗的地方逃出去了... 去天堂。";')

t(2129, '\t\tmes "[迷失的灵魂]";')
t(2130, '\t\tmes "嘿，你身上有纳特·西格的残骸。";')

t(2132, '\t\tmes "[迷失的灵魂]";')
t(2133, '\t\tmes "它们看起来像单手剑，但如果你愿意的话，我可以把它们合在一起做成一把双手剑。这是我唯一能报答你解放我的方式。";')

t(2135, '\t\tswitch(select("制作双手剑。:不用了，谢谢。")) {')

t(2137, '\t\t\tmes "[迷失的灵魂]";')
t(2138, '\t\t\tmes "如果已经升级过或者插了卡片，那些效果将会消失。你确定吗？";')

t(2140, '\t\t\tswitch(select("没关系。请制作吧。:不行！")) {')

t(2142, '\t\t\t\tmes "[迷失的灵魂]";')
t(2143, '\t\t\t\tmes "好的，那我就把这些合在一起制作双手剑。";')

t(2149, '\t\t\t\tmes "[迷失的灵魂]";')
t(2150, '\t\t\t\tmes "我明白了。我猜你不像那些其他冒险者那样贪婪或有野心。";')

t(2157, '\t\t\tmes "[迷失的灵魂]";')
t(2158, '\t\t\tmes "我明白了。我猜你不像那些其他冒险者那样贪婪或有野心。";')

t(2163, '\tmes "[迷失的灵魂]";')
t(2164, '\tmes "我想和你多聊聊，但我... 我得走了。";')

t(2166, '\tmes "[迷失的灵魂]";')
t(2167, '\tmes "再见了，年轻的冒险者。祝你好运。";')

# ============================================================
# Post-defeat announcements (Lost Soul timer events)
# ============================================================
t(2184, '\tmapannounce instance_mapname("6@tower"),"这... 这不可能！我不可能被打败！",bc_map,"0xffff00";')
t(2188, '\tmapannounce instance_mapname("6@tower"),"不！！我的灵魂... 我的躯壳...！不~！",bc_map,"0xffff00";')
t(2192, '\tmapannounce instance_mapname("6@tower"),"纳特·西格的身体化为黑暗之灰，随风飘散。",bc_map,"0x00ffcc";')


def main():
    print("=" * 60)
    print("Endless Tower Chinese Translation Script")
    print("=" * 60)

    # Check source file exists
    if not os.path.isfile(SOURCE_FILE):
        print(f"ERROR: Source file not found: {SOURCE_FILE}")
        return

    # Step 1: Read the original file
    print(f"\n[1] Reading source file: {SOURCE_FILE}")
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"    Read {len(lines)} lines.")

    # Step 2: Create backup
    print(f"\n[2] Creating backup: {BACKUP_FILE}")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(SOURCE_FILE, BACKUP_FILE)
    print(f"    Backup created successfully.")

    # Step 3: Apply translations
    print(f"\n[3] Applying {len(translations)} translations...")
    applied = 0
    for line_num, new_content in sorted(translations.items()):
        idx = line_num - 1  # Convert to 0-based index
        if idx < 0 or idx >= len(lines):
            print(f"    WARNING: Line {line_num} out of range (file has {len(lines)} lines)")
            continue
        # Replace the line, preserving the newline
        lines[idx] = new_content + "\n"
        applied += 1

    print(f"    Applied {applied} translations.")

    # Step 4: Write the translated file in GBK encoding
    print(f"\n[4] Writing translated file in GBK encoding: {SOURCE_FILE}")
    with open(SOURCE_FILE, "w", encoding="gbk") as f:
        f.writelines(lines)
    print(f"    File written successfully.")

    print(f"\n{'=' * 60}")
    print(f"Translation complete!")
    print(f"  - Lines translated: {applied}")
    print(f"  - Backup location:  {BACKUP_FILE}")
    print(f"  - Output encoding:  GBK")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
