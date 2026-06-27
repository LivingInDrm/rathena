#!/usr/bin/env python3
"""
Translate all Renewal Job Quest NPC scripts (npc/re/jobs/) to Chinese.

Reads from npc_backup_en/ (English originals), translates mes/select strings,
writes GBK-encoded output to npc/re/jobs/.

Usage:
    python tools/translate_re_jobs.py [--dry-run] [--file=PATTERN]
"""

import re
import sys
from pathlib import Path

RATHENA_ROOT = Path(r"D:\Projects\rathena")
BACKUP_DIR   = RATHENA_ROOT / "npc_backup_en" / "re" / "jobs"
OUTPUT_DIR   = RATHENA_ROOT / "npc" / "re" / "jobs"

MES_RE     = re.compile(r'^(\s*mes\s+)"([^"]*)"(;.*)?$')
SELECT_RE  = re.compile(r'(\bselect\s*\(\s*")((?:[^"\\]|\\.)*?)(")')

# ─── Translation Dictionaries ────────────────────────────────────────────────
# Format: { "English text": "Chinese text" }
# NPC name headers like [Name] are also translated.

# Common NPC name translations used across files
NPC_NAMES = {
    "[Swordman]": "[剑士]",
    "[Swordman Guildsman]": "[剑士公会会员]",
    "[Archer Guildsman]": "[弓箭手公会会员]",
    "[Mage Guildsman]": "[魔法师公会会员]",
    "[Chief Mahnsoo]": "[会长满秀]",
    "[Guildsman Mahnsoo]": "[公会会员满秀]",
    "[Thief Guide]": "[盗贼向导]",
    "[Thief Guildsman]": "[盗贼公会会员]",
    "[Commander of Thief Guild]": "[盗贼公会指挥官]",
    "[Brad]": "[布拉德]",
    "[Father Mareusis]": "[马鲁修斯神父]",
    "[Father Rubalkabara]": "[鲁巴尔卡巴拉神父]",
    "[Mother Mathilda]": "[玛蒂尔达修女]",
    "[Father Yosuke]": "[洋介神父]",
    "[Rune Knight Manuel]": "[符文骑士曼努埃尔]",
    "[Rune Leader Jungberg]": "[符文领袖荣格伯格]",
    "[Rune Knight Staff]": "[符文骑士工作人员]",
    "[Captain Tigris]": "[提格里斯队长]",
    "[Rune Knight, Lunarea]": "[符文骑士 露娜蕾亚]",
    "[Rune Knight, Renoa]": "[符文骑士 蕾诺亚]",
}


def build_swordman_dict():
    mes = {
        # Reborn path
        "It...": "这……",
        "Can't be...": "不可能……",
        "You've been reborn, haven't you?": "你已经转生了，对吧？",
        "I see you're retreading the path of the Swordman! Once you've gotten used to brandishing a sword, you can never go back!!": "我看你又踏上了剑士之路！一旦习惯了挥剑的感觉，就再也回不去了！！",
        "Hmm? Ah, you must first master the Basic Skills before you are ready to become a Swordman.": "嗯？啊，你必须先掌握基本技能，才能成为剑士。",
        "Come back to me when you have finished learning the Basic Novice Skills.": "等你学完初学者基本技能后再来找我吧。",
        "Excellent! Let me promote you to a Swordman right away!": "太好了！让我立刻将你晋升为剑士！",
        "Hmm... You look like a well-experienced Swordman. Still, I'm sure that you must train to improve your skills and gain strength!": "嗯……你看起来像一位经验丰富的剑士。不过，我相信你还需要继续修炼来提升技能和力量！",
        "Hm...?": "嗯……？",
        "You're a reborn": "你是一位转生的",
        "warrior, aren't you?": "战士，对吧？",
        "Hmmm...": "嗯嗯……",
        "It seems that being": "看起来成为",
        "a Swordman is not part": "剑士并不是",
        "of your destiny. I'm sorry,": "你的命运。很抱歉，",
        "but it seems there is nothing": "我恐怕帮不了",
        "I can do for you.": "你什么。",
        # Normal path
        "This is the Swordman Guild.": "这里是剑士公会。",
        "Why are you here?": "你来这里做什么？",
        "So you wish to know more about the mighty Swordman? Okay!": "你想了解更多关于强大的剑士的事？好的！",
        "The most distinctive feature of the Swordman is that the Swordman can show us his/her real abilities in close combat.": "剑士最显著的特点是能在近战中展现出真正的实力。",
        "There are three reasons!": "原因有三！",
        "First, Swordman has higher HP than other jobs.": "第一，剑士比其他职业拥有更高的HP。",
        "Second, except for Bows and Rods, Swordman can use all other weapons so they can fight at their optimal ability.": "第二，除了弓和法杖之外，剑士可以使用所有其他武器，因此能发挥最佳战斗力。",
        "And third, most of the skills of the Swordman give powerful physical attacks.": "第三，剑士的大部分技能都能造成强力的物理攻击。",
        "Though I gave you a simple explanation, I believe you understand the core meaning of what it is to be a Swordman.": "虽然我只是简单地解释了一下，但我相信你已经理解了成为剑士的核心意义。",
        "In my opinion, Swordman is the best job ever!": "在我看来，剑士是最好的职业！",
        "You are already an excellent Swordman, aren't you?": "你已经是一名优秀的剑士了，不是吗？",
        "Just devote yourself to be a great Swordman.": "好好努力，成为一名伟大的剑士吧。",
        "You already have one of the other jobs, don't you?": "你已经有其他职业了，不是吗？",
        "You've gone too far with that joke.": "这个玩笑开得太过了。",
        "I'm sorry to tell you this but to be a Swordman, you must reach at least ^4A4AFFJob Level 10^000000.": "很抱歉告诉你，要成为剑士，你必须达到至少^4A4AFF职业等级10^000000。",
        "and ^4A4AFFBasic Skill Level 9^000000.": "以及^4A4AFF基本技能等级9^000000。",
        "Want to be a Swordman without having the minimum requirement?": "想成为剑士却连最低要求都达不到？",
        "Do you think being a Swordman is that easy?": "你以为成为剑士那么容易吗？",
        "Hmm, both your Job Level and Basic Skill Level check out.": "嗯，你的职业等级和基本技能等级都达标了。",
        "Good. Do you want to be a Swordman right away?": "很好。你想现在就成为剑士吗？",
        "Yeah. Prudent decision is needed for choosing a job.": "是啊。选择职业确实需要慎重考虑。",
        "But I feel sorry... that you consider it again after overcoming all the hardships....": "但我觉得很遗憾……在克服了所有困难之后你却要再考虑一下……",
        "Congratulations! From now on, you are going to live a Swordman's life!": "恭喜你！从现在起，你将过上剑士的生活！",
        "Let's do it right now!": "让我们现在就开始吧！",
        "Congratulations again for being a Swordman and I hope that you participate in many activities for the revival of our guild.": "再次恭喜你成为剑士，我希望你能积极参与公会的各项活动，为公会的复兴做出贡献。",
    }
    sel = {
        "Tell me about being a Swordman.:I want to be a Swordman.:Nothing.": "告诉我关于剑士的事。:我想成为剑士。:没什么。",
        "Yes, I do.:I'll consider it again.": "是的，我愿意。:让我再考虑一下。",
    }
    return mes, sel


def build_archer_dict():
    mes = {
        "Hey, I know you.": "嘿，我认识你。",
        "You took this test": "你以前参加过",
        "before, didn't you?": "这个测试，对吧？",
        "Ah, you must have been": "啊，你一定去过瓦尔哈拉",
        "to Valhalla and been reborn.": "然后转生了。",
        "Wow, that's so impressive!": "哇，太厉害了！",
        "Err...": "呃……",
        "You'd better learn all the Basic Skills first before you can become an Archer.": "你最好先学会所有基本技能，然后才能成为弓箭手。",
        "Alright, see you later.": "好的，回头见。",
        "Well then. I don't": "那么，我不需要",
        "need to say anything else.": "多说什么了。",
        "I know you'll make a great Archer...": "我知道你会成为一名出色的弓箭手……",
        "Although there's no special": "虽然这次没有特别的",
        "reward for you this time, I hope you understand. Take care of yourself.": "奖励给你，但希望你能理解。保重。",
        "Oh...?": "哦……？",
        "Hey, what are": "嘿，你在",
        "you doing here...?": "这里做什么……？",
        "I can tell that you're not cut out to be an Archer. It sort of feels like you're meant to do": "我能看出你不适合当弓箭手。感觉你注定要做",
        "something else...": "别的事情……",
        "Nice to meet you. How may I help you?": "很高兴认识你。有什么我能帮你的吗？",
        "Haha, you are kidding me...": "哈哈，你在开我玩笑吧……",
        "I feel sorry but only Novices can change their job.": "很抱歉，只有初学者才能转职。",
        "You already have your own decent job, don't you?": "你已经有自己的职业了，不是吗？",
        "Well, you're not at the right skill level.": "嗯，你的技能等级还不够。",
        "Your job level must be at least ^4A4AFF10^000000 and your Basic Skill level should reach ^4A4AFFlevel 9": "你的职业等级必须至少达到^4A4AFF10^000000，基本技能等级应该达到^4A4AFF9级",
        "Because an Archer needs extremely high concentration, so we do not accept those who have little patience.": "因为弓箭手需要极高的专注力，所以我们不接受缺乏耐心的人。",
        "Your Basic Skill is now enough..": "你的基本技能已经足够了……",
        "....Hm~~ so you are now ready to be an Archer. I will take the step right away.": "……嗯~~看来你已经准备好成为弓箭手了。我马上为你办理。",
        "Congratulations! You are now an Archer! Also, we hope that you actively participate in many programs for the revival of the Archer Guild.": "恭喜你！你现在是一名弓箭手了！同时，我们希望你能积极参与弓箭手公会的各项复兴活动。",
        "Ah, items have arrived from the Production Department. Here, take these! These are all yours!": "啊，生产部门送来了物资。来，拿着！这些都是你的！",
        "Having a bow and arrows, now you became a real Archer.": "有了弓和箭，你现在是一名真正的弓箭手了。",
        "If you open the arrow container, there are arrows in it and then you can equip them.": "打开箭矢容器，里面有箭矢，然后你就可以装备它们了。",
        "Well, I expect to hear better news from you. It's time to say goodbye.": "好了，期待听到你更好的消息。是时候说再见了。",
        "Bye.": "再见。",
        "An Archer has skills using a bow and has various talents.": "弓箭手拥有使用弓的技能和各种才能。",
        "The greatest ability of an Archer is attacking enemies from a long distance.": "弓箭手最大的能力是从远距离攻击敌人。",
        "Although an Archer has weaker HP, he or she can shoot enemies at a long range,": "虽然弓箭手的HP较低，但他/她可以在远距离射击敌人，",
        "so an Archer is safer in a real battle.": "所以弓箭手在实战中更加安全。",
        "Although an Archer in Ragnarok has lower HP, he or she has high accuracy and attack rate so that the archer can kill monsters before they get close to an Archer.": "虽然仙境传说中的弓箭手HP较低，但他/她拥有高命中率和攻击速度，可以在怪物靠近之前将其消灭。",
        "^8C2121An Archer can change jobs to a Hunter.^000000": "^8C2121弓箭手可以转职为猎人。^000000",
        "^8C2121Other than Hunter, if you are a man, you can change your job to Bard and if you are a woman, you can change your job to Dancer.^000000": "^8C2121除了猎人之外，如果你是男性，可以转职为诗人；如果你是女性，可以转职为舞娘。^000000",
        "If you have any questions, feel free to come and ask me.": "如果你有任何问题，随时来问我。",
    }
    sel = {
        "I want to be an Archer.:I need the requirements, please.:Nothing, thanks.": "我想成为弓箭手。:请告诉我要求。:没什么，谢谢。",
    }
    return mes, sel


def build_mage_dict():
    mes = {
        "Whoa, long time no see! But weren't you supposed to be dead?": "哇，好久不见！但你不是应该已经死了吗？",
        "Ah, you must have been reborn. Well, I'm glad to have you back.": "啊，你一定是转生了。嗯，很高兴你回来了。",
        "I'm sorry, but I don't think you're ready to learn magic yet. Why don't you go finish learning the Basic Skills first?": "抱歉，我觉得你还没准备好学习魔法。你先去把基本技能学完吧？",
        "Take your time. The more you learn, the more ready you'll be to learn magic again.": "慢慢来。你学得越多，就越能为重新学习魔法做好准备。",
        "Well, since you have passed the Mage test once, I will not question your qualification. You want to have your magic skills back immediately, don't you?": "嗯，既然你已经通过了一次魔法师测试，我就不质疑你的资格了。你想立刻恢复魔法技能，对吧？",
        "Wow, for some reason, you look way better than you did before. Anyway, I believe you will do a better job being a Mage as well.": "哇，不知为何，你看起来比以前好多了。总之，我相信你会成为一名更出色的魔法师。",
        "Is there anything more I can help you with? If not, why don't you go test your skills? The world is waiting for you~!": "还有什么我能帮你的吗？如果没有，你何不去试试你的技能？世界在等着你~！",
        "What, are you interested in the Mage guild? I didn't want to tell you this, but you don't belong here.": "什么，你对魔法师公会感兴趣？我本不想告诉你这个，但你不属于这里。",
        "I am not sure why you're still standing in front of me, but I can tell that you're not meant to be a Mage.": "我不确定你为什么还站在我面前，但我能看出你不适合当魔法师。",
        "Hey, haven't you realized? You're already a Mage, silly!": "嘿，你还没意识到吗？你已经是魔法师了，傻瓜！",
        "One of these days you'll realize the power inside of you when you can make Fire with your mind!": "总有一天你会意识到你内心的力量，当你能用意念制造火焰的时候！",
        "Hey~ C'mon. Quit playing games. You can't be a Mage because you already have another Job.": "嘿~别闹了。你不能成为魔法师，因为你已经有其他职业了。",
        "Hey?": "嘿？",
        "Wanna be a Mage? Eh...": "想成为魔法师？嗯……",
        "Hey, look at you! You're kinda cute~! Not my type though...": "嘿，看看你！你还挺可爱的~！不过不是我的类型……",
        "Oooh, you're such a hot babe~!": "哦哦，你真是个大美人~！",
        "I like girls like you~": "我喜欢你这样的女孩~",
        "Right, you said that you wanna be a Mage?": "对了，你说你想成为魔法师？",
        "Whaaaaat~?! Right after you tell me that you wanna become a Mage, you change your mind?! Be a bit more decisive!": "什么~？！你刚告诉我你想成为魔法师，就改主意了？！果断一点好不好！",
        "Oh, man your Basic Skill Level doesn't reach enough to be a Mage.": "哦，天哪，你的基本技能等级还不够成为魔法师。",
        "Go back and level up your Basic Skill.": "回去把基本技能练上来吧。",
        "Hmm I can see that you've tried hard in your own way. Though it seems to be a little clumsy, but well I think it's okay!": "嗯，我能看出你以自己的方式努力过了。虽然看起来有点笨拙，但我觉得还行！",
        "Good! Always sticking to the basics is the best! I will transform you right away.": "好！始终坚持基础是最好的！我马上为你转职。",
        "Hahh..! You are now a Mage, one of our colleagues!": "哈……！你现在是魔法师了，是我们的同事了！",
        "We welcome you to the Mage Guild, our new friend!": "欢迎来到魔法师公会，我们的新朋友！",
        "'Welcome to the Mage Guild~'": "'欢迎来到魔法师公会~'",
        "Congratulations on becoming a member of the Mage Guild! Go for it!": "恭喜你成为魔法师公会的一员！加油！",
        "Wanna be a Mage, eh?": "想成为魔法师，是吗？",
        "I'd be happy to explain the requirements for a pretty girl like you!": "我很乐意为像你这样的漂亮女孩解释要求！",
        "First of all, you have to reach Novice Job Level 10 and learn all of the Basic Skills.": "首先，你必须达到初学者职业等级10并学会所有基本技能。",
        "In the past, there was a complicated potion making test. Because of that, we'd lost an aplicant slowly.": "过去有一个复杂的药水制作测试。因为那个测试，我们慢慢失去了申请者。",
        "So, we decided to accept all aplicants who meet the basic requirements.": "所以，我们决定接受所有满足基本要求的申请者。",
        "Don't hesitate. Just be a magician!": "别犹豫了。来当魔法师吧！",
        "Nothing...?": "没什么……？",
    }
    sel = {
        "I want to be a Mage:What are the requirements to be a Mage?:Nothing, thanks.": "我想成为魔法师:成为魔法师有什么要求？:没什么，谢谢。",
        "I want to be a Mage.:Nothing, thanks.": "我想成为魔法师。:没什么，谢谢。",
    }
    return mes, sel


def build_merchant_dict():
    mes = {
        "Long time no see!": "好久不见！",
        "Hey, you didn't quit": "嘿，你没有放弃",
        "your business, did you?": "你的生意吧？",
        "What happened?": "怎么回事？",
        "Whoa...": "哇……",
        "You've actually been to Valhalla?! Wow, you've come a long way...": "你居然去过瓦尔哈拉？！哇，你走了好远的路啊……",
        "Hmmm...": "嗯嗯……",
        "It seems that you're not ready to become a Merchant again. Go finish learning the Basic Novice Skills first.": "看来你还没准备好再次成为商人。先去把初学者基本技能学完吧。",
        "Don't worry, we'll always have a Merchant position open for you. Just come back when you're ready, okay?": "别担心，我们永远为你保留一个商人的位置。准备好了就回来，好吗？",
        "I guess it's destiny that we meet like this once more. Alright. Once again, let me change you into a Merchant!": "我想这就是命运，让我们再次相遇。好吧。让我再次把你变成商人！",
        "Ah~ How nostalgic. Just like old times! Alright, do your best!": "啊~真怀念。就像以前一样！好了，加油吧！",
        "^333333*Sigh*^000000": "^333333*叹气*^000000",
        "I'm so bored...": "好无聊啊……",
        "When will I hear from my lovely Blossom?": "什么时候才能收到我可爱的花花的消息呢？",
        "Hey, why are you here?": "嘿，你来这里做什么？",
        ".....? Sorry? What are you saying?": "……？什么？你说什么？",
        "You are already a merchant. Oh my..": "你已经是商人了。天哪……",
        "Huh?! ...Do I need to laugh right now?!": "啊？！……我现在需要笑吗？！",
        "Ahh? Are you trying to have both ways?": "啊？你想脚踏两条船？",
        "How about just giving yourself over to your original job?": "不如专心做好你原来的职业吧？",
        "We have business ethics you know.": "我们可是有商业道德的。",
        "Want to be a merchant? Hmm...": "想成为商人？嗯……",
        "But if you want to be a merchant, your basic skill level must reach Level 9 or you must spend all of your skill points.": "但如果你想成为商人，你的基本技能等级必须达到9级，或者你必须用完所有技能点。",
        "Don't you think we need to learn some basic skills although we just deal with money?": "你不觉得虽然我们只是跟钱打交道，但也需要学一些基本技能吗？",
        "Good, I think you're fully ready for it seeing that your basic skill level is fulfilled.": "好的，看到你的基本技能等级已经达标了，我觉得你已经完全准备好了。",
        "Now I allow you to be a merchant.": "现在我允许你成为商人。",
        "Congratulations on becoming a merchant!": "恭喜你成为商人！",
        "Congratulations again for being a member of the merchant guild and one of our colleagues. I expect your active participation from now on!": "再次恭喜你成为商人公会的一员和我们的同事。从现在起，期待你的积极参与！",
        "Absolutely, we need young people who have passion to achieve our great goal for securing 20% of the worldwide currency volume. You get it? Huh?": "没错，我们需要像你这样有热情的年轻人来实现我们掌控全球20%货币流通量的伟大目标。你懂了吗？嗯？",
        "Well, I'm just saying... it means let's make lots of money in the end. You guys know that~": "嗯，我只是说说……意思就是最终让我们一起赚大钱。你们知道的~",
        "Merchant? To put it simply, the person who sells good and makes money is a merchant.": "商人？简单来说，卖东西赚钱的人就是商人。",
        "Not good at fighting and doesn't have special attack/recovery skills... but a merchant can buy things at a low price and then sell them and make money.": "不擅长战斗，也没有特殊的攻击/恢复技能……但商人可以低价买入然后卖出赚钱。",
        "Well, a merchant has an ultimate skill called Mammonite which strikes an enemy with his/her money... We can equip everything except Bows, Rods, and Two-Handed Swords. But we can always sell and buy those.": "嗯，商人有一个终极技能叫金币投掷，用钱砸敌人……我们除了弓、法杖和双手剑之外什么都能装备。但我们随时可以买卖那些东西。",
        "Yes... we merchants always have money on our minds, got it?": "是的……我们商人脑子里永远想着钱，明白了吗？",
        "To become a merchant, although just selling and receiving money is our job, you must reach at least basic skill level 9.": "要成为商人，虽然买卖收钱是我们的工作，但你必须至少达到基本技能等级9。",
        "Well, we used to receive a start-up fee before. Wasn't it hard to make that money?": "嗯，我们以前还收过启动资金呢。凑那笔钱不容易吧？",
        "There were too many people who couldn't gather that money and kept crying.": "有太多人凑不齐那笔钱一直在哭。",
        "So recently, we decided to allow any Novice who wants to be a merchant become one.": "所以最近，我们决定让任何想成为商人的初学者都能成为商人。",
        "Because to be alive or not later is all up to one's ability.": "因为以后是死是活全凭个人能力。",
    }
    sel = {
        "I want to be a merchant.:I want to know more about merchants.:Ask him the requirements to be a merchant.:Nothing.": "我想成为商人。:我想了解更多关于商人的事。:告诉我成为商人的要求。:没什么。",
    }
    return mes, sel


def build_thief_dict():
    mes = {
        "Huh? Do I know you? It's creepy that you seem so familiar. You don't have a twin, do you?": "嗯？我认识你吗？你看起来好面熟，真诡异。你没有双胞胎吧？",
        "What, do you want to be a Thief? I'm sorry, but you look like you need more training.": "什么，你想成为盗贼？抱歉，但你看起来还需要更多训练。",
        "Take your time and learn all the Basic Skills, will you? Well then, see you later~!": "慢慢来，把所有基本技能都学会吧。那么，回头见~！",
        "Well, I got this feeling like you've been through a lifetime of fighting, so I'm promoting you to a Thief right this minute. I better give you tough guys what you want...": "嗯，我有种感觉你经历过一辈子的战斗，所以我现在就把你提升为盗贼。我最好给你们这些硬汉想要的……",
        "Since you've become a Thief, live as a Thief. Now, go for it! Next~": "既然你已经成为盗贼了，就像盗贼一样生活吧。现在，去吧！下一位~",
        "Hey, dude.": "嘿，哥们。",
        "Hey, baby~": "嘿，宝贝~",
        "Hey, baby.": "嘿，宝贝。",
        "...Hey! You look too goody-goody to want to be a Thief!! Now scram, I'm busy. Next!": "……嘿！你看起来太正经了，不像是想当盗贼的！！快走，我很忙。下一位！",
        "Well, I'm not in charge of making you a Thief. I just accept applications, get it?": "嗯，让你成为盗贼不归我管。我只负责接受申请，明白了吗？",
        "If you want to become a Thief, ask the sharp-eyed guy next to me.": "如果你想成为盗贼，去问我旁边那个眼神犀利的家伙。",
        "Hey~ if you have any trouble, get it out to me anytime, huh?": "嘿~有什么麻烦的话，随时跟我说，啊？",
        "What the heck...?": "搞什么鬼……？",
        "Hey, brother.": "嘿，兄弟。",
        "Hey, lady.": "嘿，小姐。",
        "Why are you here? Go back to your place~ go back~~": "你来这里干什么？回你该去的地方~回去~~",
        "You know you cannot be a thief without an application...": "你知道没有申请书是不能成为盗贼的……",
        "What's on your mind...?": "你在想什么……？",
        "Well, are you that proud of it?": "嗯，你还挺自豪的？",
        "You're telling me so proudly that you want to be a Thief! Why don't you go to all the villages and advertise yourself for being a thief?": "你这么骄傲地告诉我你想当盗贼！你怎么不去所有村庄宣传一下自己要当盗贼呢？",
        "'Ha ha ha! Go put up a banner that says 'I will be a proud thief who steals other people's stuff.'": "'哈哈哈！去挂个横幅写着'我要成为一个偷别人东西的光荣盗贼。'",
        "Do you want to be a thief so badly?": "你真的那么想当盗贼吗？",
        "Oh, do you...? Huh.. well... I do live and learn to see strange people like you.": "哦，是吗……？哈……嗯……活到老学到老，还能见到你这样奇怪的人。",
        "Then why are you here? Do you think you can become a thief so easily?": "那你来这里干什么？你以为当盗贼那么容易吗？",
        "Eh..? me? me?": "嗯……？我？我？",
        "Well... I just fit well to being a thief... characteristically... I don't mind this silly matter.": "嗯……我就是天生适合当盗贼……性格上来说……我不在意这种无聊的事。",
        "Anyway, in the outside world, never say that you want to be a Thief!!": "总之，在外面的世界，千万别说你想当盗贼！！",
        "So, do you want to apply for being a Thief?": "那么，你要申请成为盗贼吗？",
        "Well... do what you want to do~ Go your way~": "嗯……你想做什么就做什么吧~走你的路~",
        "I can see your strong will to become a Thief......": "我能看到你想成为盗贼的坚强意志……",
        "But only with your will, you cannot make it in a real fight, can you?": "但光有意志，在真正的战斗中可不行，对吧？",
        "So go and reach at least Basic Skill Level 9.": "所以去达到至少基本技能等级9吧。",
        # Second NPC
        "Alright. You must have passed the job interview, huh?": "好的。你一定通过了职业面试吧？",
        "Good. I'll accept you.": "好。我接受你了。",
        "Let's begin the job-changing ceremony of our guild!": "让我们开始公会的转职仪式吧！",
        "'Congratulations on becoming a Thief.'": "'恭喜你成为盗贼。'",
        "'From now on, keep the rules of our guild and be an honorable member.'": "'从现在起，遵守我们公会的规则，做一个光荣的成员。'",
        "'If you bring us any disgrace by breaking our rules, you better watch your back.'": "'如果你违反规则给我们带来耻辱，你最好小心你的后背。'",
        "'Anyway, I expect you to be a great thief.'": "'总之，我期待你成为一名伟大的盗贼。'",
        "Heee~Yaaaa~! Congratulations! My friend.": "嘿~呀~！恭喜！我的朋友。",
        "My name is 'Brad'. I'm in charge of human resources here.": "我叫'布拉德'。我负责这里的人事工作。",
        "I'm not sure for now but you'll have more chances to see me later on.": "现在还不确定，但以后你会有更多机会见到我的。",
        "Okay, I've done what I can do to you, so go on your way. I'm quite a busy man.": "好了，我能做的都做了，你上路吧。我可是个大忙人。",
        "See you again.": "再见。",
        "I don't have any special events now. So go on your way and come back later.": "我现在没有什么特别的活动。你先走吧，以后再来。",
        "Hey~ Hey~ You're not a novice or a thief!": "嘿~嘿~你既不是初学者也不是盗贼！",
        "What are you doing here? You're not welcome to make this place your home~ Hweeeee~ Get outta here~": "你在这里干什么？这里不欢迎你把这当家~嘿~出去~",
        "Ho? Why is a novice like you visiting here?": "哦？一个初学者来这里做什么？",
        "If you are here to be a Thief, ask the nasty-tempered lady right next to me.": "如果你是来当盗贼的，去问我旁边那个脾气暴躁的女士。",
    }
    sel = {
        "I want to be a Thief.:Nothing.": "我想成为盗贼。:没什么。",
        "Yes.:No.:How about you?": "是的。:不。:你呢？",
        "Yes, I do.:No.": "是的，我要。:不。",
    }
    return mes, sel


def build_acolyte_dict():
    mes = {
        "Ah, I sense you have endured": "啊，我感觉到你经历过",
        "a past life experience. You must have learned many things before entering Valhalla.": "前世的磨练。在进入瓦尔哈拉之前，你一定学到了很多东西。",
        "Unfortunately, I don't think you're ready to become an Acolyte yet. Please finish learning all of the Basic Skills first.": "很遗憾，我觉得你还没准备好成为侍祭。请先把所有基本技能学完。",
        "In the meantime,": "在此期间，",
        "I will wait until": "我会等到",
        "you are ready.": "你准备好。",
        "May God be": "愿神",
        "with you.": "与你同在。",
        "Well, I welcome you": "好的，我欢迎你",
        "back from Valhalla and": "从瓦尔哈拉归来，",
        "wish you luck on your": "祝你新的人生旅途",
        "new life's journey.": "一切顺利。",
        "Now, venture forth and seek those who need your help. May God light your path.": "现在，出发去寻找需要你帮助的人吧。愿神照亮你的道路。",
        "Now, venture forth to seek people who need your help. May God enlighten your way.": "现在，出发去寻找需要你帮助的人吧。愿神照亮你的前路。",
        "I sense that you have endured a past life experience. You must have learned many things before entering Valhalla.": "我感觉到你经历过前世的磨练。在进入瓦尔哈拉之前，你一定学到了很多东西。",
        "However, I can tell that you are not suited to be an Acolyte. Please remember who you were in your past life and find your path.": "然而，我能看出你不适合成为侍祭。请回忆起你前世的身份，找到你的道路。",
        "What is it that you seek?": "你在寻找什么？",
        "Are you feeling okay today? I can tell by your attire that you are already an Acolyte. You're not joking around, are you?": "你今天感觉还好吗？从你的穿着我能看出你已经是侍祭了。你不是在开玩笑吧？",
        "I'm sorry but it seems you already have your own job, aren't you?": "抱歉，你似乎已经有自己的职业了，不是吗？",
        "Do you truly wish to become a servant of God?": "你真的想成为神的仆人吗？",
        "Let's see whether you are ready for it or not... Hmm...": "让我看看你是否准备好了……嗯……",
        "Oh my?! You haven't accomplished the basic practice yet?! You have a long way to go! Come again after increasing your job level!": "哦天哪？！你还没完成基本修行？！你还有很长的路要走！提升你的职业等级后再来吧！",
        "Hmm... your job level is enough...": "嗯……你的职业等级足够了……",
        "Good. Now I will give you the qualification to become an Acolyte.": "好的。现在我将赐予你成为侍祭的资格。",
        "Always remember to be thankful to God, who takes care of us all the time. In chaos and times of difficulty, face your hardships with unwavering faith.": "永远记得感恩一直照顾我们的神。在混乱和困难时期，以坚定不移的信仰面对你的困难。",
        "Lastly, I want to sincerely congratulate you on persevering through your trial of penance.": "最后，我想真诚地祝贺你坚持完成了苦修的考验。",
        "Do you wish to become an Acolyte?": "你想成为侍祭吗？",
        "Then, you must fulfill the following requirements thinking those are the practices given by God.": "那么，你必须完成以下要求，将其视为神赐予的修行。",
        "First, you have to reach at least Novice Job Level 9 and learn all of the Basic Skills.": "首先，你必须达到至少初学者职业等级9并学会所有基本技能。",
        "This is the most basic thing to do, so you need to regard it as the way of training yourself.": "这是最基本的事情，你需要将其视为修炼自己的方式。",
        "When you think you fulfilled this requirement, then come back to me again. Then you will have a holy job in which you can spread God's will.": "当你觉得自己满足了这个要求，就再来找我。届时你将获得一份神圣的职业，可以传播神的旨意。",
        # Father Rubalkabara
        "Please take care. They should know that you've met me by the time you arrive at the Prontera Sanctuary.": "请保重。等你到达普隆德拉圣堂时，他们应该已经知道你见过我了。",
        "I've sent a carrier pigeon with a message. I hope it will arrive there safely...": "我已经用信鸽送出了消息。希望它能安全到达那里……",
        "Oh...? You must be the one who aspires to become an Acolyte. I've already received news from the Sanctuary that you might be coming.": "哦……？你一定是那个立志成为侍祭的人。我已经从圣堂收到消息说你可能会来。",
        "I believe you've been told much about Acolytes from Friar Mareusis. Plus, there's plenty of helpful people in the Prontera Sanctuary.": "我相信马鲁修斯修士已经告诉你很多关于侍祭的事了。而且，普隆德拉圣堂里有很多乐于助人的人。",
        "I guess there's really no need for me to teach you much. Besides, I'm sure your someone from your generation may have trouble listening to an old man like me. Hahaha~": "我想我真的没什么需要教你的了。况且，我相信你们这一代的年轻人可能不太愿意听像我这样的老人说话。哈哈~",
        "Still, lessons may come from the places you'd least expect. God loves to teach his children in strange ways. You'll see.": "不过，教训可能来自你最意想不到的地方。神喜欢用奇妙的方式教导他的孩子们。你会明白的。",
        "Well, I'll send the message telling them that you've come to visit me. So, you may now return to the Prontera Sanctuary.": "好了，我会发消息告诉他们你来拜访过我了。所以，你现在可以回普隆德拉圣堂了。",
        "Farewell.": "再见。",
        "Oh...": "哦……",
        "Are you one of the": "你是侍祭",
        "Acolyte applicants...?": "申请者之一吗……？",
        "Let's see...": "让我看看……",
        "I don't think your name": "我觉得你的名字",
        "is on my list. Hmmm...": "不在我的名单上。嗯……",
        "Why don't you go back to the Prontera Sanctuary and check again?": "你为什么不回普隆德拉圣堂再确认一下呢？",
        "Huh? What brings you here? This is a very dangerous place for a Novice like yourself!": "嗯？什么事把你带到这里来了？这里对像你这样的初学者来说太危险了！",
        "Greetings.": "你好。",
        "Welcome to the Deep. Feel free to sit and contemplate God's message with me. This place is beautiful, even if danger accompanies its sense of serenity...": "欢迎来到深处。请随意坐下，和我一起沉思神的旨意。这个地方很美，即使危险伴随着它的宁静……",
        "Oh ho...": "哦呵……",
        "Have you come into the Deep here for training? Or are you just a Wanderer?": "你是来这里训练的吗？还是只是一个流浪者？",
        "Whoever you are, please take care of yourself. The monsters in here are shockingly strong, contrary to their cute appearance.": "不管你是谁，请照顾好自己。这里的怪物虽然外表可爱，但实力惊人地强大。",
        # Mother Mathilda
        "I will send a carrier pigeon to the Prontera Sanctuary. When you return, the Priest there should already have received my message.": "我会用信鸽给普隆德拉圣堂送消息。等你回去的时候，那里的神父应该已经收到我的消息了。",
        "I will pray to God, and hope that you become an Acolyte soon.": "我会向神祈祷，希望你能早日成为侍祭。",
        "Ah, you must be one of the Acolyte applicants. I sincerely welcome you.": "啊，你一定是侍祭申请者之一。我真诚地欢迎你。",
        "Please return to the Prontera Sanctuary and speak to the Priest in charge.": "请回到普隆德拉圣堂，和负责的神父谈谈。",
        "Ah...!": "啊……！",
        "You must be one": "你一定是",
        "of the Acolyte applicants.": "侍祭申请者之一。",
        "I sincerely welcome you.": "我真诚地欢迎你。",
        "Now, what is your name?": "那么，你叫什么名字？",
        "Hmm...": "嗯……",
        "It seems your name": "你的名字似乎",
        "is not on my list...": "不在我的名单上……",
        "Perhaps you should return to the Prontera Sanctuary and check the destination for your penance trial once again.": "也许你应该回普隆德拉圣堂，再确认一下你苦修试炼的目的地。",
        "...": "……",
        "Hello there~": "你好~",
        "How is your practice coming along? I certainly hope you're enjoying living in the grace of God.": "你的修行进展如何？我真心希望你享受生活在神的恩典中。",
        "May God": "愿神",
        "be with you...": "与你同在……",
        # Father Yosuke
        "What?": "什么？",
        "Have you any more business with me?! You don't! Go back to the Sanctuary now!": "你还有什么事找我？！没有了！现在就回圣堂去！",
        "Hey.": "嘿。",
        "Whatever you are,": "不管你是什么人，",
        "you look like an": "你看起来像个",
        "Acolyte applicant.": "侍祭申请者。",
        "Right?": "对吧？",
        "Not bad, not bad. You withstood the penance trial pretty well.": "不错，不错。你经受住苦修试炼做得很好。",
        "So what's your name?": "那你叫什么名字？",
        "Now go back to the Santuary and finish becoming an Acolyte, kid.": "现在回圣堂去完成成为侍祭的手续吧，孩子。",
        "You look like an Acolyte Applicant. Am I right?": "你看起来像个侍祭申请者。我说得对吗？",
        "Not bad at all, you've made it all the way here from Prontera. So what's your name, kid?": "还不错嘛，你从普隆德拉一路走到这里了。那你叫什么名字，孩子？",
        "You probably made a mistake. Go back to the Santuary, and check with the Bishop.": "你可能搞错了。回圣堂去，跟主教确认一下。",
        "You...": "你……",
        "Novice.": "初学者。",
        "There something": "有什么",
        "you wanna tell me?": "想跟我说的吗？",
        "Hey...": "嘿……",
        "If you like, come sit here with me and meditate the great truths. God's majesty is truly inspiring...": "如果你愿意，来这里和我一起坐下冥想伟大的真理。神的威严真是令人敬畏……",
        "Do you have anything to say? Because unfortunately for you,": "你有什么要说的吗？因为很不幸，",
        "I don't any replies.": "我没有什么回答。",
    }
    sel = {
        "Change your job to acolyte.:Ask the requirements to be an acolyte.:Quit it.": "转职为侍祭。:询问成为侍祭的要求。:算了。",
    }
    return mes, sel


def process_file(rel_path, mes_dict, sel_dict, dry_run=False):
    """Process a single file with translation dictionaries."""
    # Add common NPC names to mes_dict
    full_mes = dict(NPC_NAMES)
    full_mes.update(mes_dict)

    src = BACKUP_DIR / rel_path.replace('/', '\\')
    dst = OUTPUT_DIR / rel_path.replace('/', '\\')

    if not src.exists():
        print(f"  SKIP (no backup): {rel_path}")
        return {'mes': 0, 'select': 0}

    content = src.read_text(encoding='utf-8')
    lines = content.splitlines(keepends=False)
    result = list(lines)
    stats = {'mes': 0, 'select': 0, 'mes_total': 0, 'sel_total': 0}

    for i, line in enumerate(lines):
        mm = MES_RE.match(line)
        if mm:
            stats['mes_total'] += 1
            en = mm.group(2)
            if en in full_mes:
                result[i] = mm.group(1) + '"' + full_mes[en] + '"' + (mm.group(3) or ';')
                stats['mes'] += 1
            continue
        sm = SELECT_RE.search(line)
        if sm:
            stats['sel_total'] += 1
            en = sm.group(2)
            if en in sel_dict:
                result[i] = line[:sm.start(1)] + sm.group(1) + sel_dict[en] + sm.group(3) + line[sm.end():]
                stats['select'] += 1

    print(f"[{rel_path}] mes={stats['mes']}/{stats['mes_total']} sel={stats['select']}/{stats['sel_total']}")

    if not dry_run and (stats['mes'] + stats['select']) > 0:
        translated = '\n'.join(result)
        encoded = translated.encode('gbk', errors='replace')
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(encoded)
        print(f"  -> Written (GBK)")

    return stats


def main():
    dry_run = '--dry-run' in sys.argv
    print("=== Renewal Job Quest NPC Translation ===")
    print(f"  Source:  {BACKUP_DIR}")
    print(f"  Output:  {OUTPUT_DIR}")
    print(f"  Dry run: {dry_run}")
    print()

    files = {
        '1-1/swordman.txt': build_swordman_dict,
        '1-1/archer.txt': build_archer_dict,
        '1-1/mage.txt': build_mage_dict,
        '1-1/merchant.txt': build_merchant_dict,
        '1-1/thief.txt': build_thief_dict,
        '1-1/acolyte.txt': build_acolyte_dict,
    }

    total = {'mes': 0, 'select': 0, 'files': 0}
    for rel_path, build_fn in files.items():
        mes_dict, sel_dict = build_fn()
        stats = process_file(rel_path, mes_dict, sel_dict, dry_run)
        total['mes'] += stats['mes']
        total['select'] += stats['select']
        total['files'] += 1

    print(f"\n=== Summary ===")
    print(f"  Files: {total['files']}")
    print(f"  mes:   {total['mes']}")
    print(f"  select:{total['select']}")


if __name__ == '__main__':
    main()
