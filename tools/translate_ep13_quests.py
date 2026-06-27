#!/usr/bin/env python3
"""
EP13.2 核心任务链 NPC 对话翻译工具
将 rAthena NPC 脚本中的英文对话翻译为中文（GBK编码输出）

设计原则：
- 保留文件结构（坐标、精灵ID、脚本逻辑）
- 仅替换 mes "..." 和 select("...") 中的对话文本
- 输出 GBK 编码
- 翻译风格：仙境传说官方中文风格
"""

import re
import os
import shutil

# ============================================================
# EP13.2 核心任务链翻译字典
# 按文件组织，每个文件的翻译按出现顺序排列
# ============================================================

# NPC 名称翻译（用于 mes "[NPC名]" 中的名称）
NPC_NAMES = {
    "William": "威廉",
    "Alchemist": "炼金术士",
    "Metz": "梅兹",
    "Soldier": "士兵",
    "Continental Guard": "大陆护卫",
    "Continental Official": "大陆官员",
    "Recruiter": "招募员",
    "Guard": "守卫",
    "Morocc Soldier": "摩洛哥士兵",
    "Morocc Guard": "摩洛哥守卫",
    "Cat Paw Agent": "猫爪商会代理",
    "Cat Paw Merchant": "猫爪商会商人",
    "Gyaruk": "加鲁克",
    "Laphine": "拉菲内",
    "Sapha": "萨法",
    "Splendide Soldier": "斯普兰蒂德士兵",
    "Dispatched Sapha": "派遣萨法",
    "Expedition Guide": "远征向导",
    "Allied Forces Soldier": "联合军士兵",
    "Logistics Manager": "后勤管理员",
    "Sundries Merchant": "杂货商人",
    "Party Leader": "队长",
    "Merchant Prince": "商人王子",
    "Curious Knight": "好奇的骑士",
    "Confused Thief": "困惑的盗贼",
    "Adventurous Rafflesia": "冒险的大花草",
    "Historian Shep": "历史学家谢普",
    "Nidhoggr": "尼德霍格",
    "Himmelmez": "希梅尔梅兹",
    "Bijou": "碧珠",
    "Eremes": "艾勒梅斯",
    "Seyren": "塞连",
    "Margaretha": "玛格丽塔",
    "Cecil": "塞西尔",
    "Kathryne": "凯瑟琳",
    "Howard": "霍华德",
    "Flamel": "弗拉梅尔",
    "Gertie": "格蒂",
    "Hibba Agip": "希巴·阿吉普",
    "Egnigem Cansen": "艾格尼姆·坎森",
    "Wickebine Tres": "维克拜因·特雷斯",
    "Armeyer Dinze": "阿梅耶·丁泽",
    "Errende Ebecee": "艾伦德·艾贝西",
    "Laurell Weinder": "劳雷尔·温德",
    "Kavach Icarus": "卡瓦奇·伊卡洛斯",
    "Rawrel": "拉乌雷尔",
    "Bazett": "巴泽特",
    "Taab": "塔布",
    "Rayan Moore": "拉扬·摩尔",
    "Diego": "迪亚哥",
    "Laur": "劳尔",
    "Loki": "洛基",
    "Iris": "艾丽丝",
    "Niren": "尼伦",
    "Mokep": "莫凯普",
    "Ahat": "阿哈特",
    "Ahman": "阿曼",
    "Gaebolg": "盖博尔格",
    "Echinacea": "紫锥花",
    "Dandelion": "蒲公英",
    "Valkyrie": "女武神",
    "Freyja": "芙蕾雅",
    "Odin": "奥丁",
    "Satan Morocc": "魔王莫洛克",
    "Morocc": "莫洛克",
    "Morroc": "摩洛哥",
    "Prontera": "普隆德拉",
    "Geffen": "吉芬",
    "Payon": "斐扬",
    "Alberta": "阿尔贝塔",
    "Izlude": "伊斯鲁德",
    "Aldebaran": "阿尔德巴兰",
    "Lighthalzen": "利希塔尔岑",
    "Juno": "朱诺",
    "Hugel": "胡格尔",
    "Rachel": "拉赫",
    "Veins": "维因斯",
    "Midgard": "米德加尔特",
    "Splendide": "斯普兰蒂德",
    "Manuk": "马努克",
    "Yggdrasil": "世界树",
    "Bifrost": "彩虹桥",
    "Ash Vacuum": "灰烬真空",
    "Dimensional Gorge": "次元峡谷",
    "Dimensional Gap": "次元裂缝",
    "New World": "新世界",
    "Alfheim": "精灵界",
    "Nidavellir": "侏儒界",
    "Midgard Allied Forces Post": "米德加尔特联合军驻地",
    "Midgard Camp": "米德加尔特营地",
}


def translate_file(input_path, translations_func):
    """
    翻译单个NPC脚本文件
    
    Args:
        input_path: 输入文件路径
        translations_func: 返回翻译字典的函数，接收文件内容作为参数
    """
    # 读取原文件
    with open(input_path, 'rb') as f:
        data = f.read()
    
    # 尝试 GBK 解码（之前的工具可能已经部分翻译为GBK）
    try:
        text = data.decode('gbk')
    except:
        text = data.decode('utf-8', errors='replace')
    
    lines = text.split('\n')
    translations = translations_func(text)
    
    translated_count = 0
    result_lines = []
    
    for line in lines:
        new_line = line
        
        # 翻译 mes "..." 行
        mes_match = re.match(r'^(\s*mes\s+)"(.*)"(\s*;?\s*)$', line)
        if mes_match:
            prefix = mes_match.group(1)
            content = mes_match.group(2)
            suffix = mes_match.group(3)
            
            # 检查是否是 NPC 名称行 [Name]
            name_match = re.match(r'^\[(.+)\]$', content)
            if name_match:
                npc_name = name_match.group(1)
                if npc_name in NPC_NAMES:
                    new_content = f"[{NPC_NAMES[npc_name]}]"
                    new_line = f'{prefix}"{new_content}"{suffix}'
                    translated_count += 1
            elif content in translations:
                new_line = f'{prefix}"{translations[content]}"{suffix}'
                translated_count += 1
        
        # 翻译 select("...") 行
        select_match = re.search(r'select\("([^"]+)"\)', line)
        if select_match:
            select_content = select_match.group(1)
            if select_content in translations:
                new_line = line.replace(f'select("{select_content}")', f'select("{translations[select_content]}")')
                translated_count += 1
        
        # 翻译 switch(select("...")) 行
        switch_select_match = re.search(r'switch\(select\("([^"]+)"\)\)', line)
        if switch_select_match:
            select_content = switch_select_match.group(1)
            if select_content in translations:
                new_line = line.replace(f'select("{select_content}")', f'select("{translations[select_content]}")')
                translated_count += 1
        
        result_lines.append(new_line)
    
    # 备份原文件
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(input_path)), 'npc_backup_en')
    rel_path = os.path.relpath(input_path, os.path.join(os.path.dirname(os.path.dirname(input_path)), 'npc'))
    backup_path = os.path.join(backup_dir, rel_path)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    if not os.path.exists(backup_path):
        shutil.copy2(input_path, backup_path)
    
    # 写入 GBK 编码
    output = '\n'.join(result_lines)
    with open(input_path, 'wb') as f:
        f.write(output.encode('gbk', errors='replace'))
    
    return translated_count


if __name__ == '__main__':
    print("EP13.2 核心任务链翻译工具")
    print("请使用 translate_ep13_core.py 进行实际翻译")
