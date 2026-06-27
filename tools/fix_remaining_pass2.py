#!/usr/bin/env python3
"""Fix remaining untranslated lines in merchant.txt (second pass)."""
import sys, os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'merchant.txt')
    
    with open(filepath, 'rb') as f:
        data = f.read()
    text = data.decode('gbk', errors='replace')
    
    # Fix all remaining " [Union Staff Kay] " -> "[工会职员凯]"
    text = text.replace('mes " [Union Staff Kay] ";', 'mes "[工会职员凯]";')
    
    # Fix second occurrence of "Hello there," (line 115)
    # and second "+ strcharinfo(0) +"." (line 116)
    # These are in the passed-test path
    text = text.replace('mes "Hello there,";', 'mes "你好，";')
    text = text.replace('mes ""+ strcharinfo(0) +".";', 'mes ""+ strcharinfo(0) +"。";')
    
    # Fix the getarg line that wasn't caught (line 491)
    text = text.replace('mes "^3355FF"+getarg(2)+"^000000.";', 'mes "^3355FF"+getarg(2)+"^000000。";')
    
    # Fix duplicate lines in F_MercKafra (Byalan Kafra) that are same as Prontera Kafra
    # These are repeated patterns that need multiple=True style replacement
    # Since we already replaced the first occurrence, the remaining ones are in the F_MercKafra function
    
    # We need to handle these carefully - let's do line-by-line for the remaining ones
    lines = text.split('\n')
    
    # Simple replacements for lines that appear multiple times
    simple_replacements = {
        'mes "That\'s right.";': 'mes "没错。";',
        'mes "Here\'s your";': 'mes "这是你的";',
        'mes "receipt.";': 'mes "收据。";',
        'mes "The Serial Number";': 'mes "序列号";',
        'mes "the one we ordered. Oh,";': 'mes "我们订的。哦，";',
        'mes "and don\'t forget this receipt!";': 'mes "别忘了这张收据！";',
        'mes "A delivery from";': 'mes "来自";',
        'mes "the Merchant Guild?";': 'mes "商人公会的快递？";',
        'mes "Oh, yes, please set";': 'mes "哦，好的，请把它";',
        'mes "it down right over there...";': 'mes "放在那边...";',
        'mes "You must be really tired";': 'mes "你一定很累了";',
        'mes "after carrying it for so long!";': 'mes "搬了这么久！";',
        'mes "W-wait. Didn\'t you bring it?";': 'mes "等-等等。你没带来吗？";',
        'mes "Where\'s the package?";': 'mes "包裹在哪里？";',
        'mes "Now, let me check";': 'mes "现在，让我检查一下";',
        'mes "the serial number...";': 'mes "序列号...";',
        'mes "the wrong package. What we";': 'mes "错误的包裹。我们";',
        'mes "Thanks again";': 'mes "再次感谢你";',
        'mes "for going through";': 'mes "经历了";',
        'mes "all of that trouble~";': 'mes "这些麻烦~";',
    }
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        for old, new in simple_replacements.items():
            if stripped == old:
                lines[i] = line.replace(old, new)
                break
    
    result = '\n'.join(lines)
    
    with open(filepath, 'wb') as f:
        f.write(result.encode('gbk', errors='replace'))
    
    print("Second pass fixes applied to merchant.txt")


if __name__ == '__main__':
    main()
