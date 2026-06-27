#!/usr/bin/env python3
"""
EP13.2 NPC Dialogue Translation Tool
=====================================
Translates English NPC dialogue in rAthena scripts to Chinese.
Preserves all script structure (coordinates, sprites, logic).
Outputs in GBK encoding as required by RO client.

Design principles (from architecture.md):
  - Structure-preserving: only replace dialogue text in mes/select lines
  - GBK output encoding
  - Backup before modifying
"""

import re
import os
import shutil
from pathlib import Path

RATHENA_NPC = Path(r"D:\Projects\rathena\npc")
BACKUP_DIR = Path(r"D:\Projects\rathena\npc_backup_en")


def backup_file(filepath: Path):
    """Backup original file before modification."""
    rel = filepath.relative_to(RATHENA_NPC)
    backup_path = BACKUP_DIR / rel
    if not backup_path.exists():
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        print(f"  Backed up: {rel}")


def write_gbk(filepath: Path, content: str):
    """Write content in GBK encoding with Unix line endings."""
    encoded = content.encode('gbk', errors='replace')
    # Ensure Unix line endings
    encoded = encoded.replace(b'\r\n', b'\n')
    with open(filepath, 'wb') as f:
        f.write(encoded)


def apply_translation(filepath: Path, translations: dict):
    """
    Apply translations to a file.
    translations: dict mapping line_number (1-based) -> new_line_content
    """
    # Read original file
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    # Try to decode - might be GBK or UTF-8
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        try:
            content = raw.decode('gbk')
        except UnicodeDecodeError:
            content = raw.decode('latin-1')
    
    lines = content.split('\n')
    
    changes = 0
    for line_num, new_content in translations.items():
        idx = line_num - 1  # Convert to 0-based
        if 0 <= idx < len(lines):
            lines[idx] = new_content
            changes += 1
    
    if changes > 0:
        backup_file(filepath)
        result = '\n'.join(lines)
        write_gbk(filepath, result)
        print(f"  Applied {changes} translations to {filepath.relative_to(RATHENA_NPC)}")
    
    return changes


def translate_manuk():
    """Translate manuk.txt - Manuk city NPCs (EP13.2)"""
    filepath = RATHENA_NPC / "cities" / "manuk.txt"
    print(f"\nTranslating: {filepath.relative_to(RATHENA_NPC)}")
    
    translations = {
        # NPC: Food Provider (Soldier#ep13pa829)
        22: '\t\tmes "[食物供应者]";',
        23: '\t\tmes "马努克家族主要依靠提炼很久以前深埋在地下的灰色矿石来维持生计。";',
        27: '\t\tmes "[食物供应者]";',
        28: '\t\tmes "Gdiios duuie Dssoas pogggd fdrul fdddoweet";',
        
        # NPC: Injured Manuk Soldier (Soldier#ep13_2)
        35: '\t\tmes "[受伤的马努克士兵]";',
        36: '\t\tmes "因为受了致命伤，我再也无法吸收布拉迪姆精华了。";',
        37: '\t\tmes "那些邪恶的精灵袭击了我，把我弄成了这样。";',
        39: '\t\tmes "[受伤的马努克士兵]";',
        40: '\t\tmes "我真希望能杀光所有的精灵...";',
        44: '\t\tmes "[受伤的马努克士兵";',
        45: '\t\tmes "Bhiio aaas dgwer fdds rrrrrpppp Ee";',
        47: '\t\tmes "[受伤的马努克士兵]";',
        48: '\t\tmes "Foi dsddff gggeeeerr pqowe";',
        
        # NPC: Anxious Soldier (Soldier#ep13_3)
        55: '\t\tmes "[焦急的士兵]";',
        56: '\t\tmes "快点，我遇到大麻烦了。我把所有的马努克硬币都弄丢了。我想我把它们掉在雪原的某个地方了。天哪，我在睡着之前明明还看到它们的！";',
        60: '\t\tmes "[焦急的士兵]";',
        61: '\t\tmes "Qosi dhhui rffd poaner ouh.";',
        
        # NPC: Piom (ep13_2_hiki)
        69: '\t\tmes "[皮欧姆]";',
        70: '\t\tmes "你...好小啊。但你看起来不像精灵。";',
        71: '\t\tmes "只要你不是该死的精灵，";',
        72: '\t\tmes "那你就不是我们的敌人！";',
        73: '\t\tmes "在这个世界上，只有朋友和敌人！";',
        77: '\t\tmes "[皮欧姆]";',
        78: '\t\tmes "As our wi nueo woud bus";',
        79: '\t\tmes "Gw pii rooop pishe";',
        80: '\t\tmes "Fw iusbn podim bn usow ";',
        81: '\t\tmes "Psbh io whe pasn jd";',
        
        # NPC: Benknee#ep13_2_1
        88: '\t\tmes "[本尼]";',
        89: '\t\tmes "你来这里做什么？";',
        90: '\t\tmes "你是人类吗？";',
        91: '\t\tmes "如果你是人类，你不应该在这里。";',
        93: '\t\tmes "[本尼]";',
        94: '\t\tmes "约顿海姆是一片神圣的土地。";',
        95: '\t\tmes "我们萨法族将用自己的双脚站立。";',
        96: '\t\tmes "并奋起反抗压迫！";',
        100: '\t\tmes "[本尼]";',
        101: '\t\tmes "Bdf sdio hs ioq";',
        102: '\t\tmes "Wfn is ao ps od jd";',
        103: '\t\tmes "No pip dd dow hso le";',
        105: '\t\tmes "[本尼]";',
        106: '\t\tmes "Wsd oup nc xkh d";',
        107: '\t\tmes "Rww o jsd sp";',
        108: '\t\tmes "Yd aihd oa sd s dd";',
        
        # NPC: Piom#ep13_2_1
        115: '\t\tmes "[皮欧姆]";',
        116: '\t\tmes "我们萨法族永远在一起！";',
        117: '\t\tmes "无论我们身在何处，我们始终紧密相连。";',
        118: '\t\tmes "我不知道你从哪里来，但你应该学习我们的精神。";',
        122: '\t\tmes "[皮欧姆]";',
        123: '\t\tmes "Ng go oois yus dd";',
        124: '\t\tmes "You ii iaao nfb ud";',
        125: '\t\tmes "Wqq ifn isp did";',
        126: '\t\tmes "Uy ydf sd fs wee";',
        127: '\t\tmes "Mgg gf fs d ff";',
        
        # NPC: Galtun#ep13_2_1
        134: '\t\tmes "[加尔顿]";',
        135: '\t\tmes "最近，有些小东西一直在周围飞来飞去。";',
        136: '\t\tmes "我不确定它们是不是苍蝇。";',
        137: '\t\tmes "但真的很烦人。";',
        139: '\t\tmes "[加尔顿]";',
        140: '\t\tmes "它们只能从远处使用微弱的魔法。";',
        141: '\t\tmes "但我能很快把它们踢飞。";',
        142: '\t\tmes "它们太烦人了。不过我最好不要在它们身上浪费时间。";',
        146: '\t\tmes "[加尔顿]";',
        147: '\t\tmes "Ya sda sdou sh dbi";',
        148: '\t\tmes "Av bu dgs ldo gp gf ";',
        149: '\t\tmes "Jg gfs dsd fw eerr ";',
        151: '\t\tmes "[加尔顿]";',
        152: '\t\tmes "Mb ih ids oj fd";',
        153: '\t\tmes "Pg sdf dd sd fff";',
        154: '\t\tmes "Bq wer jfsd fsd ut yy";',
        155: '\t\tmes "Nx cxd fsd fs df ";',
        
        # NPC: Galtun#ep13_2_2
        162: '\t\tmes "[加尔顿]";',
        163: '\t\tmes "有了那些成堆的布拉迪姆，我现在可以放松了。";',
        164: '\t\tmes "但我也担心我们会在短时间内用完它们。";',
        168: '\t\tmes "[加尔顿]";',
        169: '\t\tmes "Bu iu bus sfi a sd";',
        170: '\t\tmes "Zsd dwo uf sh osad ";',
        171: '\t\tmes "Qdf aih fas io d hoas";',
        172: '\t\tmes "Nas d iy as di";',
        
        # NPC: Benknee#ep13_2_2
        179: '\t\tmes "[本尼]";',
        180: '\t\tmes "嗯？谁？？你是谁？？";',
        181: '\t\tmes "哦，你不是精灵。";',
        182: '\t\tmes "我还以为你是精灵呢。";',
        183: '\t\tmes "不管怎样，你是谁？你会说话吗？";',
        187: '\t\tmes "[本尼]";',
        188: '\t\tmes "Bao j pj a sd";',
        189: '\t\tmes "Gi oh as d";',
        190: '\t\tmes "Ya sd Yrt sd ad";',
        191: '\t\tmes "Bq we ojj jd";',
        
        # NPC: Piom#ep13_2_2
        198: '\t\tmes "[皮欧姆]";',
        199: '\t\tmes "我永远不会忘记对那些叛徒的深仇大恨。";',
        200: '\t\tmes "我记得我们的祖先是怎么死的。";',
        201: '\t\tmes "我发誓要为他们报仇。";',
        203: '\t\tmes "[皮欧姆]";',
        204: '\t\tmes "首先，我要踢飞那些混蛋。";',
        205: '\t\tmes "那些飞来飞去的小东西太烦我了。";',
        209: '\t\tmes "[皮欧姆]";',
        210: '\t\tmes "Vio hs pf I aps";',
        211: '\t\tmes "Vs ou oas de ee";',
        212: '\t\tmes "Bzi sh da opd";',
        213: '\t\tmes "Mc oju asop dj a ps";',
        215: '\t\tmes "[皮欧姆]";',
        216: '\t\tmes "Be juas da sd";',
        217: '\t\tmes "Eoj ssr owq w e ";',
        218: '\t\tmes "Wps dj i ao sj daasd asd";',
        
        # NPC: Piom#ep13_2_3
        225: '\t\tmes "[皮欧姆]";',
        226: '\t\tmes "我们的生命为萨法族而存在。";',
        227: '\t\tmes "另一方面，";',
        228: '\t\tmes "萨法族的存在也是为了我。";',
        229: '\t\tmes "哈哈哈哈！";',
        231: '\t\tmes "[皮欧姆]";',
        232: '\t\tmes "我们萨法族永远在一起！";',
        233: '\t\tmes "无论我们身在何处！";',
        234: '\t\tmes "为萨法族欢呼！";',
        238: '\t\tmes "[皮欧姆]";',
        239: '\t\tmes "Esd fas hdi as sp ad osd";',
        240: '\t\tmes "Ns id pie sj idf";',
        241: '\t\tmes "Rto osd ps ad ";',
        242: '\t\tmes "Mi sho oo pesd";',
        244: '\t\tmes "[皮欧姆]";',
        245: '\t\tmes "N sd sou as d ";',
        246: '\t\tmes "Ma asd psh ds ii ";',
        247: '\t\tmes "Qso uf lj dhis id";',
        
        # NPC: Galtun#ep13_2_3
        254: '\t\tmes "[加尔顿]";',
        255: '\t\tmes "我将全身心投入";',
        256: '\t\tmes "保护我的家人和萨法族。";',
        257: '\t\tmes "这就是我所希望的一切...";',
        261: '\t\tmes "[加尔顿]";',
        262: '\t\tmes "Mr ishh qw e ee";',
        263: '\t\tmes "Baa eou sh ua sd";',
        264: '\t\tmes "Up idhs ish dk I jsd";',
        
        # NPC: Piom#ep13_2_4
        271: '\t\tmes "[皮欧姆]";',
        272: '\t\tmes "人类，你觉得我们的战斗很愚蠢，对吧？";',
        273: '\t\tmes "觉得是在浪费时间？";',
        274: '\t\tmes "但我们能否生存下去，真的取决于这场战争。";',
        278: '\t\tmes "[皮欧姆]";',
        279: '\t\tmes "Nsa dhi pao sdi a jp das";',
        280: '\t\tmes "Uaa as iijds kn sdg f";',
        281: '\t\tmes "Bzi hd sia pasd ";',
        282: '\t\tmes "Es do ja pda sj d";',
        283: '\t\tmes "Bs oju lujdi ni sdgf g ";',
        285: '\t\tmes "[皮欧姆]";',
        286: '\t\tmes "Us id jd nai dh";',
        
        # NPC: Worker#ep13bsg1
        294: '\t\tmes "[工人]";',
        295: '\t\tmes "如果不每天检查阀门，那是很危险的。";',
        296: '\t\tmes "事实上，以前就发生过事故。";',
        297: '\t\tmes "光是想想就让我毛骨悚然。";',
        301: '\t\tmes "[工人]";',
        302: '\t\tmes "Gs df o aj ud pa";',
        303: '\t\tmes "N sd asw ewt jj ";',
        304: '\t\tmes "Ud aso pda s ";',
        
        # NPC: Worker#ep13bsg2
        311: '\t\tmes "[工人]";',
        312: '\t\tmes "什么！！我...我...我没有睡着！！";',
        313: '\t\tmes "让我们回去工作吧...对，工作...";',
        317: '\t\tmes "[工人]";',
        318: '\t\tmes "Ns ad jai osd";',
        319: '\t\tmes "Rt odj as jo dp as";',
        
        # NPC: Worker#ep13bsg3
        326: '\t\tmes "[工人]";',
        327: '\t\tmes "嗯...运转得很好...完全没有问题...";',
        331: '\t\tmes "[工人]";',
        332: '\t\tmes "Mou ii ros oa d d ";',
        
        # NPC: Worker#ep13bsg4
        339: '\t\tmes "[工人]";',
        340: '\t\tmes "这些天我的视力越来越差了。";',
        344: '\t\tmes "[工人]";',
        345: '\t\tmes "Yw I eus ia d ap s";',
        
        # NPC: Worker#ep13bsg5
        352: '\t\tmes "[工人]";',
        353: '\t\tmes "这不是很棒吗？";',
        357: '\t\tmes "[工人]";',
        358: '\t\tmes "R tt osj dj d";',
        
        # NPC: Worker#ep13bsg6
        365: '\t\tmes "[工人]";',
        366: '\t\tmes "今天有很多优质的布拉迪姆，真是太幸运了。";',
        368: '\t\tmes "[工人]";',
        369: '\t\tmes "这就是我们剩下的全部了。";',
        373: '\t\tmes "[工人]";',
        374: '\t\tmes "Qw eI hs pado as d p ";',
        376: '\t\tmes "[工人]";',
        377: '\t\tmes "Too fn ish d fd";',
        
        # NPC: Manuk Galtun#door1
        385: '\t\tmes "[马努克加尔顿]";',
        386: '\t\tmes "这里是马努克，赫瓦格尔密尔后裔萨法族居住的地方。";',
        390: '\t\tmes "[马努克加尔顿]";',
        391: '\t\tmes "Zd sng pps fsr";',
        
        # NPC: Manuk Galtun#door2
        398: '\t\tmes "[马努克加尔顿]";',
        399: '\t\tmes "这里是马努克，赫瓦格尔密尔后裔萨法族居住的地方。";',
        403: '\t\tmes "[马努克加尔顿]";',
        404: '\t\tmes "To osn dia fg gh gh";',
        
        # NPC: Manuk Piom#tre1
        411: '\t\tmes "[马努克皮欧姆]";',
        412: '\t\tmes "加尔顿是勇敢的萨法战士。";',
        413: '\t\tmes "我是皮欧姆阶级，负责一般劳动。";',
        415: '\t\tmes "[马努克皮欧姆]";',
        416: '\t\tmes "多亏了加尔顿的勇猛，我们才能长期抵御拉斐尼族的侵扰。";',
        417: '\t\tmes "我们一直感激他们的付出。";',
        421: '\t\tmes "[马努克皮欧姆]";',
        422: '\t\tmes "H dn i sid p sd ";',
        423: '\t\tmes "Nd isjd sapd j s id";',
        424: '\t\tmes "Bsi o ps dkm jgf";',
        425: '\t\tmes "Eo oo ptr n sid";',
        
        # NPC: Manuk Piom#tre2
        432: '\t\tmes "[马努克皮欧姆]";',
        433: '\t\tmes "我的腿...";',
        434: '\t\tmes "已经到时间了。";',
        438: '\t\tmes "[马努克皮欧姆]";',
        439: '\t\tmes "Fn is d id ";',
        440: '\t\tmes "Yon sdi dh so dps";',
        
        # NPC: Manuk Galtun#tre3
        447: '\t\tmes "[马努克加尔顿]";',
        448: '\t\tmes "欢迎来到马努克。";',
        449: '\t\tmes "有什么可以帮你的吗？";',
        
        # NPC: Manuk Piom#tre4
        457: '\t\tmes "[马努克皮欧姆]";',
        458: '\t\tmes "嘿，小心点！";',
        459: '\t\tmes "这种矿物是布拉迪姆，是我们部族的命脉。";',
        460: '\t\tmes "如果你不小心处理这些石头，你会有麻烦的！";',
        464: '\t\tmes "[马努克皮欧姆]";',
        465: '\t\tmes "Bmm ish di sd";',
        466: '\t\tmes "Fii sd ani s a d s k ds ";',
        467: '\t\tmes "Ti h is so so pd";',
        
        # NPC: Manuk Benknee#tre5
        474: '\t\tmes "[马努克本尼]";',
        475: '\t\tmes "你看到那座雕像了吗？";',
        476: '\t\tmes "他就是赫瓦格尔密尔，对我们萨法族来说如同传说一般的存在。";',
        477: '\t\tmes "他是一个真正威严而勇敢的人。";',
        481: '\t\tmes "[马努克皮欧姆]";',
        482: '\t\tmes "Ys oadj oa s d";',
        483: '\t\tmes "Bni ii osd jo as das";',
        484: '\t\tmes "Qa oj df isd oo o";',
        
        # NPC: Young Villager#ep13bs
        492: '\t\tmes "[年轻村民]";',
        493: '\t\tmes "约会时间都过了，她怎么还没来！！？";',
        497: '\t\tmes "[Asd]";',
        498: '\t\tmes "Ywo di pi butfs oui Afbsu ";',
        
        # NPC: Mechanic#ep13bs
        505: '\t\tmes "[技师]";',
        506: '\t\tmes "外族不允许进入。";',
        507: '\t\tmes "这里非常危险，请不要再靠近了。";',
        511: '\t\tmes "[Asoui]";',
        512: '\t\tmes "Fs iua sdjosow ww ";',
        513: '\t\tmes "Adds wwpq iusnd ";',
        
        # NPC: Worker#ep13bs1
        520: '\t\tmes "[工人]";',
        521: '\t\tmes "嗯，闻起来真香。";',
        522: '\t\tmes "现在应该是翻面的时候了。";',
        524: '\t\tmes "[工人]";',
        525: '\t\tmes "硬石猛犸象牛排应该吃半生的！";',
        529: '\t\tmes "[Tee]";',
        530: '\t\tmes "As woue dpi sha we";',
        531: '\t\tmes "Two psie bu le";',
        533: '\t\tmes "[Tee]";',
        534: '\t\tmes "Tr sdou powee wwee ";',
        
        # NPC: Worker#ep13bs2
        541: '\t\tmes "[工人]";',
        542: '\t\tmes "大厨，我应该放多少个盘子？";',
        546: '\t\tmes "[Tee]";',
        547: '\t\tmes "We pishd bugs ouwwe iro ";',
        
        # NPC: Scientist#ep13bs
        554: '\t\tmes "[科学家]";',
        555: '\t\tmes "难道我们只有一条生存之路吗..？";',
        559: '\t\tmes "[Apti]";',
        560: '\t\tmes "Dso piey pioit ioep ";',
    }
    
    return apply_translation(filepath, translations)


def translate_splendide():
    """Translate splendide.txt - Splendide city NPCs (EP13.2)"""
    filepath = RATHENA_NPC / "cities" / "splendide.txt"
    print(f"\nTranslating: {filepath.relative_to(RATHENA_NPC)}")
    
    # Read the file first to understand structure
    with open(filepath, 'rb') as f:
        raw = f.read()
    try:
        content = raw.decode('utf-8')
    except UnicodeDecodeError:
        content = raw.decode('gbk', errors='replace')
    
    lines = content.split('\n')
    translations = {}
    
    # Process each line - translate mes and select lines
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # Translate NPC name headers in mes
        if stripped.startswith('mes "') and stripped.endswith('";'):
            inner = stripped[5:-2]  # content between mes " and ";
            
            # NPC name headers like [Name]
            if inner.startswith('[') and inner.endswith(']'):
                name = inner[1:-1]
                cn_name = translate_npc_name_splendide(name)
                if cn_name != name:
                    indent = line[:len(line) - len(line.lstrip())]
                    translations[line_num] = f'{indent}mes "[{cn_name}]";'
            # Regular dialogue
            elif inner and not inner.startswith('^') and not inner.startswith('+'):
                cn_text = translate_dialogue_splendide(inner, i, lines)
                if cn_text and cn_text != inner:
                    indent = line[:len(line) - len(line.lstrip())]
                    translations[line_num] = f'{indent}mes "{cn_text}";'
    
    return apply_translation(filepath, translations)


def translate_npc_name_splendide(name):
    """Translate Splendide NPC names."""
    name_map = {
        "Laphine Guard": "拉斐尼守卫",
        "Laphine Soldier": "拉斐尼士兵",
        "Laphine": "拉斐尼族人",
        "Laphine Craftsman": "拉斐尼工匠",
        "Laphine Elder": "拉斐尼长老",
        "Laphine Merchant": "拉斐尼商人",
        "Laphine Child": "拉斐尼小孩",
        "Laphine Villager": "拉斐尼村民",
        "Laphine Warrior": "拉斐尼战士",
        "Guard": "守卫",
        "Soldier": "士兵",
        "Elder": "长老",
        "Merchant": "商人",
        "Villager": "村民",
        "Child": "小孩",
    }
    return name_map.get(name, name)


def translate_dialogue_splendide(text, line_idx, all_lines):
    """Placeholder - will be filled with actual translations."""
    return text  # Will be replaced by actual translation data


if __name__ == "__main__":
    import sys
    
    total = 0
    
    print("=" * 60)
    print("EP13.2 NPC Dialogue Translation")
    print("=" * 60)
    
    # Start with smaller files
    total += translate_manuk()
    
    print(f"\n{'=' * 60}")
    print(f"Total translations applied: {total}")
    print("=" * 60)
