#!/usr/bin/env python3
"""
Fix remaining untranslated lines in pre-re 1-1 job change scripts.
These are lines that were missed in the initial translation pass,
including dynamic strings with strcharinfo(0), countitem(), getarg(), etc.

Approach: exact old->new line replacement (full line match).
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def fix_file(filepath, replacements):
    """Replace exact lines in a file. Each replacement is (old_line, new_line)."""
    with open(filepath, 'rb') as f:
        data = f.read()
    text = data.decode('gbk', errors='replace')
    
    changes = 0
    for old, new in replacements:
        if old in text:
            text = text.replace(old, new, 1)
            changes += 1
    
    if changes > 0:
        with open(filepath, 'wb') as f:
            f.write(text.encode('gbk', errors='replace'))
    
    return changes


def fix_swordman():
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'swordman.txt')
    replacements = [
        # Dynamic strings with getarg/strcharinfo
        ('mes "This is the "+getarg(0)+" check point! Cheer up!";',
         'mes "\xd5\xe2\xc0\xef\xca\xc7"+getarg(0)+"\xbc\xec\xb2\xe9\xb5\xe3\xa3\xa1\xbc\xd3\xd3\xcd\xa3\xa1";'),
        ('mes "Applicant " + strcharinfo(0) + ". Do you surrender??";',
         'mes "\xc9\xea\xc7\xeb\xc8\xcb " + strcharinfo(0) + "\xa1\xa3\xc4\xe3\xd2\xaa\xb7\xc5\xc6\xfa\xc2\xf0\xa3\xbf\xa3\xbf";'),
    ]
    # Use unicode replacements instead
    replacements = [
        ('mes "This is the "+getarg(0)+" check point! Cheer up!";',
         'mes "这里是"+getarg(0)+"检查点！加油！";'),
        ('mes "Applicant " + strcharinfo(0) + ". Do you surrender??";',
         'mes "申请人 " + strcharinfo(0) + "。你要放弃吗？？";'),
    ]
    n = fix_file(filepath, replacements)
    print(f"  swordman.txt: {n} fixes applied")
    return n


def fix_mage():
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'mage.txt')
    replacements = [
        ('mes "Okay. Sign right there. Oh, you\'re very good at spelling. Alright. So your name is... " + strcharinfo(0) + ".";',
         'mes "好的。在这里签名。哦，你的字写得真好。好的。你的名字是... " + strcharinfo(0) + "。";'),
        ('mes "" + strcharinfo(0) + "\'s test was...";',
         'mes "" + strcharinfo(0) + "的考试是...";'),
        ('mes "The Serial Number is #" + .@input + ", correct?";',
         'mes "序列号是 #" + .@input + "，对吗？";'),
    ]
    n = fix_file(filepath, replacements)
    print(f"  mage.txt: {n} fixes applied")
    return n


def fix_archer():
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'archer.txt')
    replacements = [
        ('mes "Are you..." + strcharinfo(0) + "?";',
         'mes "你是..." + strcharinfo(0) + "？";'),
        ('mes "Total Grades: ^FF0000" + .@total_archer + "^000000 / 40";',
         'mes "总评分: ^FF0000" + .@total_archer + "^000000 / 40";'),
        ('mes "Total Grades: ^0000FF" + .@total_archer + "^000000 / 40";',
         'mes "总评分: ^0000FF" + .@total_archer + "^000000 / 40";'),
    ]
    n = fix_file(filepath, replacements)
    print(f"  archer.txt: {n} fixes applied")
    return n


def fix_acolyte():
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'acolyte.txt')
    replacements = [
        # Father Mareusis
        ('mes "Good. I accept " + strcharinfo(0) + "\'s will to become an Acolyte. You understand that you must do penance before you can become a servant of God, right?";',
         'mes "好的。我接受 " + strcharinfo(0) + " 成为侍祭的意愿。你明白在成为上帝的仆人之前你必须进行苦修，对吧？";'),
        # L178 - standalone "Hmm..."
        # Need to find the exact context
        
        # Father Rubalkabara
        ('mes "Now, your name was " + strcharinfo(0) + ", right? Excellent, thank you for visiting me.";',
         'mes "你的名字是 " + strcharinfo(0) + "，对吧？太好了，谢谢你来拜访我。";'),
        
        # Mother Mathilda
        ('mes "Your name is " + strcharinfo(0) + "?";',
         'mes "你的名字是 " + strcharinfo(0) + "？";'),
        ('mes "What is your name? " + strcharinfo(0) + "? Let\'s see... Ah, you\'re on my list.";',
         'mes "你叫什么名字？" + strcharinfo(0) + "？让我看看...啊，你在我的名单上。";'),
        ('mes "I will send a message to the Sanctuary confirming that you, " + strcharinfo(0) + " visited me and completed your penance.";',
         'mes "我会向圣殿发送消息，确认你，" + strcharinfo(0) + " 拜访了我并完成了苦修。";'),
        ('mes "" + strcharinfo(0) + "? Let\'s see...";',
         'mes "" + strcharinfo(0) + "？让我看看...";'),
        
        # Father Yosuke
        ('mes "" + strcharinfo(0) + ", huh?";',
         'mes "" + strcharinfo(0) + "，嗯？";'),
        ('mes "Okay. I\'ll send a message to the Sanctuary that you, " + strcharinfo(0) + ", came to visit me.";',
         'mes "好的。我会向圣殿发送消息，说你，" + strcharinfo(0) + "，来拜访过我了。";'),
        ('mes "" + strcharinfo(0) + ", huh? Why isn\'t your name on my list?";',
         'mes "" + strcharinfo(0) + "，嗯？为什么你的名字不在我的名单上？";'),
    ]
    n = fix_file(filepath, replacements)
    
    # Handle the two standalone "Hmm..." lines that are in English context
    # These need special handling since "Hmm..." appears in both translated and untranslated contexts
    # Read the file and check lines 178 and 365
    with open(filepath, 'rb') as f:
        data = f.read()
    text = data.decode('gbk', errors='replace')
    lines = text.split('\n')
    
    extra = 0
    # Line 178 (0-indexed: 177)
    if len(lines) > 177 and lines[177].strip() == 'mes "Hmm...";':
        lines[177] = lines[177].replace('mes "Hmm...";', 'mes "嗯...";')
        extra += 1
    # Line 365 (0-indexed: 364)
    if len(lines) > 364 and lines[364].strip() == 'mes "Hmm...";':
        lines[364] = lines[364].replace('mes "Hmm...";', 'mes "嗯...";')
        extra += 1
    
    if extra > 0:
        result = '\n'.join(lines)
        with open(filepath, 'wb') as f:
            f.write(result.encode('gbk', errors='replace'))
    
    print(f"  acolyte.txt: {n + extra} fixes applied")
    return n + extra


def fix_merchant():
    """Fix the large untranslated section in merchant.txt."""
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'merchant.txt')
    
    replacements = [
        # === Chief Mahnsoo - failed test path (lines ~100-111) ===
        ('mes "Hello there,";', 'mes "你好，";'),
        ('mes ""+ strcharinfo(0) +".";', 'mes ""+ strcharinfo(0) +"。";'),
        ('mes "Unfortunately, you failed to earn your Merchant License this time.";',
         'mes "很遗憾，你这次没有获得商人执照。";'),
        ("mes \"I'll erase your records, so come back anytime when you want to reapply.\";",
         'mes "我会清除你的记录，想重新申请的时候随时回来。";'),
        
        # === Chief Mahnsoo - passed test path (lines ~115-148) ===
        ("mes \"I'm pleased to tell you\";", 'mes "我很高兴地告诉你";'),
        ('mes "that I have good news!";', 'mes "有个好消息！";'),
        ("mes \"The Merchant Guild accepted your application. You've proven that you are fully qualified to become a Merchant.\";",
         'mes "商人公会接受了你的申请。你已经证明了你完全有资格成为商人。";'),
        ('mes "The only thing to take care of is your Membership Fee.";',
         'mes "唯一需要处理的就是你的会员费。";'),
        ('mes "Are you ready?";', 'mes "你准备好了吗？";'),
        ('select("Pay the rest of the 500 Zeny:Quit")', 'select("支付剩余的500 Zeny:退出")'),
        ("mes \"I suppose you currently don't have enough zeny to pay the rest of your Membership fee right now.\";",
         'mes "看来你目前没有足够的Zeny来支付剩余的会员费。";'),
        ('mes "Please return when you have earned the 500 zeny that you need to become a Merchant.";',
         'mes "请在赚到成为商人所需的500 Zeny后再回来。";'),
        ('mes "Ah yes...!";', 'mes "啊，好的...！";'),
        ('mes "Now your";', 'mes "现在你的";'),
        ('mes "membership";', 'mes "会员资格";'),
        ('mes "is paid in full.";', 'mes "已经全额支付了。";'),
        ('mes "I suppose you need some time to gather some zeny to pay your membership fee. Please come";',
         'mes "我想你需要一些时间来凑齐Zeny支付会员费。请";'),
        ("mes \"back as soon as you're ready.\";", 'mes "准备好后尽快回来。";'),
        
        # === Chief Mahnsoo - delivery reminder (lines ~186-260) ===
        ("mes \"First, get the delivery package from the storehouse, and then take it to the former Swordman's Association in Prontera.\";",
         'mes "首先，从仓库取得快递包裹，然后送到普隆德拉的前剑士协会。";'),
        ("mes \"When you get there, give the package to the Kafra Employee stationed near there. Her name is Blossom. Did you get all that?\";",
         'mes "到了那里后，把包裹交给驻扎在附近的卡普拉职员。她的名字叫布洛瑟姆。都记住了吗？";'),
        ('mes "Remember, the Serial Number of the package is ^3355FF2485741^000000.";',
         'mes "记住，包裹的序列号是 ^3355FF2485741^000000。";'),
        ('mes "Remember, the Serial Number of the package is ^3355FF2328137^000000.";',
         'mes "记住，包裹的序列号是 ^3355FF2328137^000000。";'),
        ('mes "First, get the delivery package from the storehouse, and then take it to the Mage Guild in Geffen.";',
         'mes "首先，从仓库取得快递包裹，然后送到吉芬的魔法师公会。";'),
        ('mes "When you get there, give the package to the Mage Guildsman in charge. Remember, the packages Serial Number is ^3355FF2989396^000000.";',
         'mes "到了那里后，把包裹交给负责的魔法师公会成员。记住，包裹的序列号是 ^3355FF2989396^000000。";'),
        ('mes "When you get there, give the package to the Mage Guildsman in charge. Remember, the packages Serial Number is ^3355FF2191737^000000.";',
         'mes "到了那里后，把包裹交给负责的魔法师公会成员。记住，包裹的序列号是 ^3355FF2191737^000000。";'),
        ('mes "First, get the delivery package from the storehouse, and then take it to Morroc.";',
         'mes "首先，从仓库取得快递包裹，然后送到摩洛哥。";'),
        ("mes \"You'll have to find Java Dullihan, the Dyemaker, so that you can deliver the product he ordered.\";",
         'mes "你需要找到染色师贾瓦·杜利汉，把他订购的产品送给他。";'),
        ("mes \"But he's a little forgetful, so give it to one of his students. Remember, the package's Serial Number is ^3355FF3012685^000000.\";",
         'mes "但他有点健忘，所以交给他的一个学生吧。记住，包裹的序列号是 ^3355FF3012685^000000。";'),
        ("mes \"But he's a little forgetful, give it to one of his students. Remember, the package's Serial Number is ^3355FF3487372^000000.\";",
         'mes "但他有点健忘，交给他的一个学生吧。记住，包裹的序列号是 ^3355FF3487372^000000。";'),
        ("mes \"First, get the package from the storehouse, and then give it to the Kafra Employee stationed on Byalan Island. Her name is Blossom.\";",
         'mes "首先，从仓库取得包裹，然后交给驻扎在比亚兰岛的卡普拉职员。她的名字叫布洛瑟姆。";'),
        ("mes \"Remember, the package's Serial Number is ^3355FF3318702^000000.\";",
         'mes "记住，包裹的序列号是 ^3355FF3318702^000000。";'),
        ("mes \"Remember, the package's Serial Number is ^3355FF3543625^000000.\";",
         'mes "记住，包裹的序列号是 ^3355FF3543625^000000。";'),
        ('mes "Aaaannnnd...";', 'mes "还有...";'),
        ("mes \"Don't forget to deliver that message for me~\";",
         'mes "别忘了帮我送那封信~";'),
        ("mes \"Don't forget your destination and the package's Serial Number.\";",
         'mes "别忘了你的目的地和包裹的序列号。";'),
        ("mes \"You'll need to tell them\";", 'mes "你需要把这些告诉";'),
        ('mes "to the storekeeper.";', 'mes "仓库管理员。";'),
        ('mes "The storehouse is in the room";', 'mes "仓库在我右边";'),
        ('mes "to my right. There, you can talk";', 'mes "的房间里。在那里，你可以";'),
        ("mes \"to the storekeeper, and he'll\";", 'mes "和仓库管理员谈话，他会";'),
        ('mes "help you out.";', 'mes "帮你处理的。";'),
        ('mes "After you make the delivery, return to the storehouse and give the receipt to the storekeeper.";',
         'mes "送完货后，回到仓库把收据交给仓库管理员。";'),
        ('mes "Then, come back";', 'mes "然后，回来";'),
        ('mes "and see me.";', 'mes "找我。";'),
        
        # === Chief Mahnsoo - dynamic strings ===
        ('mes "Hmm... ";', 'mes "嗯... ";'),
        ('mes "" + strcharinfo(0) + "...";', 'mes "" + strcharinfo(0) + "...";'),  # keep as-is, name is dynamic
        ('mes "Hmm...";', 'mes "嗯...";'),
        ('mes "^3355FF"+getarg(0)+"^000000.";', 'mes "^3355FF"+getarg(0)+"^000000。";'),
        
        # === Union Staff Kay - delivery check (lines ~520-570) ===
        ('mes " [Union Staff Kay] ";', 'mes "[工会职员凯]";'),
        ('mes "Oh, yeah? Okay, lemme check. Your name is " + strcharinfo(0) + "? Alright, your destination was...";',
         'mes "哦，是吗？好的，让我查查。你的名字是 " + strcharinfo(0) + "？好的，你的目的地是...";'),
        ('mes "Wow! You met the Kafra babe in Prontera?! Lucky you~ ...Receipt?";',
         'mes "哇！你见到了普隆德拉的卡普拉美女？！你真幸运~ ...收据呢？";'),
        ('mes "Geffen Magic Academy. Okay, receipt?";',
         'mes "吉芬魔法学院。好的，收据呢？";'),
        ('mes "The dyemaker in Morocc. Not bad. Receipt?";',
         'mes "摩洛哥的染色师。不错。收据呢？";'),
        ('mes "Oh hohohoho~! The Kafra Babe on Byalan Island?! Awesome! Anyway, did you bring the receipt?";',
         'mes "哦呵呵呵呵~！比亚兰岛的卡普拉美女？！太棒了！总之，你带收据了吗？";'),
        ("mes \"Wait a sec.\";", 'mes "等一下。";'),
        ("mes \"Where's the receipt?\";", 'mes "收据呢？";'),
        ("mes \"If you don't have the receipt, you fail the test! You better talk to Mahnsoo if you wanna retake it, alright? Pay attention next time!\";",
         'mes "如果你没有收据，你就考试不及格！想重考的话最好去找马恩苏谈谈，好吗？下次注意点！";'),
        ("mes \"...Great! Everything's perfect! I'll report your success to the Guildmaster. You should talk to Chief Mahnsoo now, alright?\";",
         'mes "...太好了！一切完美！我会向公会长报告你的成功。你现在应该去找马恩苏会长谈谈，好吗？";'),
        
        # === Union Staff Kay - package handling (lines ~573-644) ===
        ('mes "Huh?";', 'mes "嗯？";'),
        ("mes \"You're back?\";", 'mes "你回来了？";'),
        ('mes "So how did";', 'mes "送货";'),
        ('mes "the delivery go?";', 'mes "怎么样？";'),
        ('select("*Sob* I lost the package.:Fine.")', 'select("*呜呜* 我弄丢了包裹:还好")'),
        ("mes \"Are you kidding me? You'll fail the test if you lose the package!\";",
         'mes "你在开玩笑吗？弄丢包裹你就考试不及格了！";'),
        ("mes \"Awwww man. Well, if you wanna restart the test, talk to Mahnsoo, okay? You're lucky you're getting another chance!\";",
         'mes "天哪。好吧，如果你想重新开始考试，去找马恩苏谈谈，好吗？你能再有一次机会已经很幸运了！";'),
        ('mes "Huh...";', 'mes "嗯...";'),
        ('mes "Okay...";', 'mes "好吧...";'),
        ("mes \"Hey, what are you still doing here? Shouldn't you be on your way already?\";",
         'mes "嘿，你还在这里干什么？你不是应该已经上路了吗？";'),
        ("select(\"I need a new package.:Oh, yeah. You're right!\")", 'select("我需要一个新包裹:哦，对。你说得对！")'),
        ('mes "Wha--?";', 'mes "什--？";'),
        ('mes "So where did";', 'mes "那包裹";'),
        ('mes "the package go?";', 'mes "去哪了？";'),
        ('mes "Where is it?!";', 'mes "在哪里？！";'),
        ('select("*Sob* I lost it!:I have it right here.")', 'select("*呜呜* 我弄丢了！:我就在这里")'),
        ('mes "You...";', 'mes "你...";'),
        ('mes "Lost it?!";', 'mes "弄丢了？！";'),
        ('mes "You failed the test!";', 'mes "你考试不及格了！";'),
        ("mes \"*Sigh* If you want to restart the test, go visit Mahnsoo in the other room, alright?\";",
         'mes "*叹气* 如果你想重新开始考试，去另一个房间找马恩苏，好吗？";'),
        ('mes "Huh.";', 'mes "嗯。";'),
        ('mes "I thought";', 'mes "我以为";'),
        ('mes "you lost it.";', 'mes "你弄丢了。";'),
        ("mes \"You don't\";", 'mes "你不";'),
        ('mes "need a new one.";', 'mes "需要新的。";'),
        ("mes \"*Sigh* Man, you're starting to become a pain in the ass. Hold on, lemme cancel your record...\";",
         'mes "*叹气* 老兄，你开始变得很烦人了。等一下，让我取消你的记录...";'),
        ("mes \"I need some time to get everything in order, so come back later.\";",
         'mes "我需要一些时间来整理一切，所以晚点再来。";'),
        ('mes "What a bummer...";', 'mes "真扫兴...";'),
        
        # === Union Staff Kay - destination confirmation (lines ~704-715) ===
        ('mes "Destination is Prontera. The Serial Number is " + .@input + ". Are you positive?";',
         'mes "目的地是普隆德拉。序列号是 " + .@input + "。你确定吗？";'),
        ("mes \"Destination is Geffen. Phew! That's really far! The Serial Number is \" + .@input + \". Are you positive?\";",
         'mes "目的地是吉芬。呼！真的很远！序列号是 " + .@input + "。你确定吗？";'),
        ("mes \"Destination is Morocc. That's pretty far away! The Serial Number is \" + .@input + \". Are you positive?\";",
         'mes "目的地是摩洛哥。那可真远！序列号是 " + .@input + "。你确定吗？";'),
        ('mes "Lucky you! Your destination is Byalan Island. The Serial Number is " + .@input + ". Are you positive?";',
         'mes "你真幸运！目的地是比亚兰岛。序列号是 " + .@input + "。你确定吗？";'),
        ('select("Positive.:Whoops! Wrong number!")', 'select("确定:哎呀！号码错了！")'),
        
        # === Student#mer in Morroc (lines ~775-857) ===
        ("mes \"You're from\";", 'mes "你是来自";'),
        ('mes "the Merchant Guild?";', 'mes "商人公会的吗？";'),
        ("mes \"Yes! You've come to\";", 'mes "是的！你来对";'),
        ('mes "the right place.";', 'mes "地方了。";'),
        ('mes "Okay~";', 'mes "好的~";'),
        ('mes "Please set the";', 'mes "请把包裹";'),
        ('mes "package down";', 'mes "放在";'),
        ('mes "over there.";', 'mes "那边。";'),
        ('mes "But...";', 'mes "但是...";'),
        ("mes \"Where's the\";", 'mes "我订的";'),
        ('mes "package I ordered?";', 'mes "包裹在哪里？";'),
        ("mes \"That's strange...\";", 'mes "真奇怪...";'),
        ("mes \"Let me check the Serial Number of the package so I can give you the receipt, okay?\";",
         'mes "让我检查一下包裹的序列号，这样我就可以给你收据了，好吗？";'),
        ('mes "3012685...";', 'mes "3012685...";'),
        ("mes \"That's right.\";", 'mes "没错。";'),
        ("mes \"Here's your\";", 'mes "这是你的";'),
        ('mes "receipt.";', 'mes "收据。";'),
        ('mes "3487372...";', 'mes "3487372...";'),
        ('mes "Excuse me, but...";', 'mes "不好意思，但是...";'),
        ("mes \"I don't think this is the package we ordered. The Serial Number should be 3012685. See?\";",
         'mes "我觉得这不是我们订的包裹。序列号应该是3012685。看到了吗？";'),
        ("mes \"I don't think this is the package we ordered. The Serial Number should be 3487372. See?\";",
         'mes "我觉得这不是我们订的包裹。序列号应该是3487372。看到了吗？";'),
        ("mes \"I don't think this is the package we ordered. The Serial Number should be 3012685 or 3487372. Well, one of those two...\";",
         'mes "我觉得这不是我们订的包裹。序列号应该是3012685或3487372。嗯，是其中一个...";'),
        ('mes "Thanks a lot!";', 'mes "非常感谢！";'),
        ('mes "See you again";', 'mes "下次";'),
        ('mes "sometime!";', 'mes "再见！";'),
        ('mes "Oh...";', 'mes "哦...";'),
        ("mes \"You're gonna\";", 'mes "你要";'),
        ('mes "go back? Okay";', 'mes "回去了？好的";'),
        ('mes "then, take care!";', 'mes "那保重！";'),
        ("mes \"Mr. Java Dullihan is the one and only, the best dye maker on the Rune-Midgard continent.\";",
         'mes "贾瓦·杜利汉先生是独一无二的，卢恩-米德加兹大陆上最好的染色师。";'),
        ("mes \"Aaaand I'm proud to say that I'm his student! Someday, I'll be able to make really beautiful dyes too!\";",
         'mes "而且我很自豪地说我是他的学生！总有一天，我也能制作出非常漂亮的染料！";'),
        ("mes \"Of course, I'm still learning the basics right now, but someday...\";",
         'mes "当然，我现在还在学习基础，但总有一天...";'),
        
        # === Guild Staff#mer in Geffen (lines ~860-938) ===
        ("mes \"Ah, you must be with the Merchant Guild. Finally, my package has arrived! Alright...!\";",
         'mes "啊，你一定是商人公会的。终于，我的包裹到了！好的...！";'),
        ('mes "You must be very tired";', 'mes "你一定很累了";'),
        ('mes "from having to travel";', 'mes "不得不在这种";'),
        ('mes "in this kind";', 'mes "天气里";'),
        ('mes "of weather...";', 'mes "赶路...";'),
        ('mes "Wait...";', 'mes "等等...";'),
        ("mes \"Where's the\";", 'mes "包裹";'),
        ('mes "package?";', 'mes "在哪里？";'),
        ('mes "Alright, let me";', 'mes "好的，让我";'),
        ('mes "check the Serial Number...";', 'mes "检查一下序列号...";'),
        ('mes "2989396. Yes, this is what we ordered. Here is your receipt.";',
         'mes "2989396。是的，这就是我们订的。这是你的收据。";'),
        ('mes "2191737. Yes, this is what we ordered. Here is your receipt.";',
         'mes "2191737。是的，这就是我们订的。这是你的收据。";'),
        ("mes \"Uh oh, this is the wrong number. This isn't what we ordered...\";",
         'mes "糟糕，号码不对。这不是我们订的...";'),
        ('mes "The Serial Number";', 'mes "序列号";'),
        ('mes "should be 2989396.";', 'mes "应该是2989396。";'),
        ('mes "should be 2191737.";', 'mes "应该是2191737。";'),
        ('mes "should be 2989396";', 'mes "应该是2989396";'),
        ('mes "or 2191737, one of";', 'mes "或2191737，是";'),
        ('mes "those two.";', 'mes "其中一个。";'),
        ('mes "Look here!";', 'mes "看这里！";'),
        ("mes \"Don't you see\";", 'mes "你没看出";'),
        ('mes "something";', 'mes "有什么";'),
        ('mes "is wrong?";', 'mes "不对吗？";'),
        ('mes "Heh heh~";', 'mes "嘿嘿~";'),
        ('mes "Thank you!";', 'mes "谢谢！";'),
        ('mes "Bye bye!";', 'mes "再见！";'),
        ('mes "Hello,";', 'mes "你好，";'),
        ('mes "Merchant Guildsman~";', 'mes "商人公会成员~";'),
        ('mes "I give you my thanks.";', 'mes "我向你表示感谢。";'),
        ("mes \"My package should have arrived by now. Huh. I guess the Merchant Guild might be running a little late...\";",
         'mes "我的包裹现在应该到了。嗯。我猜商人公会可能有点晚了...";'),
        
        # === Kafra Employee#mer in Prontera (lines ~941-1057) ===
        ('mes "Oh! Thank you for";', 'mes "哦！谢谢你";'),
        ('mes "traveling such a long";', 'mes "不远万里";'),
        ('mes "way to come over here~";', 'mes "来到这里~";'),
        ('mes "A delivery from";', 'mes "来自";'),
        ('mes "the Merchant Guild?";', 'mes "商人公会的快递？";'),
        ('mes "Oh, yes, please set";', 'mes "哦，好的，请把它";'),
        ('mes "it down right over there...";', 'mes "放在那边...";'),
        ('mes "You must be really tired";', 'mes "你一定很累了";'),
        ('mes "after carrying it for so long!";', 'mes "搬了这么久！";'),
        ("mes \"W-wait. Didn't you bring it?\";", 'mes "等-等等。你没带来吗？";'),
        ("mes \"Where's the package?\";", 'mes "包裹在哪里？";'),
        ('mes "Now, let me check";', 'mes "现在，让我检查一下";'),
        ('mes "the serial number...";', 'mes "序列号...";'),
        ('mes "2485741. Right, this is";', 'mes "2485741。对，这就是";'),
        ('mes "the one we ordered. Oh,";', 'mes "我们订的。哦，";'),
        ("mes \"and don't forget this receipt!\";", 'mes "别忘了这张收据！";'),
        ('mes "2328137. Right, this is";', 'mes "2328137。对，这就是";'),
        ('mes "Mmmm? Hold on. This is";', 'mes "嗯？等一下。这是";'),
        ('mes "the wrong package. What we";', 'mes "错误的包裹。我们";'),
        ("mes \"ordered had the serial number 2485741. I'm sure it's not this.\";",
         'mes "订的序列号是2485741。我确定不是这个。";'),
        ("mes \"ordered had the serial number 2328137. I'm sure it's not this.\";",
         'mes "订的序列号是2328137。我确定不是这个。";'),
        ('mes "ordered had the serial number 2485741 or 2328137.";',
         'mes "订的序列号是2485741或2328137。";'),
        ("mes \"I'm afraid there\";", 'mes "恐怕";'),
        ('mes "must be some kind";', 'mes "一定是出了";'),
        ('mes "of mistake. Perhaps";', 'mes "什么差错。也许";'),
        ('mes "you should go back to";', 'mes "你应该回";'),
        ('mes "the Merchant Guild to";', 'mes "商人公会";'),
        ('mes "clear up this situation?";', 'mes "把情况弄清楚？";'),
        ('mes "Thanks again";', 'mes "再次感谢你";'),
        ('mes "for going through";', 'mes "经历了";'),
        ('mes "all of that trouble~";', 'mes "这些麻烦~";'),
        ('mes "Welcome to the";', 'mes "欢迎来到";'),
        ('mes "Kafra Corportation,";', 'mes "卡普拉公司，";'),
        ('mes "where the service is";', 'mes "我们的服务";'),
        ('mes "always on your side~";', 'mes "永远在你身边~";'),
        ('mes "As you can see, the";', 'mes "如你所见，";'),
        ('mes "Swordman Assocation";', 'mes "剑士协会";'),
        ('mes "has moved to Izlude, a";', 'mes "已经搬到了伊斯鲁德，";'),
        ('mes "satellite city of Prontera.";', 'mes "普隆德拉的卫星城。";'),
        ('mes "Currently, we offer a Teleport";', 'mes "目前，我们提供传送";'),
        ('mes "Service to Izlude for 600 zeny.";', 'mes "到伊斯鲁德的服务，收费600 Zeny。";'),
        ('select("Use:Cancel")', 'select("使用:取消")'),
        ("mes \"I'm sorry, but you\";", 'mes "抱歉，你";'),
        ("mes \"don't have enough zeny\";", 'mes "没有足够的Zeny";'),
        ('mes "for this Teleport Service.";', 'mes "使用这个传送服务。";'),
        
        # === F_MercKafra function (Byalan Island Kafra) (lines ~1060-1155) ===
        ('mes "Oh hello~";', 'mes "哦你好~";'),
        ('mes "Um, is there";', 'mes "嗯，有什么";'),
        ('mes "some special reason";', 'mes "特别的原因";'),
        ("mes \"as to why you're here?\";", 'mes "让你来这里吗？";'),
        ('mes "3318702. Right, this is";', 'mes "3318702。对，这就是";'),
        ('mes "3543625. Right, this is";', 'mes "3543625。对，这就是";'),
        ('mes "Mmmm? Hold on. This is";', 'mes "嗯？等一下。这是";'),
        ("mes \"ordered had the serial number 3318702. I'm sure it's not this.\";",
         'mes "订的序列号是3318702。我确定不是这个。";'),
        ("mes \"ordered had the serial number 3543625. I'm sure it's not this.\";",
         'mes "订的序列号是3543625。我确定不是这个。";'),
        ('mes "ordered had the serial number 3318702 or 3543625.";',
         'mes "订的序列号是3318702或3543625。";'),
        ('select("This is from Chief Mahnsoo of the Merchant Guild...")',
         'select("这是商人公会马恩苏会长的信...")'),
        ('mes "Oh~! A letter from";', 'mes "哦~！马恩苏的";'),
        ("mes \"Mahnsoo! Thank you\";", 'mes "信！非常感谢";'),
        ("mes \"so much, I've been dying\";", 'mes "你，我一直很想";'),
        ('mes "to hear from him. How is";', 'mes "收到他的消息。他";'),
        ('mes "he doing, is he alright?";', 'mes "怎么样，还好吗？";'),
        ("mes \"I can't wait to read it...\";", 'mes "我迫不及待要读了...";'),
        ('mes "Oh, thank you for";', 'mes "哦，谢谢你";'),
        ('mes "going through all the";', 'mes "经历了所有";'),
        ('mes "trouble of delivering all";', 'mes "这些送货的";'),
        ("mes \"of this. This isn't anything\";", 'mes "麻烦。这不是什么";'),
        ('mes "special, but please take it.";', 'mes "特别的东西，但请收下。";'),
        ('mes "Well, see you again~";', 'mes "好了，再见~";'),
    ]
    
    n = fix_file(filepath, replacements)
    print(f"  merchant.txt: {n} fixes applied")
    return n


def fix_thief():
    filepath = os.path.join(PROJECT_ROOT, 'npc', 'pre-re', 'jobs', '1-1', 'thief.txt')
    replacements = [
        # Dynamic strings
        ('mes "" + strcharinfo(0) + "?";',
         'mes "" + strcharinfo(0) + "？";'),
        ('mes "What kind of name is " + strcharinfo(0) + "? Anyway, give me a second.";',
         'mes "什么名字啊 " + strcharinfo(0) + "？算了，给我一秒钟。";'),
        ('mes "Huh, " + countitem(1069) + " of them.";',
         'mes "嗯，" + countitem(1069) + "个。";'),
        ('mes "Now I\'ll just check your Orange Gooey Mushrooms. That\'s " + countitem(1070) + " you gathered.";',
         'mes "现在让我检查一下你的橙色粘液蘑菇。你收集了 " + countitem(1070) + " 个。";'),
        ('mes "Hmmm. " + .@total_thief + " degrees, multiplied by the speed of light, divided by the integral of pi times height plus the absolute value of politics...";',
         'mes "嗯。" + .@total_thief + " 度，乘以光速，除以圆周率乘以高度的积分加上政治的绝对值...";'),
        ('mes "Okay!";', 'mes "好的！";'),
        ('mes "I got it.";', 'mes "我算出来了。";'),
        ('mes "Hmm...";', 'mes "嗯...";'),
        ('mes "Your name is " + strcharinfo(0) + "? Ah, it\'s on the list. Alright, I\'ll let you into the Mushroom Farm , but I can\'t guarantee your safety...";',
         'mes "你的名字是 " + strcharinfo(0) + "？啊，在名单上。好的，我让你进蘑菇农场，但我不能保证你的安全...";'),
    ]
    n = fix_file(filepath, replacements)
    print(f"  thief.txt: {n} fixes applied")
    return n


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("Fixing remaining untranslated lines in job change scripts...")
    print("=" * 50)
    
    total = 0
    total += fix_swordman()
    total += fix_mage()
    total += fix_archer()
    total += fix_acolyte()
    total += fix_merchant()
    total += fix_thief()
    
    print("=" * 50)
    print(f"Total fixes applied: {total}")


if __name__ == '__main__':
    main()
