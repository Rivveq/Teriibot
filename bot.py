import random
import json
import datetime
import twitchio
import asyncio
from twitchio.ext import commands
from operator import itemgetter

# ===========================================================================
#                              v1.3.5
# ===========================================================================


TOKEN='oauth:0ig7bjlzvnss3o4navanvbgzo9mrqq'
CLIENT_ID='gp762nuuoqcoxypju8c569th9wz7q5'
BOT_NICK='Teriibot'
BOT_PREFIX='$'
CHANNEL='irivv'
OWNER='irivv'


# ===========================================================================
#                              ECONOMY
# ===========================================================================


POINTS_WELCOME = 10 # points on hi command

POINTS_SLOTSWIN = 200
POINTS_SLOTSCOST = 10

POINTS_SLOTSWIN_PLUS = 2500
POINTS_SLOTSCOST_PLUS= 10

POINTS_WORK = 50 # points on work command

STEAL_CHANCE = 30 # in %
STEAL_MAX_AMOUNT = 30 # in %

GAMBLE_CHANCE = 30 # in %
GAMBLE_RATIO = 2 # points conversion rate after gamble success

STARTING_POINTS = 400

BUG_FIND_REWARD = 150

LOTTO_MIN_ENTRY = 200
LOTTO_EXECUTE_TIME = 180
LOTTO_PRIZE_MODIFIER = 0.1
LOTTO_IN_PROGRESS = False

# ===========================================================================
#                             BOT LOGIC
# ===========================================================================


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TOKEN, prefix=BOT_PREFIX, initial_channels=[CHANNEL, "meowbez"])
    

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        await check_lotto_ready()

    async def event_message(self, message):
        if message.echo:
            return

        print(f"{message.author.name} said: {message.content}")

        await self.handle_commands(message)
    
    async def event_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return
        
        elif isinstance(error, commands.ArgumentParsingFailed):
            await ctx.send(error.message)

        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You're missing an argument: " + error.name)

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Command is on cooldown! {round(error.retry_after)} seconds left")

        else:
            print(error)


    @commands.command(name='hello', aliases=('hi', 'yo'))
    async def hello_command(self, ctx: commands.Context):
        author_name = ctx.author.name

        if check_profiles_database(author_name):
            if create_datenow_math() - check_attribute(author_name, 'lasthello') > 0:
                await ctx.send(f'Hello {ctx.author.display_name}!')
                add_attribute(author_name, POINTS_WELCOME, "points")
                update_lasthello_date(author_name)
            else:
                await ctx.send(f'We said hello earlier!')
        else:
            await ctx.send(f'Hello {ctx.author.display_name}!')
            create_profile(author_name)
    

    @commands.command(name='balance', aliases=('catnip', 'saldo'))
    async def balance_command(self, ctx: commands.Context):
        author_name = ctx.author.name

        if check_profiles_database(author_name):
            balance = check_attribute(author_name, 'balance')
            await ctx.send(f'{ctx.author.display_name} current balance: {balance}')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
    

    @commands.command(name='give')
    async def give_command(self, ctx: commands.Context, user: twitchio.PartialUser, amount) -> None:
        user_balance = check_attribute(ctx.author.name, 'balance')
        
        if check_profiles_database(ctx.author.name) and user.name.lower() == "teriibot":
            await ctx.send("You're too kind! uwu Keep it for yourself <3")
        elif check_profiles_database(ctx.author.name) and user.name.lower() == ctx.author.name:
            await ctx.send("You're a narcissist huh?")
        
        elif check_profiles_database(ctx.author.name) and check_profiles_database(user.name.lower()):
            if user_balance <= 0:
                await ctx.send("You don't have enough catnip!")
                return
            elif amount.lower() == 'all':
                given_points = user_balance
            elif amount.lower() == 'none':
                await ctx.send(f"Aha")
                return
            elif amount.isdigit() and int(amount) <= user_balance:
                given_points = int(amount)
            elif amount.isdigit() and int(amount) > user_balance:
                await ctx.send("You don't have enough catnip for that!")
                return
            
            add_attribute(ctx.author.name, -abs(given_points), "points")
            add_attribute(user.name, abs(given_points), "points")
            await ctx.send(f"{ctx.author.display_name} gave {user.name} {abs(given_points)} grams of catnp!")
        
        elif check_profiles_database(user.name):
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
        else:
            await ctx.send(f"I don't remember {user.name}! They should say hi first")
    

    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.user)
    @commands.command(name='work')
    async def work_command(self, ctx: commands.Context):
        author_name = ctx.author.name
        if check_profiles_database(author_name):
            # Calculating the payout based on user level
            payout = check_work_payout(check_level(check_attribute(author_name, "work_xp")))

            add_attribute(author_name, payout, "points")
            add_attribute(author_name, 1, "work_xp")

            await ctx.send(f'{ctx.author.display_name} gathered some catnip in the forest')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
    

    @commands.command(name='level')
    async def level_check_command(self, ctx: commands.Context):
        user_level = check_level(check_attribute(ctx.author.name, "work_xp"))

        await ctx.send(f"Your current level: {user_level}")

    
    @commands.command(name='leaderboard', aliases=('lb', 'board'))
    async def leaderboard_command(self, ctx: commands.Context):
        lboard = read_leaderboard()
        user_place = check_leaderboard_place(lboard, ctx.author.name)
        user1 = check_attribute(lboard[0], 'balance')
        user2 = check_attribute(lboard[1], 'balance')
        user3 = check_attribute(lboard[2], 'balance')
        await ctx.send(f"Your place by catnip owned: {user_place} <|> Top 3 are: 1. {lboard[0]} - {user1} | 2. {lboard[1]} - {user2} | 3. {lboard[2]} - {user3}")

    
    @commands.cooldown(rate=1, per=900, bucket=commands.Bucket.user)
    @commands.command(name='steal', aliases=('yoink', 'take'))
    async def steal_command(self, ctx: commands.Context, user: twitchio.PartialUser):
        if check_profiles_database(ctx.author.name) and user.name.lower() == "teriibot":
            await ctx.send(f"What are you trying to do huh -10g of catnip for you, you greedy bastard KEKW")
            add_attribute(ctx.author.name, -10, "points")
        elif check_profiles_database(ctx.author.name) and user.name.lower() == ctx.author.name:
            await ctx.send("You're a narcissist huh?")
        elif check_profiles_database(ctx.author.name) and check_profiles_database(user.name):
            success_roll = random.randrange(1,101)
            if success_roll <= STEAL_CHANCE:
                if check_attribute(user.name, 'balance') >= 5:
                    stolen_amount_ratio = random.randrange(1,STEAL_MAX_AMOUNT + 1)
                    stolen_amount = check_attribute(user.name, 'balance') * (stolen_amount_ratio * 0.01)
                    add_attribute(user.name, -int(stolen_amount), "points")
                    add_attribute(ctx.author.name, int(stolen_amount), "points")
                    await ctx.send(f"Success! {ctx.author.display_name} has stolen {int(stolen_amount)} grams of catnip from {user.name}!")
                else:
                    await ctx.send(f"Your victim doesn't have enough catnip!")
            else:
                fee_amount_ratio = random.randrange(10, 61)
                fee_amount = check_attribute(ctx.author.name, 'balance') * (fee_amount_ratio * 0.01)
                await ctx.send(f"{ctx.author.name} was caught while stealing and thus was forced to pay his bail out fee of {int(fee_amount)}!")
                add_attribute(ctx.author.name, -int(fee_amount), "points")
        elif check_profiles_database(user.name):
            await ctx.send(f"{user.name} is not even registered yet!")
        else:
            await ctx.send(f"I don't remember {user.name}! They should say something or introduce themself first")
    

    @commands.cooldown(rate=1, per=15, bucket=commands.Bucket.user)
    @commands.command(name='gamble')
    async def gamble_command(self, ctx: commands.Context, amount):
        if check_profiles_database(ctx.author.name):
            user_balance = check_attribute(ctx.author.name, 'balance')
            went_all_in = False

            if user_balance == 0:
                await ctx.send("You don't have anything to gamble with!")
            elif amount.lower() == 'all':
                went_all_in = True
                gambled_points = user_balance
            elif amount.isdigit() and int(amount) <= user_balance:
                gambled_points = int(amount)
            elif amount.isdigit() and int(amount) > user_balance:
                await ctx.send("You don't have enough catnip for that!")
                return
            else:
                await ctx.send("I don't understand what are you trying to do")
                return
            
            success_roll = random.randrange(1,101)
            if success_roll <= GAMBLE_CHANCE:
                add_attribute(ctx.author.name, gambled_points * (GAMBLE_RATIO - 1), 'points') # minus 1 so ratio 2 becomes 100% more not 200% more (1.25 would become 25% more etc)
                if went_all_in:
                    await ctx.send(f"{ctx.author.display_name} WENT ALL IN AND WON! PogChomp")
                else:
                    await ctx.send(f"{ctx.author.display_name} won the gamble and got {gambled_points} grams of catnip!")
            else:
                add_attribute(ctx.author.name, -(gambled_points * (GAMBLE_RATIO - 1)), 'points')
                if went_all_in:
                    await ctx.send(f"{ctx.author.display_name} LOST ALL THEIR POINTS! KEKWait")
                else:
                    await ctx.send(f"{ctx.author.display_name} gambled {gambled_points} grams and lost...")
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
        

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='slots')
    async def slots_command(self, ctx: commands.Context):
        slots_1 = random.randrange(0,3)
        slots_2 = random.randrange(0,3)
        slots_3 = random.randrange(0,3)
        slots_images = ['amikoscream', 'kurwaTen', 'rivhop']
    
        if check_profiles_database(ctx.author.name):
            if check_attribute(ctx.author.name, 'balance') >= POINTS_SLOTSCOST:
                if(slots_1==slots_2==slots_3):
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} congratulations!')
                    add_attribute(ctx.author.name, POINTS_SLOTSWIN, "points")
                elif((slots_1==slots_2) or (slots_2==slots_3)):
                    await ctx.send(f"{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} your points are refunded!")
                else:
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} better luck next time!')
                    add_attribute(ctx.author.name, -POINTS_SLOTSCOST, "points")
            else:
                await ctx.send(f'Not enough catnip!')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')


    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.user)
    @commands.command(name='slotsplus')
    async def slotsplus_command(self, ctx: commands.Context):
        slots_1 = random.randrange(0,5)
        slots_2 = random.randrange(0,5)
        slots_3 = random.randrange(0,5)
        slots_images = ['amikoscream', 'kurwaTen', 'rivhop', 'INSANECAT', 'CokeShakey']
    
        if check_profiles_database(ctx.author.name):
            if check_attribute(ctx.author.name, 'balance') >= POINTS_SLOTSCOST_PLUS:
                if(slots_1==slots_2==slots_3):
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} congratulations!!! PogChomp')
                    add_attribute(ctx.author.name, POINTS_SLOTSWIN_PLUS, "points")
                else:
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} better luck next time!')
                    add_attribute(ctx.author.name, -POINTS_SLOTSCOST_PLUS, "points")
            else:
                await ctx.send(f'Not enough catnip!')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')

    
    @commands.command(name='lotto')
    async def lotto_command(self, ctx: commands.Context, amount: int, number: int, minimum_participants: int | None):
        if abs(number) > 20:
            await ctx.send(f"Pick a number from 1 to 20!")
            return
        if amount < LOTTO_MIN_ENTRY:
            await ctx.send(f"You have to provide at least 200g of catnip to participate!")
            return
        if not check_profiles_database(ctx.author.name):
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
            return
        if check_attribute(ctx.author.name, 'balance') < amount:
            await ctx.send(f"You don't have enough catnip for that!")
            return
        
        if check_active_lotto():
            if check_lotto_particopants(ctx.author.name):
                await ctx.send(f"You're already participating in the game!")
            else:
                join_lotto(ctx.author.name, abs(amount), abs(number))
                add_attribute(ctx.author.name, -abs(amount), "points")
                await ctx.send(f"You joined the game with a number of {abs(number)}")
                check_lotto_ready()
        else:
            if minimum_participants is None:
                await ctx.send(f"There isn't a lotto game running. You need to provide the minimum number of participants if you want to create a new lotto game")
            else:
                create_lotto(ctx.author.name, abs(minimum_participants), abs(amount), abs(number), ctx.channel.name)
                add_attribute(ctx.author.name, -abs(amount), "points")
                await ctx.send(f"Lotto created! Your number is {abs(number)}")


    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='wall')
    async def crash_counter_command(self, ctx: commands.Context):
        if ctx.author.is_vip or ctx.author.is_mod or ctx.author.is_broadcaster:
            amount = count_handler('wall')
            await ctx.send(f"Bez crashed {amount} times")
        else:
            await ctx.send(f"Only vips can use this command!")

    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='bw')
    async def dead_counter_command(self, ctx: commands.Context):
        if ctx.author.is_vip or ctx.author.is_mod or ctx.author.is_broadcaster:
            amount = count_handler('bw')
            await ctx.send(f"Bez passed out {amount} times")
        else:
            await ctx.send(f"Only vips can use this command!")
    
    @commands.cooldown(rate=1, per=10, bucket=commands.Bucket.channel)
    @commands.command(name='pink')
    async def pink_counter_command(self, ctx: commands.Context):
        if ctx.author.is_vip or ctx.author.is_mod or ctx.author.is_broadcaster:
            amount = count_handler('pink')
            await ctx.send(f"Bez was amazed by the colour pink {amount} times")
        else:
            await ctx.send(f"Only vips can use this command!")
    

    @commands.command(name='bug')
    async def bug_found_command(self, ctx: commands.Context, user: twitchio.PartialUser):
        if ctx.author.name == 'irivv':
            await ctx.send(f"Thanks for finding a bug {user.name}! Heres a reward")
            add_attribute(user.name.lower(), BUG_FIND_REWARD, "points")
        else:
            await ctx.send(f"Nu uh kid, not for you NOPERS")
    
    @commands.command(name='addpointsall')
    async def add_points_to_all_command(self, ctx: commands.Context, amount: int):
        if ctx.author.name == 'irivv':
            add_points_all(amount)
        else:
            await ctx.send(f"Nu uh kid, not for you NOPERS")

    @commands.command(name='worm')
    async def worm_command(self, ctx: commands.Context):
            await ctx.send(f"Yes, worm catYep")

    @commands.command(name='motto')
    async def motto_command(self, ctx: commands.Context):
        mottos = ["If you think you are too small to make a difference, try sleeping with a mosquito",
                  "The face you're born with is the one God gave you. Your face at 50 is the one you gave yourself",
                  "If you keep your feet firmly on the ground, you'll have trouble putting on your pants",
                  "Life is a very complicated drinking game",
                  "After Tuesday, even the calendar says WTF",
                  "If the facts don't fit the theory, change the facts",
                  "Sometimes, you're the windshield; sometimes, you're the bug",
                  "To get a loan, you first have to prove you don't need it",
                  "A failure is like fertilizer; it stinks, to be sure, but it makes things grow faster in the future",
                  "When nothing goes right... go left",
                  "I drink to make other people more interesting",
                  "Going to church doesn't make you a Christian any more than going to a garage makes you an automobile",
                  "Anything worth doing is worth doing badly",
                  "I walk around like everything's fine, but deep down, inside my shoe, my sock is sliding off",
                  "If a book about failures doesn't sell, is it a success?",
                  "Do not take life too seriously, you will never get out of it alive",
                  "If a cluttered desk is a sign of a cluttered mind, of what, then, is an empty desk a sign?",
                  "Behind every great man is a woman rolling her eyes",
                  "I found there was only one way to look thin, hang out with Sylvester",
                  "If you can't convince them, confuse them…",
                  "Always remember you're unique, just like everyone else"
                  ]
        await ctx.send(f"{random.choice(mottos)}")


# ===========================================================================
#                                Logic
# ===========================================================================


def read_database(local_filename):
    with open(local_filename, "r") as file:
        temp = json.load(file)
    return temp

def write_database(data, local_filename):
    with open(local_filename, "w") as file:
        json.dump(data, file, indent=4)

#----------------------------------------------

def check_profiles_database(name):
    data = read_database(filename_profiles)
    for dict in data:
        if dict["username"] == name:
            return True
    return False

def check_attribute(name, attribute_name):
    data = read_database(filename_profiles)
    for dict in data:
        if dict["username"] == name:
            match attribute_name:
                case 'balance':
                    return int(dict["points"])
                case 'lasthello':
                    return dict["last_hello_date"]
                case 'work_xp':
                    return int(dict["work_xp"])

def read_leaderboard():
    data = read_database(filename_profiles)
    dict_lboard = sorted(data, key=itemgetter('points'), reverse=True)
    lboard = [line['username'] for line in dict_lboard]
    return lboard

def check_leaderboard_place(lboard, name):
    nr = 1
    for place in lboard:
        if place == name:
            return str(nr)
        nr += 1
    return str('None')

def check_level(exp):
    levels_data = read_database(filename_levels)

    for level in levels_data:
        if exp >= level["xp_required"]:
            return level["level"]
        
def check_work_payout(user_level):
    levels_data = read_database(filename_levels)

    for level in levels_data:
        if user_level == level["level"]:
            return level["catnip_gained"]

#----------------------------------------------

def create_profile(name):
    user_data = {}
    data = read_database(filename_profiles)

    user_data["username"] = name
    user_data["points"] = STARTING_POINTS
    user_data["work_xp"] = 0
    user_data["last_hello_date"] = create_datenow_math()

    data.append(user_data)
    write_database(data, filename_profiles)

def create_datenow_math():
    date = datetime.datetime.now().year
    date += datetime.datetime.now().month * 0.01
    date += datetime.datetime.now().day * 0.0001
    return date

def update_lasthello_date(name):
    data = read_database(filename_profiles)
    new_data = []
    for dict in data:
        if dict["username"] == name:
            temp_data = {}
            temp_data["username"] = dict["username"]
            temp_data["points"] = dict["points"]
            temp_data["work_xp"] = dict["work_xp"]
            temp_data["last_hello_date"] = create_datenow_math()
            
            new_data.append(temp_data)
        else:
            new_data.append(dict)
    write_database(new_data, filename_profiles)

def add_attribute(name, amount, attribute_name):
    data = read_database(filename_profiles)
    new_data = []

    match attribute_name:
        case "points":
            for dict in data:
                if dict["username"] == name:
                    temp_data = {}
                    temp_data["username"] = dict["username"]
                    temp_data["points"] = dict["points"] + amount
                    temp_data["work_xp"] = dict["work_xp"]
                    temp_data["last_hello_date"] = dict["last_hello_date"]
                    
                    new_data.append(temp_data)
                else:
                    new_data.append(dict)
            write_database(new_data, filename_profiles)
        case "work_xp":
            for dict in data:
                if dict["username"] == name:
                    temp_data = {}
                    temp_data["username"] = dict["username"]
                    temp_data["points"] = dict["points"]
                    temp_data["work_xp"] = dict["work_xp"] + amount
                    temp_data["last_hello_date"] = dict["last_hello_date"]
                    
                    new_data.append(temp_data)
                else:
                    new_data.append(dict)
            write_database(new_data, filename_profiles)

def add_points_all(amount):
    data = read_database(filename_profiles)
    new_data = []

    for dict in data:
        temp_data = {}
        temp_data["username"] = dict["username"]
        temp_data["points"] = dict["points"] + amount
        temp_data["work_xp"] = dict["work_xp"]
        temp_data["last_hello_date"] = dict["last_hello_date"]     
        new_data.append(temp_data)
    write_database(new_data, filename_profiles)

#----------------------------------------------

def count_handler(counter_name):
    add_count(counter_name)
    return check_count(counter_name)

def add_count(counter_name):
    data = read_database(filename_counters)
    data[f"{counter_name}"] += 1
    write_database(data, filename_counters)

def check_count(counter_name):
    data = read_database(filename_counters)
    return data[f"{counter_name}"]

#----------------------------------------------

def create_lotto(name, min_paricipants, amount, number, channel_name):
    data = read_database(filename_lotto)
    temp_data = {}
    temp_participant = {}

    temp_data["active_lotto"] = 1
    temp_data["channel"] = channel_name
    temp_data["prize_pool"] = 0 + amount
    temp_data["participants_amount"] = 1
    temp_data["min_participants"] = min_paricipants

    temp_participant["name"] = name
    temp_participant["number"] = number

    temp_data["participants"] = [temp_participant]

    write_database(temp_data, filename_lotto)

def join_lotto(name, amount, number):
    data = read_database(filename_lotto)
    temp_data = {}
    temp_participant = {}

    temp_data["active_lotto"] = data["active_lotto"]
    temp_data["channel"] = data["channel"]
    temp_data["prize_pool"] = data["prize_pool"] + amount
    temp_data["participants_amount"] = data["participants_amount"] + 1
    temp_data["min_participants"] = data["min_participants"]

    temp_participant["name"] = name
    temp_participant["number"] = number

    temp_data["participants"] = data["participants"]
    temp_data["participants"].append(temp_participant)

    write_database(temp_data, filename_lotto)

def reset_lotto():
    temp_data = {}
    temp_data["active_lotto"] = 0
    write_database(temp_data, filename_lotto)

    LOTTO_IN_PROGRESS = False

def check_active_lotto():
    data = read_database(filename_lotto)
    if data["active_lotto"] == 1: return True
    else: return False

def check_lotto_particopants(name):
    data = read_database(filename_lotto)
    for user in data["participants"]:
        if user["name"] == name:
            return True
    return False

async def check_lotto_ready():
    data = read_database(filename_lotto)
    if data["active_lotto"] == 1 and data["participants_amount"] >= data["min_participants"]:
        await lotto_ready()

async def lotto_ready():
    global LOTTO_IN_PROGRESS

    if LOTTO_IN_PROGRESS:
        return
    else:
        LOTTO_IN_PROGRESS = True

        await asyncio.sleep(LOTTO_EXECUTE_TIME)

        data = read_database(filename_lotto)

        lotto_channel = bot.get_channel(data["channel"])

        winning_number = random.randrange(1,21)
        prize_modifier = 1 + (data["participants_amount"] * LOTTO_PRIZE_MODIFIER)
        prize = data["prize_pool"] * prize_modifier
        winners = []

        for user in data["participants"]:
            if user["number"] == winning_number:
                winners.append(user["name"])
        
        if len(winners) == 0:
            await twitchio.Channel.send(lotto_channel, f"The lucky number is {winning_number}! Sadly noone won Sadge")
            
        elif len(winners) == 1:
            await twitchio.Channel.send(lotto_channel, f"The lucky number is {winning_number}! The winner is {winners[0]}, they got {prize}")
            add_attribute(winners[0], prize, "points")
        
        else:
            number_of_winners = len(winners)
            devided_prize = round(prize/number_of_winners)

            await twitchio.Channel.send(lotto_channel, f"The lucky number is {winning_number}! There are {number_of_winners}, they got {devided_prize} each")
            for winner in range(number_of_winners):
                add_attribute(winners[winner], devided_prize, "points")
        
        reset_lotto()



# ===========================================================================


filename_profiles = 'points.json'
filename_counters = 'counters.json'
filename_lotto = 'lotto.json'
filename_levels = 'levels.json'

bot = Bot()
bot.run()
