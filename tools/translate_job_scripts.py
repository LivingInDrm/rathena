#!/usr/bin/env python3
"""
Translate rAthena 1-1 job change NPC scripts from English to Chinese.

Approach:
  - For each file, a per-file translation dictionary maps English dialogue
    strings (the text inside mes "..." and select("...")) to Chinese.
  - Lines are processed one at a time; only mes/select content is replaced.
  - All script structure (coordinates, sprite IDs, variable names, function
    calls, logic, comments, warp definitions, monster spawns, etc.) is
    preserved exactly.
  - Output is written in GBK encoding via binary mode to avoid Windows
    line-ending issues.
  - Original files are backed up to npc_backup_en/ before modification.

Usage:
    python tools/translate_job_scripts.py              # translate all 6 files
    python tools/translate_job_scripts.py --dry-run    # preview without writing
    python tools/translate_job_scripts.py --restore    # restore EN, then re-translate
    python tools/translate_job_scripts.py --restore --dry-run  # restore only
"""

import os
import re
import sys
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

def backup_file(filepath):
    """Back up the original file to npc_backup_en/, preserving directory structure."""
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    backup_path = os.path.join(PROJECT_ROOT, 'npc_backup_en', rel)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"  [backup] {rel} -> npc_backup_en/{rel}")
    else:
        print(f"  [backup] already exists: npc_backup_en/{rel}")


def read_file(filepath):
    """Read a file trying UTF-8 first, then GBK, then latin-1 as fallback."""
    for enc in ('utf-8', 'gbk', 'latin-1'):
        try:
            with open(filepath, 'r', encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    raise RuntimeError(f"Cannot decode {filepath}")


def write_gbk(filepath, content):
    """Write content in GBK encoding using binary mode (no line-ending mangling)."""
    with open(filepath, 'wb') as f:
        f.write(content.encode('gbk', errors='replace'))


def translate_line(line, translations):
    """
    Translate a single line if it contains mes "..." or select("...").

    Rules:
      - Comments (lines whose first non-whitespace is //) are never touched.
      - Only the quoted string content inside mes "..." or select("...") is
        replaced; everything else on the line is preserved.
      - The translation dictionary is checked for exact matches of the
        extracted string.  If no match is found the line is returned as-is.
    """
    stripped = line.lstrip()

    # Never touch comments
    if stripped.startswith('//'):
        return line

    # --- mes "..." ---
    # Matches:  mes "some text";   or   mes "some text";  (with leading whitespace)
    # Also handles lines like:  mes "[NPC Name]";
    mes_match = re.match(r'^(\s*mes\s+)"(.*)"(\s*;.*)$', line)
    if mes_match:
        prefix = mes_match.group(1)
        content = mes_match.group(2)
        suffix = mes_match.group(3)
        if content in translations:
            return prefix + '"' + translations[content] + '"' + suffix
        return line

    # --- select("opt1:opt2:...") ---
    # Handles both  select("...")  and  switch(select("..."))
    sel_match = re.search(r'(select\()"([^"]*)"(\))', line)
    if sel_match:
        content = sel_match.group(2)
        if content in translations:
            new_content = translations[content]
            return line[:sel_match.start()] + sel_match.group(1) + '"' + new_content + '"' + sel_match.group(3) + line[sel_match.end():]
        # Try translating individual options separated by ':'
        options = content.split(':')
        translated_options = []
        any_translated = False
        for opt in options:
            if opt in translations:
                translated_options.append(translations[opt])
                any_translated = True
            else:
                translated_options.append(opt)
        if any_translated:
            new_content = ':'.join(translated_options)
            return line[:sel_match.start()] + sel_match.group(1) + '"' + new_content + '"' + sel_match.group(3) + line[sel_match.end():]
        return line

    # --- mapannounce with string ---
    ann_match = re.search(r'(mapannounce\s+"[^"]*"\s*,\s*)"([^"]*)"', line)
    if ann_match:
        content = ann_match.group(2)
        if content in translations:
            return line[:ann_match.start()] + ann_match.group(1) + '"' + translations[content] + '"' + line[ann_match.end():]
        return line

    return line


def translate_file(filepath, translations, dry_run=False):
    """Read, translate, and write a single NPC script file."""
    rel = os.path.relpath(filepath, PROJECT_ROOT)
    if not os.path.exists(filepath):
        print(f"  [SKIP] file not found: {rel}")
        return False

    print(f"  [translate] {rel}")
    content = read_file(filepath)
    lines = content.split('\n')

    translated_lines = []
    changes = 0
    for line in lines:
        new_line = translate_line(line, translations)
        if new_line != line:
            changes += 1
        translated_lines.append(new_line)

    result = '\n'.join(translated_lines)
    print(f"    -> {changes} lines translated")

    if not dry_run:
        backup_file(filepath)
        write_gbk(filepath, result)
        print(f"    -> written (GBK)")
    else:
        print(f"    -> dry run, not written")

    return True


# ---------------------------------------------------------------------------
# Translation Dictionaries
# ---------------------------------------------------------------------------
# Each dictionary maps the exact English string (the content between quotes
# in mes "..." or select("...")) to its Chinese translation.
#
# NPC name brackets like [Swordman] are part of the mes content and are
# translated as a whole.
#
# Color codes (^FF0000 etc.) and variable references (strcharinfo(0)) are
# preserved in the translated strings.
# ---------------------------------------------------------------------------

SWORDMAN_TRANSLATIONS = {
    # --- NPC names ---
    "[Swordman]": "[剑士]",
    "[Test Hall Staff]": "[考场工作人员]",
    "[Medic]": "[医护兵]",
    "[Mae]": "[梅]",

    # --- Main NPC: Swordman#swd_1 (reborn path) ---
    "It...": "这...",
    "Can't be...": "不会吧...",
    "You've been reborn, haven't you?": "你转生了，对吧？",
    "I see you're retreading the path of the Swordman! Once you've gotten used to brandishing a sword, you can never go back!!": "我看你又踏上了剑士之路！一旦习惯了挥剑的感觉，就再也回不去了！！",
    "Hmm? Ah, you must first master the Basic Skills before you are ready to become a Swordman.": "嗯？啊，你必须先掌握基本技能，才能成为剑士。",
    "Come back to me when you have finished learning the Basic Novice Skills.": "学完初学者基本技能后再来找我吧。",
    "Excellent! Let me promote you to a Swordman right away!": "太好了！让我立刻把你提升为剑士！",
    "Hmm... You look like a well-experienced Swordman. Still, I'm sure that you must train to improve your skills and gain strength!": "嗯...你看起来像一个经验丰富的剑士。不过，我相信你还需要继续训练来提升技能和力量！",
    "Hm...?": "嗯...？",
    "You're a reborn": "你是一个转生的",
    "warrior, aren't you?": "战士，对吧？",
    "Hmmm...": "嗯嗯嗯...",
    "It seems that being": "看来成为",
    "a Swordman is not part": "剑士并不是",
    "of your destiny. I'm sorry,": "你命运的一部分。很抱歉，",
    "but it seems there is nothing": "但看起来我没有什么",
    "I can do for you.": "能为你做的。",

    # --- Main NPC: welcome / menu ---
    "Welcome to the": "欢迎来到",
    "Swordman Association!": "剑士协会！",
    "So...": "那么...",
    "What business": "有什么事",
    "brings you to us?": "让你来找我们？",

    # --- select options ---
    "Job Change:About Swordman.:About the Job requirements.:Cancel.": "转职:关于剑士:关于转职要求:取消",
    "Sign up.:Cancel.": "报名:取消",
    "Yes.:No.": "是:否",

    # --- Job Change path ---
    "Job change? Muhahaha! But you're already a Swordman! Be proud and be strong!": "转职？哈哈哈！但你已经是剑士了！骄傲地变强吧！",
    "Haha! Oh boy. I'm flattered, but you already have another job! Still, I can't blame you...": "哈哈！天哪。我很荣幸，但你已经有其他职业了！不过，我不怪你...",
    "So you wish to become a proud Swordman? By all means, please sign up!": "你想成为一名骄傲的剑士？当然可以，请报名吧！",
    "Ah, yes. Your application will be reviewed as soon as possible.": "啊，好的。你的申请将尽快审核。",
    "If you have already met the requirements, you can take an interview right now. Would you like to?": "如果你已经满足了要求，现在就可以参加面试。你愿意吗？",
    "Good, good.": "好的，好的。",
    "Now, let's see...": "现在，让我看看...",
    "Alright then. Feel free to come back whenever you are ready. All you ahve to do now is meet our requirements. Good luck to you.": "好吧。准备好了随时回来。你现在要做的就是满足我们的要求。祝你好运。",
    "Hm? Alright, come back whenever you change your mind. The world can always use another Swordman!": "嗯？好吧，改变主意了随时回来。这个世界总是需要更多的剑士！",
    "Hm, you still haven't learned all of the Basic Skills. You need to do that before you can become a Swordman.": "嗯，你还没有学完所有的基本技能。你需要先学完才能成为剑士。",
    "Check the requirements for job change again, and come back when you are ready.": "再检查一下转职要求，准备好了再来。",
    "Hm, you've learned all of the Basic Skills but didn't take the test yet. You must first pass the exam before you can change your job to Swordman.": "嗯，你已经学完了所有基本技能，但还没有参加考试。你必须先通过考试才能转职为剑士。",
    "Enter the room to my right so that you can take the test. You'll need to speak to my right so you can enter the examination area.": "进入我右边的房间参加考试。你需要和我右边的人说话才能进入考场。",
    "Hahaha! Congratulations! Now you are fully qualified to be a real Swordman! I will transform you right away!": "哈哈哈！恭喜你！现在你完全有资格成为一名真正的剑士了！我马上为你转职！",
    "Once again, congratulations. I expect that you will be a good representative of the Swordman Association.": "再次恭喜。我期待你能成为剑士协会的优秀代表。",

    # --- Case 2: About Swordman ---
    "So you wish to know more about the mighty Swordman job? Well, then...": "你想了解更多关于强大的剑士职业的信息？那么...",
    "Amongst the First Class jobs, the Swordman is the best melee fighter for three reasons.": "在所有一转职业中，剑士是最好的近战战士，原因有三。",
    "There are 3 reasons why Swordy is the best to approch a fight!": "剑士是最适合战斗的职业，有三个原因！",
    "First, Swordman has the benefit of additional HP. Second, Swordman generally have access to a wider selection fo weapons than the other First Class jobs.": "第一，剑士拥有额外HP的优势。第二，剑士通常比其他一转职业能使用更多种类的武器。",
    "And third, most of the Swordman skills are crushing physical attacks! In my opinion, being a Swordman is the best job ever!": "第三，大多数剑士技能都是强力的物理攻击！在我看来，剑士是最好的职业！",

    # --- Case 3: Requirements ---
    "But there's no need to tell you the requirements. You've met them and already became a Swordman! Well, anyway...": "但没有必要告诉你要求了。你已经满足了要求并成为了剑士！不过，无论如何...",
    "It's too late for you to become a Swordman. You already have another job. Still, there's no harm in telling you...": "你已经不能成为剑士了。你已经有其他职业了。不过，告诉你也无妨...",
    "First, you must learn all 9 of the Basic Skills. If you can't complete this requirement, you won't be able to change to any job.": "首先，你必须学会全部9个基本技能。如果你不能完成这个要求，你将无法转职为任何职业。",
    "Second, you must pass the Swordman Test. Inquire the Test Manager located in the waiting room of the Swordman Test.": "其次，你必须通过剑士考试。请向剑士考试等候室的考试管理员咨询。",
    "If you can complete these 2 requirements, you can change to a Swordman anytime you want.": "如果你能完成这两个要求，你随时可以转职为剑士。",

    # --- Case 4 ---
    "Ha ha ha!": "哈哈哈！",
    "Ah, youth!": "啊，年轻真好！",

    # --- Swordman#swd_2 (gate guard) ---
    "Sorry guy, but I can only allow Novices to enter the Test Hall.": "抱歉，我只能允许初学者进入考场。",
    "Who the hell are you?! Nobody, other than Novices, is permitted to come in here!": "你是谁？！除了初学者，任何人都不允许进入这里！",
    "Stop! I can't let you in until you learn all of the Basic Skills. The Test Hall isn't for goofing off!": "站住！在你学完所有基本技能之前，我不能让你进去。考场不是闹着玩的地方！",
    "Hey. You need to talk to the Swordman in the center of the room, not me.": "嘿。你需要和房间中央的剑士说话，不是我。",
    "Stop! If you want to take the Swordman Test, you'll need to fill out an application first.": "站住！如果你想参加剑士考试，你需要先填写申请表。",
    "The Swordman in the center of the room can help you with that, got it?": "房间中央的剑士可以帮你办理，明白了吗？",

    # --- Swordman#swd_3 (test explanation) ---
    "I will tell you about the Test! Listen carefully, I won't repeat myself.": "我来告诉你关于考试的事！仔细听，我不会重复的。",
    "The purpose of this test is to confirm whether or not you are qualified to be a Swordman. As you know, a Swordman needs physical strength and spirit!": "这个考试的目的是确认你是否有资格成为剑士。如你所知，剑士需要体力和精神力！",
    "Without those, you won't be able to become a Swordman. Now, the conditions for completing this test are very simple.": "没有这些，你就无法成为剑士。现在，完成这个考试的条件非常简单。",
    "You will travel through three courses and must reach the final checkpoint within ^FF000010 minutes^000000.": "你将通过三个关卡，必须在^FF000010分钟^000000内到达最终检查点。",
    "If you choose to 'Surrender,' or if you run out of time, you will not pass the test.": "如果你选择'放弃',或者时间用完,你将无法通过考试。",
    "If you find that you are not strong enough to pass the test, head to the entrance of the course and talk to the checkpoint manager.": "如果你发现自己不够强壮无法通过考试，请前往关卡入口与检查点管理员交谈。",
    "As you travel through the three courses, you may fall to a random, underground area. The course is designed so that you can still find your way back.": "在通过三个关卡的过程中，你可能会掉到随机的地下区域。关卡的设计使你仍然可以找到回去的路。",
    "However, be careful, as this will waste your time! Godspeed to you.": "但是要小心，这会浪费你的时间！祝你好运。",

    # --- Test Hall Staff#swd_1 ---
    "Hm? How did you get inside? You're not supposed to be in here, so please leave now.": "嗯？你是怎么进来的？你不应该在这里，请现在离开。",
    "Who are you?! This place is for the Swordman Test! You're not allowed to be in here! Leave now!": "你是谁？！这里是剑士考场！你不允许在这里！现在离开！",
    "So are you the one who wants to be a Swordman? Alright! You look reliable!": "你就是想成为剑士的人？好的！你看起来很可靠！",
    "Try to relax and do your best. This course isn't so difficult.": "放轻松，尽力而为。这个关卡并不难。",
    "Retesting? Try not to worry about it. It's good that you don't back down from a challenge! Here, take these and cheer up!": "重新测试？别担心。你不退缩是好事！拿着这些，振作起来！",
    "Don't ever give up! Now retesting!": "永远不要放弃！现在重新测试！",

    # --- Medic function ---
    # Note: "This is the "+getarg(0)+" check point! Cheer up!" is dynamic,
    # handled via the getarg pattern - we translate the static parts.

    # --- Test Hall Staff surrender function ---
    "Do you surrender?": "你要放弃吗？",
    "Bravo! Go for it again!": "好样的！再加油！",

    # --- F_JobSwdTestStaff ---
    # "Applicant " + strcharinfo(0) + ". Do you surrender??" is dynamic

    # --- Mae (success) ---
    "I sencerely congratulate you for passing the test!": "我真诚地祝贺你通过了考试！",
    "I already sent your test result to the Job Department.Please inquire at the Officer in Centre.Thank you.": "我已经把你的考试结果发送到了职业部门。请到中央的官员那里咨询。谢谢。",
}

MAGE_TRANSLATIONS = {
    # --- NPC names ---
    "[Mage Guildsman]": "[魔法师公会成员]",
    "[Mixing Machine]": "[混合机器]",
    "[Guide Book]": "[指南书]",
    "[Mage Test Solution No. 1]": "[魔法师测试溶液1号]",
    "[Mage Test Solution No. 2]": "[魔法师测试溶液2号]",
    "[Mage Test Solution No. 3]": "[魔法师测试溶液3号]",
    "[Mage Test Solution No. 4]": "[魔法师测试溶液4号]",

    # --- Reborn path ---
    "Whoa, long time no see! But weren't you supposed to be dead?": "哇，好久不见！但你不是应该已经死了吗？",
    "Ah, you must have been reborn. Well, I'm glad to have you back.": "啊，你一定是转生了。很高兴你回来了。",
    "I'm sorry, but I don't think you're ready to learn magic yet. Why don't you go finish learning the Basic Skills first?": "抱歉，我觉得你还没准备好学习魔法。你何不先去学完基本技能呢？",
    "Take your time. The more you learn, the more ready you'll be to learn magic again.": "慢慢来。你学得越多，就越准备好再次学习魔法。",
    "Well, since you have passed the Mage test once, I will not question your qualification. You want to have your magic skills back immediately, don't you?": "既然你已经通过了一次魔法师考试，我不会质疑你的资格。你想立刻恢复你的魔法技能，对吧？",
    "Wow, for some reason, you look way better than you did before. Anyway, I believe you will do a better job being a Mage as well.": "哇，不知为什么，你看起来比以前好多了。总之，我相信你作为魔法师也会做得更好。",
    "Is there anything more I can help you with? If not, why don't you go test your skills? The world is waiting for you~!": "还有什么我能帮你的吗？如果没有，何不去测试一下你的技能呢？世界在等着你~！",
    "What, are you interested in the Mage guild? I didn't want to tell you this, but you don't belong here.": "什么，你对魔法师公会感兴趣？我不想告诉你这个，但你不属于这里。",
    "I am not sure why you're still standing in front of me, but I can tell that you're not meant to be a Mage.": "我不确定你为什么还站在我面前，但我能看出你不适合当魔法师。",

    # --- Main dialogue ---
    "Yo. What's up?": "嘿。怎么了？",
    "I want to be a Mage.:Tell me the Requirements.:Pretty much nothing.": "我想成为魔法师:告诉我要求:没什么事",
    "Hey, haven't you realized? You're aleady a Mage, silly!": "嘿，你没意识到吗？你已经是魔法师了，傻瓜！",
    "One of these days you'll realize the power inside of you when you can make Fire with your mind!": "总有一天，当你能用意念制造火焰时，你会意识到你内心的力量！",
    "Hey~ C'mon. Quit playing games. You can't be a Mage because you already have another Job.": "嘿~别闹了。别开玩笑了。你不能成为魔法师，因为你已经有其他职业了。",
    "Wanna be a Mage, eh...?": "想成为魔法师，嗯...？",
    "Hey, look at you! You're kinda cute~! Not my type though...": "嘿，看看你！你还挺可爱的~！不过不是我的类型...",
    "Oooh, you're such a hot babe~!": "哦，你真是个大美人~！",
    "I like girls like you~": "我喜欢像你这样的女孩~",
    "Right, you said that you wanna be a Mage? Alright then, please sign the Mage Application.": "好的，你说你想成为魔法师？那好，请签署魔法师申请表。",
    "Sign Up.:Quit.": "报名:退出",
    "Okay. Sign right there. Oh, you're very good at spelling. Alright. So your name is... " + "\" + strcharinfo(0) + \"" + ".": None,  # handled specially below
    # We need the exact string from the file for this one:
    "Now it's time for": "现在是时候",
    "me to give you the test.": "给你考试了。",
    "Make me a ^3355FFMixed Solution No. 1^000000": "给我制作一瓶^3355FF混合溶液1号^000000",
    "and bring it back to me.": "然后带回来给我。",
    "Make me a ^3355FFMixed Solution No. 2^000000": "给我制作一瓶^3355FF混合溶液2号^000000",
    "Make me a ^3355FFMixed Solution No. 3^000000": "给我制作一瓶^3355FF混合溶液3号^000000",
    "Make me a ^3355FFMixed Solution No. 4^000000": "给我制作一瓶^3355FF混合溶液4号^000000",
    "You can find the necessary ingredients inside the Guide Book in this Guild. So you better look up what you need before you go.": "你可以在公会的指南书中找到所需的材料。所以你最好在出发前查看你需要什么。",
    "Once you collect all the ingredients you, use the machine in the center of the room to mix the solution. Good luck!": "收集完所有材料后，使用房间中央的机器来混合溶液。祝你好运！",
    "Whaaaaat~?! Right after you tell me that you wanna become a Mage, you change your mind?! Be a bit more decisive!": "什么~？！你刚告诉我你想成为魔法师，就改变主意了？！果断一点！",
    "Yeah? Ready...?": "是吗？准备好了...？",
    "Oh, what a bummer. You haven't met the requirements yet.": "哦，真遗憾。你还没有满足要求。",
    "Go back and reach Novice Job level 9 first. Don't forget that you also have to learn all of the Basic Skills before you come back.": "先回去达到初学者职业等级9。别忘了你还需要在回来之前学完所有基本技能。",
    "Making Mixed Solution No. 1.": "制作混合溶液1号。",
    "Making Mixed Solution No. 2.": "制作混合溶液2号。",
    "Making Mixed Solution No. 3.": "制作混合溶液3号。",
    "Making Mixed Solution No. 4.": "制作混合溶液4号。",
    "Okay, let me": "好的，让我",
    "check if you made your": "检查一下你的",
    "solution accurately...": "溶液是否准确...",
    "Hey, where's the Solution": "嘿，我要的溶液呢",
    "I asked for...? I can't check it if you don't show it to me, right?": "...？你不给我看，我怎么检查呢，对吧？",
    "Wait.": "等等。",
    "This isn't the": "这不是",
    "Solution I asked for!": "我要的溶液！",
    "You're supposed to make Mixed Solution No. 1 and bring it back to me. Now go and try it again.": "你应该制作混合溶液1号并带回来给我。现在去再试一次。",
    "You're supposed to make Mixed Solution No. 2 and bring it back to me. Now go and try it again.": "你应该制作混合溶液2号并带回来给我。现在去再试一次。",
    "You're supposed to make Mixed Solution No. 3 and bring it back to me. Now go and try it again.": "你应该制作混合溶液3号并带回来给我。现在去再试一次。",
    "You're supposed to make Mixed Solution No. 4 and bring it back to me. Now go and try it again.": "你应该制作混合溶液4号并带回来给我。现在去再试一次。",
    "Hmm. I can see that you tried really hard. For a beginner's attempt, this is really good.": "嗯。我能看出你真的很努力。对于初学者来说，这真的很好。",
    "Great work!": "干得好！",
    "Alright! I'm pleased to say that you've passed the Mage Test. I will transform you right away!": "好的！我很高兴地告诉你，你通过了魔法师考试。我马上为你转职！",
    "*Ahem*": "*咳咳*",
    "Congratulations!": "恭喜！",
    "You are now a Mage!": "你现在是魔法师了！",
    "'Welcome to My World~'": "'欢迎来到我的世界~'",
    "Heh heh, I just wanted to say that. You know, it's a quote from a well-known movie~": "嘿嘿，我只是想说这句话。你知道的，这是一部著名电影的台词~",
    "Now that you're a Mage just like us, let's be friends, okay?": "既然你现在和我们一样是魔法师了，让我们做朋友吧，好吗？",

    # --- Case 2: Requirements ---
    "Wanna be a Mage, eh?": "想成为魔法师，嗯？",
    "For a cutie like you, I'd be happy to explain the requirements!": "对于像你这样可爱的人，我很乐意解释要求！",
    "I'd be happy to explain the requirements for a pretty girl like you!": "我很乐意为像你这样漂亮的女孩解释要求！",
    "First of all, you have to reach Novice Job Level 10 and learn all of the Basic Skills. Then, you'll have to pass the Mage Test.": "首先，你必须达到初学者职业等级10并学会所有基本技能。然后，你需要通过魔法师考试。",
    "Your test is to": "你的考试是",
    "make me a": "给我制作一瓶",
    "^3355FFMixed Solution No. 1^000000": "^3355FF混合溶液1号^000000",
    "^3355FFMixed Solution No. 2^000000": "^3355FF混合溶液2号^000000",
    "^3355FFMixed Solution No. 3^000000": "^3355FF混合溶液3号^000000",
    "^3355FFMixed Solution No. 4^000000": "^3355FF混合溶液4号^000000",
    "You can look up the ingredients you'll need to make the Solution inside the Guide Book in this Guild.": "你可以在公会的指南书中查找制作溶液所需的材料。",
    "You will be informed as to which Mixed Solution you will need to create after signing the application form.": "签署申请表后，你将被告知需要制作哪种混合溶液。",
    "Let me know when you are ready to become a Mage, alright?": "准备好成为魔法师时告诉我，好吗？",
    "Nothing...?": "没事...？",

    # --- Mixing Machine ---
    "This machine is the property of the Geffen Mage Guild and is used only for mixing solutions for magic purposes.": "这台机器是吉芬魔法师公会的财产，仅用于混合魔法用途的溶液。",
    "Use Machine.:Cancel.": "使用机器:取消",
    "Choose the": "选择",
    "Solvent for": "溶液的",
    "the Solution.": "溶剂。",
    "Payon Solution.:Morocc Solution.:No Solvent.": "斐扬溶液:摩洛哥溶液:无溶剂",
    "Error.": "错误。",
    "Cannot find the item.": "找不到物品。",
    "Please check again.": "请再次检查。",
    "Process Halting.": "程序停止。",
    "Please choose if you wish to begin mixing, or to re-enter the number of items to be mixed.": "请选择是否开始混合，或重新输入要混合的物品数量。",
    "Begin Mixing.:Re-Enter Number of Items.:Reset.": "开始混合:重新输入物品数量:重置",
    "Please place the items into the Mixing Receptacle. Make sure the item amounts are correct.": "请将物品放入混合容器中。确保物品数量正确。",
    "You cannot adjust or restore items once they are placed into the Mixing Receptacle.": "物品放入混合容器后，无法调整或恢复。",
    "If everything is correct, press the 'Mix' button when you are ready. Otherwise, press the 'Cancel' button.": "如果一切正确,准备好后按'混合'按钮。否则,按'取消'按钮。",
    "Press 'Mix' Button.:Press 'Cancel' Button.": "按'混合'按钮:按'取消'按钮",
    "Place items into the Mixing Receptacle now. Please wait.": "现在将物品放入混合容器。请稍候。",
    "Insufficient Jellopy.": "金属碎片不足。",
    "Please Check again.": "请再次检查。",
    "Process Halted.": "程序已停止。",
    "Insufficient Fluff.": "绒毛不足。",
    "Insufficient Milk.": "牛奶不足。",
    "Solution not found.": "未找到溶液。",
    "Items are Ready.": "物品已准备好。",
    "Close the Lid.": "关闭盖子。",
    "Reset Complete.": "重置完成。",
    "Initiate again?": "再次开始？",
    "Yes.:No.": "是:否",
    "Process Halted.": "程序已停止。",
    "Thank you.": "谢谢。",
    "Nothing found.": "未找到任何东西。",
    "Select items to mix.": "选择要混合的物品。",
    "Jellopy.:Fluff.:Milk.:Ready to Mix.": "金属碎片:绒毛:牛奶:准备混合",
    "Error: Item limit exceeded. Please enter values less than 10,000 try again.": "错误：物品数量超限。请输入小于10,000的值后重试。",
    "Please enter the ": "请输入",
    "Serial Number of": "魔法粉末的",
    "the Magic Powder.": "序列号。",
    "Do you want to skip this Menu?": "你想跳过这个菜单吗？",
    "Invalid Serial Number.": "无效的序列号。",
    "Please try again.": "请再试一次。",
    "Confirm.:Cancel.": "确认:取消",
    "Choose a": "选择一个",
    "Catalyst Stone.": "催化石。",
    "Yellow Gemstone.:Red Gemstone.:Blue Gemstone.:1carat Diamond.:Skip.": "黄色宝石:红色宝石:蓝色宝石:1克拉钻石:跳过",
    "All Set.": "全部设置完毕。",
    "Initiating": "正在启动",
    "Mixing process.": "混合程序。",
    "Please Wait.": "请稍候。",
    "- Proverb of the Day -": "- 每日谚语 -",
    "An Eye for an Eye: When you take from a person, you must replace or repay in some way.": "以眼还眼：当你从别人那里拿走东西时，你必须以某种方式替换或偿还。",
    "Credibility is a Man's Currency: There's a value in genuine trust that cannot be measured.": "信誉是人的货币：真正的信任有着无法衡量的价值。",
    "What Goes Around Comes Around: Ultimately, you will be treated in the way you treat others.": "善有善报，恶有恶报：最终，你会以你对待别人的方式被对待。",
    "It means 'When you harm Another you will be harmed by him in an unavoidable situation'.": "意思是'当你伤害别人时,你将在不可避免的情况下被他伤害'。",
    "A good neighbor is better than a distant brother: When you need help, you can count on those close to you.": "远亲不如近邻：当你需要帮助时，你可以依靠身边的人。",
    "Birds of a Feather Flock Together: You can look at a person's friends as an indicator of their character.": "物以类聚，人以群分：你可以通过一个人的朋友来判断他的品格。",
    "Mage Test Solution No. 1.": "魔法师测试溶液1号。",
    "Mage Test Solution No. 2.": "魔法师测试溶液2号。",
    "Mage Test Solution No. 3.": "魔法师测试溶液3号。",
    "Mage Test Solution No. 4.": "魔法师测试溶液4号。",
    "Unexpected": "发生了",
    "Error Occurred.": "意外错误。",
    "Mixing Complete.": "混合完成。",

    # --- Bookshelf / Guide Book ---
    "This Guide Book is the property of the Geffen Mage Association. Please handle with care.": "本指南书是吉芬魔法师协会的财产。请小心使用。",
    "Solution No. 1.:Solution No. 2.:Solution No. 3.:Solution No. 4.:Close.": "溶液1号:溶液2号:溶液3号:溶液4号:关闭",
    "* Ingredients List *": "* 材料清单 *",
    "2 Jellopy": "2个金属碎片",
    "3 Fluff": "3个绒毛",
    "1 Milk": "1个牛奶",
    "* Solvent Agent *": "* 溶剂 *",
    "Payon Solution": "斐扬溶液",
    "Where to Find:": "获取地点：",
    "A small spring in Payon, the Archer Village.": "斐扬弓箭手村的一个小泉。",
    "* Magic Power Serial Code *": "* 魔力序列号 *",
    "8472": "8472",
    "* Catalyst *": "* 催化剂 *",
    "Yellow Gemstone": "黄色宝石",
    "(Provided by": "（由",
    "Mixing Machine)": "混合机器提供）",
    "3 Jellopy": "3个金属碎片",
    "1 Fluff": "1个绒毛",
    "None": "无",
    "3735": "3735",
    "Red Gemstone": "红色宝石",
    "6 Jellopy": "6个金属碎片",
    "2750": "2750",
    "Blue Gemstone": "蓝色宝石",
    "2 Jellopy": "2个金属碎片",
    "Morroc Solution": "摩洛哥溶液",
    "A small spring near entrance of pyramid in Morroc.": "摩洛哥金字塔入口附近的一个小泉。",
    "5429": "5429",
    "1 carat Diamond": "1克拉钻石",
}

# Remove the None entry that was a mistake
MAGE_TRANSLATIONS = {k: v for k, v in MAGE_TRANSLATIONS.items() if v is not None}

ARCHER_TRANSLATIONS = {
    # --- NPC names ---
    "[Archer Guildsman]": "[弓箭手公会成员]",

    # --- Reborn path ---
    "Hey, I know you.": "嘿，我认识你。",
    "You took this test": "你以前参加过",
    "before, didn't you?": "这个考试，对吧？",
    "Ah, you must have been": "啊，你一定去过",
    "to Valhalla and been reborn.": "瓦尔哈拉并转生了。",
    "Wow, that's so impressive!": "哇，太厉害了！",
    "Err...": "呃...",
    "You'd better learn all the Basic Skills first before you can become an Archer.": "你最好先学完所有基本技能才能成为弓箭手。",
    "Alright, see you later.": "好的，回头见。",
    "Well then. I don't": "那么。我不",
    "need to say anything else.": "需要再说什么了。",
    "I know you'll make a great Archer...": "我知道你会成为一名出色的弓箭手...",
    "Although there's no special": "虽然这次没有特别的",
    "reward for you this time, I hope you understand. Take care of yourself.": "奖励给你，希望你理解。保重。",
    "Oh...?": "哦...？",
    "Hey, what are": "嘿，你在",
    "you doing here...?": "这里做什么...？",
    "I can tell that you're not cut out to be an Archer. It sort of feels like you're meant to do": "我能看出你不适合当弓箭手。感觉你注定要做",
    "something else...": "其他的事情...",

    # --- Main dialogue ---
    "Good day. How may I help you?": "你好。有什么可以帮你的？",
    "I want to be an Archer.:I need the requirements, please.:Nothing, thanks.": "我想成为弓箭手:请告诉我要求:没事，谢谢",
    "You've already become an Archer...": "你已经是弓箭手了...",
    "Hmm...": "嗯...",
    "You don't look much like a Novice at all...": "你看起来一点也不像初学者...",
    "Anyway, whatever you are, you can't choose a job as an Archer because you have a job already.": "总之，不管你是什么，你不能选择弓箭手职业，因为你已经有职业了。",
    "Do you want to be an Archer?": "你想成为弓箭手吗？",
    "If so, you need to fill out this application form.": "如果是的话，你需要填写这份申请表。",
    "Apply.:Cancel": "申请:取消",
    "Okay, sign here. Alright, um, I'll promote you once you meet the requirements.": "好的，在这里签名。好的，嗯，一旦你满足要求，我就为你转职。",
    "If you think you've met them already, we can check that now.": "如果你觉得你已经满足了要求，我们现在就可以检查。",
    "Are you ready?": "你准备好了吗？",
    "Yes, I am.:No, not yet.": "是的，我准备好了:不，还没有",
    "Alright, let me check.": "好的，让我检查一下。",
    "I understand. Be my guest if you want to look at the requirements.": "我理解。如果你想看看要求，请随意。",
    "Well, alright.": "好吧。",
    "See you next time.": "下次见。",
    "Well, you're not at the right job level. Please check the requirements again.": "嗯，你的职业等级不够。请再次检查要求。",
    "Your job level must be at least 10, and don't forget you should learn all of the Basic Skills. Once you've done that, come back.": "你的职业等级必须至少为10，别忘了你应该学会所有基本技能。完成后再回来。",
    "Excellent!": "太好了！",
    "Now then,": "那么，",
    "let's see...": "让我看看...",
    "I will appraise the value of the various types of Trunks, needed to produce a Bow, that you've brought.": "我将评估你带来的各种类型的树干的价值，这些树干是制作弓所需的。",
    "Um...": "嗯...",
    "Unfortunately you didn't bring any of the required items. There's nothing for me to appraise.": "很遗憾你没有带来任何所需的物品。我没有什么可以评估的。",
    "Less than 25!? You have to get a grade of at least 25! Come on, try harder!": "不到25！？你必须至少获得25分！加油，再努力一点！",
    "Wow! More than 40!": "哇！超过40分！",
    "Excellent! Congratulations!": "太好了！恭喜！",
    "More than 30! Nice job!": "超过30分！干得好！",
    "Congratulations!": "恭喜！",
    "*Sigh* Well, you just barely passed... Anyway, well done.": "*叹气* 嗯，你勉强通过了...不管怎样，做得好。",
    "I'll transfer these Trunks to our Bow Production Department. Now that you've met the requirements, let me promote you right away!": "我会把这些树干转交给我们的弓制作部门。既然你已经满足了要求，让我立刻为你转职！",
    "You are now an Archer!": "你现在是弓箭手了！",
    "Of course, we expect that you will help contribute towards the future of the Archer Guild with your efforts.": "当然，我们期望你能用你的努力为弓箭手公会的未来做出贡献。",
    "Ah, your bow has arrived from the Bow Production Department. Here, take it! It's yours~": "啊，你的弓已经从弓制作部门送来了。拿着吧！这是你的~",
    "Now, off you go. Hunt with pride, knowing you were trained by one of the best!": "好了，出发吧。骄傲地去狩猎吧，要知道你是由最优秀的人训练出来的！",

    # --- Case 2: Requirements ---
    "I will explain the requirements for being an Archer.": "我来解释成为弓箭手的要求。",
    "But...": "但是...",
    "You're already an Archer. You should know these already...": "你已经是弓箭手了。你应该已经知道这些了...",
    "Wait a second. You've chosen a different job already. You don't need to know this~": "等一下。你已经选择了其他职业。你不需要知道这些~",
    "So...Yeah...no real reason to tell you the requirements...": "所以...是的...没有什么理由告诉你要求了...",
    "First of all, you have to the Job Level 9 as a Novice, and know all of the Basic Skills.": "首先，你必须作为初学者达到职业等级9，并学会所有基本技能。",
    "An Archer needs extremely high concentration and reflexes, so we do not accept those who have little patience.": "弓箭手需要极高的专注力和反应力，所以我们不接受缺乏耐心的人。",
    "You also have to gather ^FF0000Trunks^000000. There are 4 different types of Trunks, each of differing quality. You'll be given different grades for your Trunks, depending on their quality.": "你还需要收集^FF0000树干^000000。有4种不同类型的树干，每种质量不同。根据质量，你的树干会获得不同的评分。",
    "In order to become an Archer, you must receive a grade of at least ^0000FF25^000000 points out of 40. You can get Trunks from 'Willow,' the tree. Be careful, though. They can be tough monsters.": "要成为弓箭手，你必须在40分中至少获得^0000FF25^000000分。你可以从树怪'柳树'那里获得树干。不过要小心，它们可能是很强的怪物。",
}

ACOLYTE_TRANSLATIONS = {
    # --- NPC names ---
    "[Father Mareusis]": "[马雷乌西斯神父]",
    "[Father Rubalkabara]": "[鲁巴尔卡巴拉神父]",
    "[Mother Mathilda]": "[玛蒂尔达修女]",
    "[Father Yosuke]": "[洋介神父]",

    # --- Reborn path ---
    "Ah, I sense you have endured": "啊，我感觉到你经历了",
    "a past life experience. You must have learned many things before entering Valhalla.": "前世的经历。你在进入瓦尔哈拉之前一定学到了很多东西。",
    "Unfortunately, I don't think you're ready to become an Acolyte yet. Please finish learning all of the Basic Skills first.": "很遗憾，我认为你还没有准备好成为侍祭。请先学完所有基本技能。",
    "In the meantime,": "在此期间，",
    "I will wait until": "我会等到",
    "you are ready.": "你准备好。",
    "May God be": "愿上帝",
    "with you.": "与你同在。",
    "Well, I welcome you": "好的，我欢迎你",
    "back from Valhalla and": "从瓦尔哈拉回来，",
    "wish you luck on your": "祝你在新的",
    "new life's journey.": "人生旅途中好运。",
    "Now, venture forth and seek those who need your help. May God light your path.": "现在，勇往直前，去寻找那些需要你帮助的人。愿上帝照亮你的道路。",
    "Now, venture forth to seek people who need your help. May God enlighten your way.": "现在，勇往直前去寻找需要你帮助的人。愿上帝指引你的方向。",
    "I sense that you have endured a past life experience. You must have learned many things before entering Valhalla.": "我感觉到你经历了前世的经历。你在进入瓦尔哈拉之前一定学到了很多东西。",
    "However, I can tell that you are not suited to be an Acolyte. Please remember who you were in your past life and find your path.": "然而，我能看出你不适合成为侍祭。请记住你前世是谁，找到你的道路。",

    # --- Main dialogue ---
    "What is it that you seek?": "你在寻找什么？",
    "Father, I want to be a Acolyte.:Acolyte Requirements.:Just looking around.": "神父，我想成为侍祭:侍祭要求:只是看看",
    "Are you feeling okay today? I can tell by your attire that you are already an Acolyte. You're not joking around, are you?": "你今天感觉还好吗？从你的着装我能看出你已经是侍祭了。你不是在开玩笑吧？",
    "I'm sorry, but we can only accept Novices as applicants for the job change to Acolyte.": "抱歉，我们只能接受初学者申请转职为侍祭。",
    "Do you truly": "你真的",
    "wish to become": "想成为",
    "a servant of God?": "上帝的仆人吗？",
    "Yes Father, I do.:Nope, I lied.": "是的神父，我愿意:不，我撒谎了",
    "Well, I will": "好的，我将",
    "give you a mission...": "给你一个任务...",
    "Please visit ^000077Father Rubalkabara^000000, a member of the Prontera Parish, and return here. He has been practicing asceticism in the ^000077Relics NorthEast of Prontera City^000000.": "请拜访普隆德拉教区的成员^000077鲁巴尔卡巴拉神父^000000，然后返回这里。他一直在^000077普隆德拉城东北方的遗迹^000000修行。",
    "Please visit ^000077Mother Mathilda^000000 and then return to me. She has been practicing asceticism near ^000077Morroc Town, SouthWest of Prontera City^000000.": "请拜访^000077玛蒂尔达修女^000000然后回来找我。她一直在^000077普隆德拉城西南方的摩洛哥镇^000000附近修行。",
    "Please visit ^000077Father Yosuke^000000 and return here. He has been practicing asceticism around ^000077a bridge somewhere NorthWest of Prontera^000000.": "请拜访^000077洋介神父^000000然后返回这里。他一直在^000077普隆德拉西北方某处的桥^000000附近修行。",
    "May the grace of God light your path and guide you during your journey of penance.": "愿上帝的恩典照亮你的道路，在你的苦修之旅中指引你。",
    "You lied?": "你撒谎了？",
    "It is good that you": "你能",
    "have confessed your": "忏悔你的",
    "wrongdoing. Go in": "过错是好的。",
    "peace, my son.": "平安地去吧，我的孩子。",
    "Oh, you've come back. Let me check and see if you are ready to serve God. Let's see...": "哦，你回来了。让我检查一下你是否准备好侍奉上帝。让我看看...",
    "Good Lord! Haven't you accomplished the Basic Training yet?! It's important that you finish that!": "天哪！你还没有完成基础训练吗？！完成那个很重要！",
    "You should have trained more! Go back and make sure you reach Novice Job Level 9 and learn all of the Basic Skills!": "你应该多训练！回去确保你达到初学者职业等级9并学会所有基本技能！",
    "Oh? I can't find your name on the Registration List.": "哦？我在登记名单上找不到你的名字。",
    "Please visit ^000077Father Rubalkabara^000000, a member of the Prontera Parish, and return here.": "请拜访普隆德拉教区的成员^000077鲁巴尔卡巴拉神父^000000，然后返回这里。",
    "He has been practicing asceticism in the ^000077Relics at the NorthEast of Prontera City^000000.": "他一直在^000077普隆德拉城东北方的遗迹^000000修行。",
    "Please Visit ^000077Mother Mathilda^000000 and return here to me.": "请拜访^000077玛蒂尔达修女^000000然后回来找我。",
    "She has been practicing asceticism near ^000077Morroc Town, located SouthWest of Prontera City^000000.": "她一直在^000077普隆德拉城西南方的摩洛哥镇^000000附近修行。",
    "Please visit ^000077 Father Yosuke ^000000 and return here to me.": "请拜访^000077洋介神父^000000然后回来找我。",
    "He has been practicing asceticism near a ^000077bridge somewhere to the NorthWest of Prontera^000000.": "他一直在^000077普隆德拉西北方某处的桥^000000附近修行。",
    "May the grace of God brighten your path and guide you on your journey of penance.": "愿上帝的恩典照亮你的道路，在你的苦修之旅中指引你。",
    "Your name is on the list and you've proven your qualification.": "你的名字在名单上，你已经证明了你的资格。",
    "I am proud to say that you are now ready to become an Acolyte!": "我很自豪地说，你现在已经准备好成为侍祭了！",
    "Always remember to be thankful to God, who is taking care of us all the time.": "永远记得感谢上帝，他一直在照顾我们。",
    "Always use your gifts to serve Him by helping others. In chaos and times of difficulty, face your hardships with unwavering faith.": "永远用你的天赋通过帮助他人来侍奉他。在混乱和困难时期，以坚定不移的信仰面对你的困难。",
    "Lastly, I want to sincerely congratulate you on persevering through your trial of penance.": "最后，我想真诚地祝贺你坚持完成了苦修的考验。",

    # --- Case 2: Requirements ---
    "Do you wish to become an Acolyte? You must fulfill two requirements.": "你想成为侍祭吗？你必须满足两个要求。",
    "First, you have to reach at least Novice Job Level 9 and learn all of the Basic Skills. Second, you will be given a trial of penance to overcome.": "首先，你必须至少达到初学者职业等级9并学会所有基本技能。其次，你将被给予一个苦修考验来克服。",
    "For your trial, please visit ^000077Father Rubalkabara ^000000 and then return here to me.": "作为你的考验，请拜访^000077鲁巴尔卡巴拉神父^000000然后回来找我。",
    "He is practicing asceticism in the ^000077Relics at the NorthEast of Prontera City^000000.": "他在^000077普隆德拉城东北方的遗迹^000000修行。",
    "For your trial, please visit ^000077Mother Mathilda^000000 and return here to me.": "作为你的考验，请拜访^000077玛蒂尔达修女^000000然后回来找我。",
    "She has been practicing asceticism near ^000077Morroc, located to the SouthWest of Prontera City^000000.": "她一直在^000077普隆德拉城西南方的摩洛哥^000000附近修行。",
    "For your trial, please visit ^000077Father Yosuke^000000 and return here to me.": "作为你的考验，请拜访^000077洋介神父^000000然后回来找我。",
    "He has been practicing asceticism around a bridge somewhere ^000077NorthWest of Prontera^000000.": "他一直在^000077普隆德拉西北方^000000某处的桥附近修行。",
    "May the grace of God light your path and guide you on your journey of penance.": "愿上帝的恩典照亮你的道路，在你的苦修之旅中指引你。",
    "The destination for this trial will be decided once you fill the application form.": "考验的目的地将在你填写申请表后决定。",
    "Please come back after fulfilling the two requirements I've asked of you. As long as your desire to serve God and others is sincere, you will be able to make it.": "请在满足我提出的两个要求后回来。只要你侍奉上帝和帮助他人的愿望是真诚的，你就能做到。",

    # --- Father Rubalkabara ---
    "Please take care. They should know that you've met me by the time you arrive at the Prontera Sanctuary.": "请保重。当你到达普隆德拉圣殿时，他们应该已经知道你见过我了。",
    "I've sent a carrier pigeon with a message. I hope it will arrive there safely...": "我已经用信鸽发送了消息。希望它能安全到达...",
    "Oh...? You must be the one who aspires to become an Acolyte. I've already received news from the Sanctuary that you might be coming.": "哦...？你一定是那个渴望成为侍祭的人。我已经从圣殿收到消息说你可能会来。",
    "I believe you've been told much about Acolytes from Friar Mareusis. Plus, there's plenty of helpful people in the Prontera Sanctuary.": "我相信马雷乌西斯修士已经告诉你很多关于侍祭的事了。而且，普隆德拉圣殿有很多乐于助人的人。",
    "I guess there's really no need for me to teach you much. Besides, I'm sure your someone from your generation may have trouble listening to an old man like me. Hahaha~": "我想我真的没有必要教你太多。况且，我相信你们这一代的人可能不太愿意听像我这样的老人说话。哈哈哈~",
    "Still, lessons may come from the places you'd least expect. God loves to teach his children in strange ways. You'll see.": "不过，教训可能来自你最意想不到的地方。上帝喜欢用奇特的方式教导他的孩子们。你会明白的。",
    "Well, I'll send the message telling them that you've come to visit me. So, you may now return to the Prontera Sanctuary.": "好的，我会发送消息告诉他们你来拜访过我了。所以，你现在可以返回普隆德拉圣殿了。",
    "Farewell.": "再见。",
    "Oh...": "哦...",
    "Are you one of the": "你是",
    "Acolyte applicants...?": "侍祭申请者之一...？",
    "Let's see...": "让我看看...",
    "I don't think your name": "我觉得你的名字",
    "is on my list. Hmmm...": "不在我的名单上。嗯...",
    "Why don't you go back to the Prontera Sanctuary and check again?": "你何不回普隆德拉圣殿再确认一下？",
    "Huh? What brings you here? This is a very dangerous place for a Novice like yourself!": "嗯？你来这里做什么？对于像你这样的初学者来说，这里非常危险！",
    "Greetings.": "你好。",
    "Welcome to the Deep. Feel free to sit and contemplate God's message with me. This place is beautiful, even if danger accompanies its sense of serenity...": "欢迎来到深处。请随意坐下来和我一起思考上帝的信息。这个地方很美，即使危险伴随着它的宁静...",
    "Oh ho...": "哦呵...",
    "Have you come into the Deep here for training? Or are you just a Wanderer?": "你来这里的深处是为了训练吗？还是你只是一个流浪者？",
    "Whoever you are, please take care of yourself. The monsters in here are shockingly strong, contrary to their cute appearance.": "不管你是谁，请照顾好自己。这里的怪物出奇地强大，与它们可爱的外表相反。",

    # --- Mother Mathilda ---
    "I will send a carrier pigeon to the Prontera Sanctuary. When you return, the Priest there should already have received my message.": "我会向普隆德拉圣殿发送信鸽。当你回去时，那里的牧师应该已经收到了我的消息。",
    "I will pray to God, and hope that you become an Acolyte soon.": "我会向上帝祈祷，希望你早日成为侍祭。",
    "Ah, you must be one of the Acolyte applicants. I sincerely welcome you.": "啊，你一定是侍祭申请者之一。我真诚地欢迎你。",
    "Please return to the Prontera Sanctuary and speak to the Priest in charge.": "请返回普隆德拉圣殿，与负责的牧师交谈。",
    "Ah...!": "啊...！",
    "You must be one": "你一定是",
    "of the Acolyte applicants.": "侍祭申请者之一。",
    "I sincerely welcome you.": "我真诚地欢迎你。",
    "Now, what is your name?": "那么，你叫什么名字？",
    "It seems your name": "看来你的名字",
    "is not on my list...": "不在我的名单上...",
    "Perhaps you should return to the Prontera Sanctuary and check the destination for your penance trial once again.": "也许你应该返回普隆德拉圣殿，再次确认你苦修考验的目的地。",
    "...": "...",
    "Hello there~": "你好~",
    "How is your practice coming along? I certainly hope you're enjoying living in the grace of God.": "你的修行进展如何？我当然希望你享受生活在上帝的恩典中。",
    "May God": "愿上帝",
    "be with you...": "与你同在...",

    # --- Father Yosuke ---
    "What?": "什么？",
    "Have you any more business with me?! You don't! Go back to the Sanctuary now!": "你还有什么事吗？！没有了！现在回圣殿去！",
    "Hey.": "嘿。",
    "Whatever you are,": "不管你是什么，",
    "you look like an": "你看起来像一个",
    "Acolyte applicant.": "侍祭申请者。",
    "Right?": "对吧？",
    "Not bad, not bad. You withstood the penance trial pretty well.": "不错，不错。你很好地经受住了苦修考验。",
    "So what's your name?": "你叫什么名字？",
    "Okay. I'll send a message to the Sanctuary that you, \" + strcharinfo(0) + \", came to visit me.": None,  # dynamic
    "Now go back to the Santuary and finish becoming an Acolyte, kid.": "现在回圣殿去完成成为侍祭的手续吧，孩子。",
    "You look like an Acolyte Applicant. Am I right?": "你看起来像一个侍祭申请者。我说得对吗？",
    "Not bad at all, you've made it all the way here from Prontera. So what's your name, kid?": "一点也不差，你从普隆德拉一路走到了这里。你叫什么名字，孩子？",
    "You probably made a mistake. Go back to the Santuary, and check with the Bishop.": "你可能搞错了。回圣殿去，和主教确认一下。",
    "You...": "你...",
    "Novice.": "初学者。",
    "There something": "有什么",
    "you wanna tell me?": "想告诉我的吗？",
    "Hey...": "嘿...",
    "If you like, come sit here with me and meditate the great truths. God's majesty is truly inspiring...": "如果你愿意，来这里和我一起坐下来冥想伟大的真理。上帝的威严真的令人敬畏...",
    "Do you have anything to say? Because unfortunately for you,": "你有什么要说的吗？因为很不幸，",
    "I don't any replies.": "我没有任何回答。",
}

# Remove None entries
ACOLYTE_TRANSLATIONS = {k: v for k, v in ACOLYTE_TRANSLATIONS.items() if v is not None}

MERCHANT_TRANSLATIONS = {
    # --- NPC names ---
    "[Chief Mahnsoo]": "[马恩苏会长]",
    "[Union Staff Kay]": "[工会职员凯]",
    "[Dyer's Student]": "[染色师的学生]",
    "[Guild Staff]": "[公会职员]",
    "[Kafra Employee]": "[卡普拉职员]",

    # --- Reborn path ---
    "Long time no see!": "好久不见！",
    "Hey, you didn't quit": "嘿，你没有放弃",
    "your business, did you?": "你的生意吧？",
    "What happened?": "发生了什么？",
    "Whoa...": "哇...",
    "You've actually been to Valhalla?! Wow, you've come a long way...": "你真的去过瓦尔哈拉？！哇，你走了很长的路...",
    "Hmmm...": "嗯嗯嗯...",
    "It seems that you're not ready to become a Merchant again. Go finish learning the Basic Novice Skills first.": "看来你还没准备好再次成为商人。先去学完初学者基本技能吧。",
    "Don't worry, we'll always have a Merchant position open for you. Just come back when you're ready, okay?": "别担心，我们总会为你保留一个商人的位置。准备好了就回来，好吗？",
    "I guess it's destiny that we meet like this once more. Alright. Once again, let me change you into a Merchant!": "我想这是命运让我们再次这样相遇。好的。让我再次把你变成商人！",
    "Ah~ How nostalgic. Just like old times! Alright, do your best!": "啊~真怀念。就像以前一样！好的，加油！",
    "^333333*Sigh*^000000": "^333333*叹气*^000000",
    "I'm so bored...": "我好无聊...",
    "When will I hear from my lovely Blossom?": "我什么时候才能收到我可爱的布洛瑟姆的消息？",

    # --- Already merchant ---
    "Hello there!": "你好！",
    "How do you like": "你觉得",
    "being a Merchant?": "当商人怎么样？",
    "Having a way with": "善于理财",
    "money certainly": "确实",
    "has its perks,": "有它的好处，",
    "does it not?": "不是吗？",

    # --- Non-novice ---
    "We Merchants hate people who are two faced. It's bad for business.": "我们商人讨厌两面三刀的人。这对生意不好。",
    "People who always try to take advantage of other people by selling things at a ridiculous price just so they can make money that they'll waste are the worst.": "那些总是试图通过以荒谬的价格卖东西来占别人便宜、只为了赚他们会浪费的钱的人是最糟糕的。",
    "Well, in any case, we only accept Novices for job changes to the Merchant class. But I appreciate your interest in what we do.": "好吧，无论如何，我们只接受初学者转职为商人。但我感谢你对我们工作的兴趣。",

    # --- Main menu ---
    "So, what brings you to": "那么，是什么让你来到",
    "the Merchant Association?": "商人协会的？",
    "Is there anything": "有什么",
    "I can help you with?": "我能帮你的吗？",
    "I want to be a Merchant.:Tell me about Merchants.:Tell me the requirements.:Nope.": "我想成为商人:告诉我关于商人的事:告诉我要求:不了",

    # --- Job change path ---
    "Do you want to": "你想",
    "be a Merchant?": "成为商人吗？",
    "Well...": "嗯...",
    "First, you have to be a Novice with Job Level 10. Once you do that, make sure you learn all of the Basic Skills.": "首先，你必须是职业等级10的初学者。做到这一点后，确保你学会所有基本技能。",
    "We're not just": "我们不仅仅是",
    "simple money makers!": "简单的赚钱者！",
    "We pride ourselves on having standards and only accepting qualified applicants!": "我们以拥有标准和只接受合格申请者为荣！",
    "Alright, you'll need to fill out this application and prepare 1,000 Zeny for your Membership Fee.": "好的，你需要填写这份申请表并准备1,000 Zeny的会员费。",
    "Oh...!": "哦...！",
    "If you don't have all the money,": "如果你没有足够的钱，",
    "I can just take 500 Zeny now.": "我现在可以只收500 Zeny。",
    "You can pay the rest after you": "你可以在",
    "pass the test and earn your": "通过考试并获得",
    "Merchant Guild License.": "商人公会执照后支付剩余的。",
    "So what do you think?": "你觉得怎么样？",
    "Are you ready to join now?": "你现在准备好加入了吗？",
    "Yes, I will.:Ummm, maybe later...": "是的，我加入:嗯，也许以后吧...",
    "Let me check if you": "让我检查一下你",
    "filled out everything": "是否填写了",
    "on your application form...": "申请表上的所有内容...",
    "That's a nice name.": "好名字。",
    "This application will": "这份申请将",
    "only be registered once": "只有在",
    "the Membership Fee is paid.": "会员费支付后才会注册。",
    "How do you wish to": "你想怎么",
    "handle the fee?": "处理费用？",
    "Pay all 1,000 Zeny now!:Two payments of 500 Zeny.:Quit": "现在支付全部1,000 Zeny！:分两次支付500 Zeny:退出",
    "Alright~": "好的~",
    "That's 1,000 zeny.": "这是1,000 Zeny。",
    "Excellent, excellent.": "太好了，太好了。",
    "It seems don't have enough zeny to pay all of the fee right now. Why don't you just pay 500 zeny now? Think about it.": "看来你现在没有足够的Zeny支付全部费用。你何不现在只付500 Zeny？考虑一下。",
    "Let's see...": "让我看看...",
    "That's 500 Zeny. Although I don't think splitting payment is a good idea for any Merchant, it's alright since you're still learning.": "这是500 Zeny。虽然我认为分期付款对任何商人来说都不是好主意，但既然你还在学习，就没关系了。",
    "It seems you don't have the funds to pay half of the membership fee. Please come back once you collect the zeny that you need.": "看来你没有足够的资金支付一半的会员费。请在收集到所需的Zeny后再回来。",
    "Feel free to return anytime": "随时欢迎回来",
    "when you are ready, alright?": "当你准备好的时候，好吗？",
    "You don't have enough zeny now? That's no problem. Take your time and come back when you're": "你现在没有足够的Zeny？没关系。慢慢来，准备好了",
    "ready, okay?": "再回来，好吗？",
    "Alright, you're now on the list of applicants. Ah, before I get started let me say just one thing.": "好的，你现在在申请者名单上了。啊，在我开始之前让我说一件事。",
    "There are some dumb and greedy people out there who do not know what it means to be a Merchant.": "外面有一些愚蠢贪婪的人不知道成为商人意味着什么。",
    "I hope you won't turn out to be like them, will you?": "我希望你不会变成像他们那样的人，对吧？",
    "Now, let me": "现在，让我",
    "explain what you": "解释一下你",
    "need to do for the": "需要做什么来通过",
    "Merchant License Test.": "商人执照考试。",

    # --- Delivery missions ---
    "First, get the delivery package from the storehouse, then go to the former Swordman's Association in Prontera.": "首先，从仓库取得快递包裹，然后去普隆德拉的前剑士协会。",
    "When you get there, visit the Kafra Employee stationed there. Her name is Blossom. Did you get": "到了那里后，找驻扎在那里的卡普拉职员。她的名字叫布洛瑟姆。你都",
    "all of that?": "记住了吗？",
    "First, get the delivery package from the storehouse, and then go to the Mage Guild in Geffen. When you get there, visit the Mage Guildsman in charge.": "首先，从仓库取得快递包裹，然后去吉芬的魔法师公会。到了那里后，找负责的魔法师公会成员。",
    "First, get the delivery package from the storehouse, and then go to Morroc. There you must find Java Dullihan, the dyemaker.": "首先，从仓库取得快递包裹，然后去摩洛哥。在那里你必须找到染色师贾瓦·杜利汉。",
    "He's a bit forgetful, so you should probably give the package to one of his students.": "他有点健忘，所以你最好把包裹交给他的一个学生。",
    "First, get the delivery package from the storehouse, and then give it to the Kafra Employee stationed on Byalan Island.": "首先，从仓库取得快递包裹，然后把它交给驻扎在比亚兰岛的卡普拉职员。",
    "Ummmm...": "嗯嗯嗯...",
    "And I also have": "我还有",
    "a bit of a personal": "一个小小的",
    "request for you.": "私人请求。",
    "Would you please give her this message when you deliver the package? Please~": "你能在送包裹的时候把这封信交给她吗？拜托~",
    "Don't forget your destination and the package's Serial Number. You will need to tell those to the storekeeper in the storehouse to the right of me.": "别忘了你的目的地和包裹的序列号。你需要把这些告诉我右边仓库里的仓库管理员。",
    "After the delivery, give the receipt to the storekeeper, and then come back and see me.": "送完货后，把收据交给仓库管理员，然后回来找我。",
    "Is that clear?": "清楚了吗？",
    "Alright, that's": "好的，这就是",
    "the spirit.": "精神。",
    "Take care!": "保重！",
    "Remember...": "记住...",
    "The package's": "包裹的",
    "Serial Number is": "序列号是",

    # --- Case 2: About Merchants ---
    "Merchant?": "商人？",
    "Well, we basically sell goods to make money. That is the way": "嗯，我们基本上是通过卖货来赚钱。这就是",
    "of the Merchant.": "商人之道。",
    "I guess we may not be the best at fighting, and we don't have many special attacks. We've got no healing skills...": "我想我们可能不是最擅长战斗的，我们没有很多特殊攻击。我们没有治疗技能...",
    "But we can buy goods at lower prices from NPC shops and sell them at a higher price to other people~": "但我们可以从NPC商店以更低的价格购买商品，然后以更高的价格卖给其他人~",
    "Our ultimate attack skill is 'Mammonite.' The strength of Mammonite comes from the anger": "我们的终极攻击技能是'金钱攻击'。金钱攻击的力量来自于",
    "when we're forced to throw away perfectly good zeny.": "当我们被迫扔掉完好的Zeny时的愤怒。",
    "Throwing away zeny like that": "像那样扔掉Zeny",
    "causes a deadly rage to well up in the heart of any Merchant!": "会在任何商人心中激起致命的愤怒！",
    "Just thinking about it": "光是想想",
    "makes my blood boil!": "就让我热血沸腾！",
    "Anyway, we can use most": "总之，我们可以使用大多数",
    "weapons except Bows, Rods, and Two-Handed Swords. But we can always sell those.": "武器，除了弓、法杖和双手剑。但我们总是可以卖掉那些。",
    "Yes...": "是的...",
    "We Merchants generally": "我们商人通常",
    "have money on our minds...": "脑子里想的都是钱...",

    # --- Case 3: Requirements ---
    "There are three conditions that must be fulfilled before you can become a Merchant.": "在你成为商人之前，必须满足三个条件。",
    "First, You have to be a Novice with Job Level 10, and have learned all of the Basic Skills.": "第一，你必须是职业等级10的初学者，并且学会了所有基本技能。",
    "Second, You have to pay a 1,000 Zeny Membership Fee. I believe any Merchant candidate should be able to earn 1,000 Zeny with ease.": "第二，你必须支付1,000 Zeny的会员费。我相信任何商人候选人都应该能轻松赚到1,000 Zeny。",
    "Third, there is a License Test to test your physical strength and sense of direction. You will deliver a package to a specific person in a specific location.": "第三，有一个执照考试来测试你的体力和方向感。你将把一个包裹送到特定地点的特定人手中。",

    # --- Congratulations ---
    "Congratulations!": "恭喜！",
    "I'm very pleased that you are joining the Merchant Guild and hope that you will play an active part in Rune-Midgarts' economy.": "我很高兴你加入了商人公会，希望你能在卢恩-米德加兹的经济中发挥积极作用。",
    "*Ahem* Aaaaand let me give you a little bit of money for delivering that message to Blossom for me.": "*咳咳* 还有，让我给你一点钱，感谢你帮我把信送给布洛瑟姆。",
    "I hope you'll help me again next time~": "希望你下次还能帮我~",
    "The message you were supposed to deliver as per my request? You've forgotten about that? Oh well. Good work!": "你应该按我的要求送的那封信？你忘了？哦好吧。干得好！",
    "Our goal is to control 20 % of the world's income! We're going to need young, eager people like you!": "我们的目标是控制世界20%的收入！我们需要像你这样年轻、热情的人！",
    "But overall, we'll also be happy just to make loads of money.": "但总的来说，我们也很乐意赚很多钱。",
    "But we all know that~": "但我们都知道这一点~",

    # --- Union Staff Kay ---
    "Heya pal.": "嘿，伙计。",
    "How ya doin'?": "你好吗？",
    "Hey you. We don't have any open positions for part time work. If you wanna earn some zeny, you'll hafta look elsewhere.": "嘿你。我们没有兼职的空缺。如果你想赚点Zeny，你得去别处找。",
    "Hey you. Yeah, you.": "嘿你。对，就是你。",
    "If you wanna restart the test, go visit Mahnsoo in the other room. Then we can talk.": "如果你想重新开始考试，去另一个房间找马恩苏。然后我们再谈。",
    "Alright! Everything looks perfect! I'll report your success to the guildmaster. Now go talk to Chief Mahnsoo, yeah?": "好的！一切看起来完美！我会向公会长报告你的成功。现在去找马恩苏会长谈谈，好吗？",
    "Hey there.": "嘿。",
    "what brings": "什么事",
    "you here?": "让你来这里？",
    "My Merchant License test.:I'm looking for part time work.:Nothing.": "我的商人执照考试:我在找兼职工作:没事",
    "I see.": "我明白了。",
    "Alright.": "好的。",
    "So what's": "那你",
    "your name?": "叫什么名字？",
    "Huh. Your name's not on my list. Did you apply for the job change quest or what?": "嗯。你的名字不在我的名单上。你申请了转职任务了吗？",
    "You gotta apply first by talking to Chief Mahnsoo in the center": "你得先去和中央的马恩苏会长谈话来申请",
    "of this building, okay?": "在这栋建筑里，好吗？",
    "Alright, there you go. Lemme give you the package. Now, choose the destination of the delivery.": "好的，给你。让我给你包裹。现在，选择送货目的地。",
    "Prontera.:Geffen.:Morocc.:Byalan Island.": "普隆德拉:吉芬:摩洛哥:比亚兰岛",
    "Okay, now you need to give me the package's Serial Number. If you wanna cancel, just enter '0', alright?": "好的，现在你需要给我包裹的序列号。如果你想取消，输入'0'就行，好吗？",
    "Are you sure that you wanna cancel?": "你确定要取消吗？",
    "Yes.:Let me try again.": "是的:让我再试一次",
    "Alright, we'll cancel for now.": "好的，我们现在取消。",
    "Hey hey. That number's not valid! Enter a value from 1000000 to 5000000. got it?": "嘿嘿。那个号码无效！输入1000000到5000000之间的值，明白了吗？",
    "Alright. Take this package and guard it with your life until it's safely delivered to the customer. Don't lose this thing, got it?": "好的。拿着这个包裹，用你的生命保护它，直到安全送到客户手中。别弄丢了，明白吗？",
    "Well then, I wish you luck. Remember, you gotta bring me": "那么，祝你好运。记住，你得给我带",
    "a receipt once you finish the delivery, okay?": "送完货后的收据回来，好吗？",
    "Part time job? Sorry pal, no jobs yet. The Paymaster's department can never balance our budget...": "兼职？抱歉伙计，还没有工作。财务部门永远无法平衡我们的预算...",
    "Nothing, eh?": "没事，嗯？",
    "I guess you enjoy": "我猜你喜欢",
    "bothering people for": "无缘无故",
    "no reason then, yeah?": "打扰别人，是吧？",
}

THIEF_TRANSLATIONS = {
    # --- NPC names ---
    "[Thief Guide]": "[盗贼向导]",
    "[Comrade]": "[同志]",
    "[Brad]": "[布拉德]",
    "[Mr. Irrelevant]": "[无关先生]",

    # --- Reborn path ---
    "Huh? Do I know you? It's creepy that you seem so familiar. You don't have a twin, do you?": "嗯？我认识你吗？你看起来这么面熟，真让人毛骨悚然。你没有双胞胎吧？",
    "What, do you want to be a Thief? I'm sorry, but you look like you need more training.": "什么，你想成为盗贼？抱歉，但你看起来需要更多训练。",
    "Take your time and learn all the Basic Skills, will you? Well then, see you later~!": "慢慢来，学完所有基本技能，好吗？那么，回头见~！",
    "Well, I got this feeling like you've been through a lifetime of fighting, so I'm promoting you to a Thief right this minute. I better give you tough guys what you want...": "嗯，我有种感觉你已经经历了一辈子的战斗，所以我现在就把你提升为盗贼。我最好给你们这些硬汉想要的...",
    "Since you've become a Thief, live as a Thief. Now, go for it! Next~": "既然你已经成为了盗贼，就像盗贼一样生活吧。现在，加油！下一个~",
    "Hey, dude.": "嘿，兄弟。",
    "Hey, baby~": "嘿，美女~",
    "Hey, baby.": "嘿，美女。",
    "...Hey! You look too goody-goody to want to be a Thief!! Now scram, I'm busy. Next!": "...嘿！你看起来太正经了，不像是想当盗贼的！！快走，我很忙。下一个！",

    # --- Non-thief classes ---
    "What the heck...?": "搞什么...？",
    "Huh.": "嗯。",
    "Now, that's": "嗯，那是",
    "a big sword.": "一把大剑。",
    "So...": "所以...",
    "Trying to make": "想要弥补",
    "up for something": "什么",
    "...Buddy?": "...伙计？",
    "What's a Mage doin' here? Shouldn't you be doing card tricks elsewhere? Oh well, it's a free country...": "魔法师来这里干什么？你不应该去别处变魔术吗？算了，这是个自由的国家...",
    "Oh wait,": "哦等等，",
    "it's not...": "不是...",
    "Get outta here!": "快出去！",
    "Man, shouldn't you": "老兄，你不应该",
    "Archers be playing": "弓箭手们去",
    "in the forest": "森林里",
    "or something?": "玩耍什么的吗？",
    "You know we all steal for a living, right? What are you doing in this kinda place, Acolyte?": "你知道我们都是靠偷窃为生的，对吧？你在这种地方做什么，侍祭？",
    "You're a Merchant,": "你是商人，",
    "right? Why are you": "对吧？你为什么",
    "walking into a den": "走进一个",
    "of Thieves?!": "盗贼的巢穴？！",
    "It's like you're begging": "你简直是在求",
    "us to steal from you!": "我们偷你的东西！",
    "Come on, hurry and": "快点，赶紧",
    "get outta here~": "离开这里~",
    "Oh my God...": "天哪...",
    "Am I dying?": "我要死了吗？",
    "Why else would a Priest come here? I guess I better start confessing all of my misdeeds.": "不然牧师为什么会来这里？我想我最好开始忏悔我所有的恶行了。",
    "Didn't you use to be one of us?! Man, you changed. You seem real dangerous now...": "你以前不是我们中的一员吗？！老兄，你变了。你现在看起来真的很危险...",
    "Man, you got real cool all of a sudden! You must have some skills I can only dream of!": "老兄，你突然变得好酷！你一定有一些我只能梦想的技能！",
    "*Sigh* Look, there's really no need for you to be in this kind of place. You oughta go where you ought to go.": "*叹气* 听着，你真的没有必要在这种地方。你应该去你该去的地方。",

    # --- Already thief ---
    "If you have a problem, feel free to speak to me anytime, alright?": "如果你有问题，随时可以来找我谈，好吗？",

    # --- Mushroom check ---
    "Hmmm?": "嗯？",
    "You gathered Mushrooms for": "你为盗贼考试",
    "the Thief test, right?": "收集了蘑菇，对吧？",
    "Here, talk to the other guy right next to me. He's the one in charge of checking your Mushrooms.": "来，和我旁边的那个人谈谈。他负责检查你的蘑菇。",
    "So how was the": "蘑菇农场",
    "Mushroom Farm?": "怎么样？",
    "Have any fun?": "好玩吗？",
    "Yeah, kinda Cool.:It was horrible.": "是的，还挺酷的:太可怕了",
    "Heh heh! That's a good attitude. In our line of work, you gotta enjoy getting your hands dirty, one way or another.": "嘿嘿！态度不错。在我们这行，你得享受弄脏双手的过程，不管用什么方式。",
    "Yeah? I've been there too, so I can see why that place isn't everyone's cup of tea. Still, being a Thief isn't all glamour and trendy night life.": "是吗？我也去过那里，所以我能理解为什么那个地方不是每个人都喜欢的。不过，当盗贼也不全是光鲜亮丽的夜生活。",

    # --- Test explanation (repeated) ---
    "Hey, whaddya doin' here? Aren't you supposed to be gathering Mushrooms? Or did you need it explained to you again?": "嘿，你在这里干什么？你不是应该去收集蘑菇吗？还是你需要我再解释一遍？",
    "Yes.:No, that's okay.": "是的:不，没关系",
    "*Sigh* Well, there's always one in the bunch. Alright, listen carefully.": "*叹气* 嗯，总有这样的人。好吧，仔细听。",
    "Alright, for your test, you gotta steal Mushrooms from a farm. Don't worry, the guy who owns the farm deserves to be robbed.": "好的，你的考试是从农场偷蘑菇。别担心，农场的主人活该被抢。",
    "Anyway, you gotta gather two kinds of Mushrooms: ^0000FFOrange Net Mushrooms^000000 and ^0000FFOrange Gooey Mushrooms^000000.": "总之，你需要收集两种蘑菇：^0000FF橙色网状蘑菇^000000和^0000FF橙色粘液蘑菇^000000。",
    "Be careful, since there are monsters are the farm that are there to protect the Mushrooms. So this will be no walk in the park.": "小心，农场里有怪物在保护蘑菇。所以这不会是轻松的事。",
    "When you come back here after gathering Mushrooms, you'll be graded on the Mushrooms you've collected.": "收集完蘑菇回来后，你将根据收集的蘑菇获得评分。",
    "Each Orange Net Mushroom gets you 3 points, and you get 1 point for each Orange Gooey Mushroom. You need a total of 25 points to pass the test.": "每个橙色网状蘑菇得3分，每个橙色粘液蘑菇得1分。你需要总共25分才能通过考试。",
    "Go outside and keep going ahead toward the Eastern Field of the Pyramids. Then you will see one of our comrades between two columns.": "出去后一直向金字塔东部的田野走。然后你会在两根柱子之间看到我们的一个同伴。",
    "Speak to that guy, and he'll take you to the farm through the backdoor.": "和那个人说话，他会带你从后门进入农场。",
    "On that field, I think his coordinates are '^FF0000141, 125^000000.' Just type ^3355FF/where^000000 in the right side of your chat box to check your present coordinates.": "在那片田野上，我记得他的坐标是'^FF0000141, 125^000000。'只需在聊天框右侧输入^3355FF/where^000000来查看你当前的坐标。",
    "Huh. For a second there, I thought you had something really important to tell me.": "嗯。有那么一瞬间，我以为你有什么真正重要的事要告诉我。",

    # --- Main dialogue ---
    "What brings you down": "什么风把你吹到",
    "here to this rathole?": "这个老鼠洞来了？",
    "Ah...": "啊...",
    "You came back.": "你回来了。",
    "Are you sure you're": "你确定你",
    "ready to try again?": "准备好再试一次了吗？",
    "Hey, I came here to be a Thief!:Nah, I'm just looking around.": "嘿，我来这里是为了成为盗贼！:不，我只是看看",
    "Heh, I like your confidence. Still, you know being a Thief isn't all what it's cracked up to be.": "嘿，我喜欢你的自信。不过，你知道当盗贼并不像传说中那么好。",
    "Still...": "不过...",
    "Do you really": "你真的",
    "want to be": "想成为",
    "a Thief?": "盗贼吗？",
    "Yeah.:No, just wasting your time.:Why did you become a Thief?": "是的:不，只是浪费你的时间:你为什么成为盗贼？",
    "Really...": "真的...",
    "Yeah...": "是啊...",
    "I can see that.": "我看得出来。",
    "Me...?": "我...？",
    "I had no choice at the time. It was either steal or starve. But it's not like I need to give you my life story.": "当时我别无选择。要么偷，要么饿死。但我也不需要给你讲我的人生故事。",
    "So do you want to": "那你想",
    "apply to become": "申请成为",
    "a Thief or not?": "盗贼还是不想？",
    "Yes, I will.:I'm too scared to be a Thief!": "是的，我要:我太害怕当盗贼了！",
    "Alright, tell": "好的，告诉",
    "me your name.": "我你的名字。",
    "What kind of name is \" + strcharinfo(0) + \"? Anyway, give me a second.": None,  # dynamic
    "Alright, your registration has been processed. Okay, you can begin your test if you're ready.": "好的，你的注册已经处理完毕。好了，如果你准备好了就可以开始考试。",
    "Yeah, I'm ready.:No, I'm not ready yet.": "是的，我准备好了:不，我还没准备好",
    "Not ready?": "没准备好？",
    "How can you": "你怎么能",
    "not be ready?!": "没准备好？！",
    "Too scared?!?": "太害怕了？！？",
    "Hahahahahahah!": "哈哈哈哈哈哈哈！",
    "Oh, please...!": "哦，拜托...！",
    "That's hilarious!": "太搞笑了！",
    "Okay...": "好的...",
    "Give me": "给我",
    "one second.": "一秒钟。",
    "Your name is...": "你的名字是...",
    "Isn't that cute? I can see you're ambitious, but you gotta learn all of the Basic Skills before you can become a Thief.": "真可爱？我能看出你很有野心，但你得先学完所有基本技能才能成为盗贼。",
    "Alright. I looked at your Felony Record, and you seem to have a very interesting history. You might have what it takes to be a Thief.": "好的。我看了你的犯罪记录，你似乎有一段非常有趣的历史。你可能有成为盗贼的资质。",
    "Because I feel like it, I now decree that you have passed this interview. Good work!": "因为我高兴，我现在宣布你通过了这次面试。干得好！",
    "Now, your actual abilities will need to be tested. Do you know anything about the test?": "现在，你的实际能力需要被测试。你对考试了解多少？",
    "Yes, I do.:Sorry, I don't.": "是的，我了解:抱歉，我不了解",
    "Oh yeah? Well, this makes things a lot easier.": "哦是吗？那这就简单多了。",
    "Alright, let me inform you then. Listen carefully. This test decides if you are worthy of becoming a Thief.": "好的，那让我告诉你。仔细听。这个考试决定你是否有资格成为盗贼。",
    "You will be sneaking to Shibu's Farm. He is the worst Merchant, in terms of character, in Morocc.": "你将潜入希布的农场。他是摩洛哥品行最差的商人。",
    "Alright, for your test, you gotta steal Mushrooms from his farm. Don't worry, that guy deserves to be robbed.": "好的，你的考试是从他的农场偷蘑菇。别担心，那家伙活该被抢。",
    "Don't forget to make plans and prepare yourself before you go inside the Mushroom Farm. Move as quickly as you can and try not to get killed, alright?": "进入蘑菇农场之前别忘了制定计划并做好准备。尽可能快地行动，尽量不要被杀死，好吗？",

    # --- Comrade (mushroom checker) ---
    "We don't have any special events yet. Come some other time when there's news, alright?": "我们还没有什么特别活动。有消息的时候再来吧，好吗？",
    "Um...": "嗯...",
    "You don't look": "你看起来",
    "like a Thief.": "不像盗贼。",
    "What the heck are": "你到底在",
    "you doing here anyway?": "这里做什么？",
    "What's the matter? If you want to be a Thief, speak to the girl beside me.": "怎么了？如果你想成为盗贼，和我旁边的女孩说话。",
    "Did you pass the interview?": "你通过面试了吗？",
    "Then what are you waiting for?": "那你还在等什么？",
    "Ah, the guide told me about you. So, let me check your mushrooms...": "啊，向导告诉我关于你的事了。那么，让我检查一下你的蘑菇...",
    "What the hell...": "搞什么...",
    "You don't have any Mushrooms at all! Go back and get them. Otherwise, you won't pass the test and become a Thief!": "你一个蘑菇都没有！回去拿。否则，你不会通过考试成为盗贼的！",
    "First, let me check the Orange Net Mushrooms you got.": "首先，让我检查一下你得到的橙色网状蘑菇。",
    "Now I'll just check your Orange Gooey Mushrooms. That's \" + countitem(1070) + \" you gathered.": None,  # dynamic
    "So that would": "那么这将",
    "bring your total to...": "使你的总分达到...",
    "You got more": "你得到了超过",
    "than 25 points!": "25分！",
    "Awesome!": "太棒了！",
    "Exactly 25 points!": "正好25分！",
    "You did it! Badass!": "你做到了！太厉害了！",
    "Definitely less than the 25 points you need to pass. Go out there and get me more Mushrooms!": "绝对不到通过所需的25分。出去给我拿更多蘑菇来！",
    "You have passed the official Thief Test. You are now one of us.": "你已经通过了正式的盗贼考试。你现在是我们中的一员了。",
    "Congratulations on becoming a Thief! From now, be an honorable representative of the Thief's Guild.": "恭喜你成为盗贼！从现在起，做盗贼公会的光荣代表。",
    "If you bring disgrace to our guild, you will be killed. I expect you to bring our comrades pride.": "如果你给我们的公会带来耻辱，你将被杀死。我期望你给我们的同伴带来骄傲。",
    "*Ahem* Welcome to the Guild, comrade! I'm Brad, and I'm in charge of human resources here.": "*咳咳* 欢迎加入公会，同志！我是布拉德，我负责这里的人事。",
    "Here is a small subsidy for a Newbie like you. Spend it whereever you want. Alright then, I'll see you around~": "这是给像你这样的新人的一点补贴。随便花吧。好了，回头见~",

    # --- Mr. Irrelevant ---
    "Ah, I see that you are now a Thief. I always knew you'd join us.": "啊，我看到你现在是盗贼了。我一直知道你会加入我们的。",
    "Stealing from a Mushroom farm is too easy for you now. You should build up your skills and master our craft.": "从蘑菇农场偷东西对你来说现在太简单了。你应该提升你的技能并精通我们的手艺。",
    "I could use a good, hard drink.": "我需要来一杯烈酒。",
    "Gimme your money.": "把你的钱给我。",
    "Kidding, I'm off the clock.": "开玩笑的，我下班了。",
    "WHO YOU CALLING A PSYCHO?!?!": "你说谁是疯子？！？！",
    "I've got nothing to say to you. Would you mind leaving me alone?": "我没什么要对你说的。你能不能别烦我？",
    "Today looks like a good day to go to the pyramids and hunt with some of my friends.": "今天看起来是个好日子，可以和朋友们去金字塔打猎。",
    "Hahahahaha~!": "哈哈哈哈哈~！",
    "You haven't": "你还没有",
    "passed the test yet?": "通过考试吗？",
    "Alright, I'll let you in...": "好吧，我让你进去...",
    "You've come to take the test, right? I can see in your eyes that you know something.": "你是来参加考试的，对吧？我能从你的眼神中看出你知道些什么。",
    "There is this strange smell coming from... You. Now why would that be?": "有一股奇怪的气味来自...你。这是为什么呢？",
    "Hey Novice! Why don't you join the ranks of the Thief Guild? You newbies are always welcome to join us and our selfish cause.": "嘿初学者！为什么不加入盗贼公会的行列呢？你们新人随时欢迎加入我们和我们自私的事业。",
    "You can get more information in the Underground Room in the Pyramid 1 BF.": "你可以在金字塔地下1层的地下室获得更多信息。",
}

# Remove None entries
THIEF_TRANSLATIONS = {k: v for k, v in THIEF_TRANSLATIONS.items() if v is not None}


# ---------------------------------------------------------------------------
# File Definitions
# ---------------------------------------------------------------------------

JOB_FILES = [
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'swordman.txt'),
        'translations': SWORDMAN_TRANSLATIONS,
    },
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'mage.txt'),
        'translations': MAGE_TRANSLATIONS,
    },
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'archer.txt'),
        'translations': ARCHER_TRANSLATIONS,
    },
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'acolyte.txt'),
        'translations': ACOLYTE_TRANSLATIONS,
    },
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'merchant.txt'),
        'translations': MERCHANT_TRANSLATIONS,
    },
    {
        'path': os.path.join('npc', 'pre-re', 'jobs', '1-1', 'thief.txt'),
        'translations': THIEF_TRANSLATIONS,
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def restore_files():
    """Restore original English files from npc_backup_en/."""
    print("Restoring original English files from backups...")
    restored = 0
    for job in JOB_FILES:
        filepath = os.path.join(PROJECT_ROOT, job['path'])
        rel = os.path.relpath(filepath, PROJECT_ROOT)
        backup_path = os.path.join(PROJECT_ROOT, 'npc_backup_en', rel)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, filepath)
            print(f"  [restored] {rel}")
            restored += 1
        else:
            # Also check without the 'npc/' prefix (legacy backup structure)
            alt_rel = rel
            if alt_rel.startswith('npc' + os.sep):
                alt_rel = alt_rel[len('npc' + os.sep):]
            alt_backup = os.path.join(PROJECT_ROOT, 'npc_backup_en', alt_rel)
            if os.path.exists(alt_backup):
                shutil.copy2(alt_backup, filepath)
                print(f"  [restored] {rel} (from legacy backup)")
                restored += 1
            else:
                print(f"  [SKIP] no backup found for {rel}")
    print(f"Restored {restored}/{len(JOB_FILES)} files.")
    return restored


def main():
    dry_run = '--dry-run' in sys.argv
    restore = '--restore' in sys.argv

    print("rAthena Job Script Translator (EN -> CN)")
    print("=" * 50)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Files to process: {len(JOB_FILES)}")
    print()

    if restore:
        restore_files()
        if dry_run:
            print("\n(Restore only, not re-translating in dry-run mode)")
            return
        print()

    if dry_run:
        print("[DRY RUN] No files will be modified.\n")

    success = 0
    for job in JOB_FILES:
        filepath = os.path.join(PROJECT_ROOT, job['path'])
        if translate_file(filepath, job['translations'], dry_run=dry_run):
            success += 1
        print()

    print("=" * 50)
    print(f"Done. {success}/{len(JOB_FILES)} files processed.")
    if dry_run:
        print("(Dry run - no files were modified)")


if __name__ == '__main__':
    main()
