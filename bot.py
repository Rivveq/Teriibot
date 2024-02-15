import random
import json
import datetime
import twitchio
from twitchio.ext import commands
from operator import itemgetter

# ===========================================================================
#                              v1.0
# ===========================================================================


TOKEN='yourtoken'
CLIENT_ID='yourclientid'
BOT_NICK='yourbotnickname'
BOT_PREFIX='$'
CHANNEL='yourchannelname'
OWNER='yournickname'


# ===========================================================================
#                              ECONOMY
# ===========================================================================


POINTS_WELCOME = 10 # points on hi command

POINTS_SLOTSWIN = 150
POINTS_SLOTSCOST = 10

POINTS_SLOTSWIN_PLUS = 6000
POINTS_SLOTSCOST_PLUS= 20

POINTS_WORK = 40 # points on work command

STEAL_CHANCE = 60 # in %
STEAL_MAX_AMMOUNT = 20 # in %
JAIL_TIME = 0 # timeout value

GAMBLE_CHANCE = 25 # in %
GAMBLE_RATIO = 2 # points conversion rate after gamble success

STARTING_POINTS = 50


# ===========================================================================
#                             BOT LOGIC
# ===========================================================================


class Bot(commands.Bot):

    def __init__(self):
        super().__init__(token=TOKEN, prefix=BOT_PREFIX, initial_channels=[CHANNEL])
    

    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')


    async def event_message(self, message):
        if message.echo:
            return

        print(f"{message.author.name} said: {message.content}")

        await self.handle_commands(message)
    

    @commands.command(name='hello', aliases=('hi', 'yo'))
    async def hello_command(self, ctx: commands.Context):
        author_name = ctx.author.name

        if check_database(author_name):
            if create_datenow_math() - check_lasthello(author_name) > 0:
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

        if check_database(author_name):
            balance = check_balance(author_name)
            await ctx.send(f'{ctx.author.display_name} current balance: {balance}')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
    

    @commands.command(name='give')
    async def give_command(self, ctx: commands.Context, user: twitchio.User, ammount: int) -> None:
        if check_database(ctx.author.name) and check_database(user.name):
            if check_balance(ctx.author.name) >= ammount:
                add_attribute(ctx.author.name, -ammount, "points")
                add_attribute(user.name, ammount, "points")
                await ctx.send(f"{ctx.author.display_name} gave {user.name} {ammount} grams of catnp!")
            else:
                await ctx.send("You don't have enough catnip!")
        elif check_database(user.name):
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')
        else:
            await ctx.send(f"I don't yet know {user.display_name}! They should introduce themself first")
    

    @commands.cooldown(rate=1, per=600, bucket=commands.Bucket.user)
    @commands.command(name='work')
    async def work_command(self, ctx: commands.Context):
        author_name = ctx.author.name
        if check_database(author_name):
            add_attribute(author_name, POINTS_WORK, "points")
            add_attribute(author_name, 1, "work_xp")
            await ctx.send(f'{ctx.author.display_name} gathered some catnip in the forest')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')

    
    @commands.command(name='leaderboard', aliases=('lb'))
    async def leaderboard_command(self, ctx: commands.Context):
        lboard = check_leaderboard()
        user_place = check_leaderboard_place(lboard, ctx.author.name)
        user1 = check_balance(lboard[0])
        user2 = check_balance(lboard[1])
        user3 = check_balance(lboard[2])
        await ctx.send(f"Your place by catnip owned: {user_place} <|> Top 3 are: 1.{lboard[0]} - {user1} | 2.{lboard[1]} - {user2} | 3.{lboard[2]} - {user3}")

    
    @commands.cooldown(rate=1, per=900, bucket=commands.Bucket.user)
    @commands.command(name='steal', aliases=('yoink'))
    async def steal_command(self, ctx: commands.Context, user: twitchio.PartialChatter):
        if check_database(ctx.author.name) and check_database(user.name):
            success_roll = random.randrange(1,101)
            if success_roll <= STEAL_CHANCE:
                if check_balance(user.name) >= 5:
                    stolen_ammount = random.randrange(1,STEAL_MAX_AMMOUNT + 1)
                    ammount = check_balance(user.name) * (stolen_ammount * 0.01)
                    add_attribute(user.name, -int(ammount), "points")
                    add_attribute(ctx.author.name, int(ammount), "points")
                    await ctx.send(f"Success! {ctx.author.display_name} has stolen {int(ammount)} grams of catnip from {user.display_name}!")
                else:
                    await ctx.send(f"Your victim doesn't have enough catnip!")
            else:
                await ctx.send(f"{ctx.author.name} was caught while stealing and thus sent to jail for {JAIL_TIME} minutes!")
                # ctx.author.timeout(duration=JAIL_TIME, reason='Caught while stealing.')
        elif check_database(user.name):
            await ctx.send(f"{user.display_name} is not even registered yet!")
        else:
            await ctx.send(f"I don't yet know {user.display_name}! They should introduce themself first")
    

    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='gamble')
    async def gamble_command(self, ctx: commands.Context, ammount):
        if check_database(ctx.author.name):
            user_balance = check_balance(ctx.author.name)
            went_all_in = False
            if ammount.lower() == 'all':
                went_all_in = True
                gambled_points = user_balance
            elif ammount.isdigit() and int(ammount) <= user_balance:
                gambled_points = int(ammount)
            elif ammount.isdigit() and int(ammount) > user_balance:
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
        

    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='slots')
    async def slots_command(self, ctx: commands.Context):
        slots_1 = random.randrange(0,3)
        slots_2 = random.randrange(0,3)
        slots_3 = random.randrange(0,3)
        slots_images = ['amikoscream', 'kurwaTen', 'rivhop']
    
        if check_database(ctx.author.name):
            if check_balance(ctx.author.name) >= POINTS_SLOTSCOST:
                if(slots_1==slots_2==slots_3):
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} congratulations!')
                    add_attribute(ctx.author.name, POINTS_SLOTSWIN, "points")
                else:
                    await ctx.send(f'{ctx.author.display_name} rolled: {slots_images[slots_1]} | {slots_images[slots_2]} | {slots_images[slots_3]} better luck next time!')
                    add_attribute(ctx.author.name, -POINTS_SLOTSCOST, "points")
            else:
                await ctx.send(f'Not enough catnip!')
        else:
            await ctx.send(f'Try saying hello first {ctx.author.display_name}!')


    @commands.cooldown(rate=1, per=30, bucket=commands.Bucket.user)
    @commands.command(name='slotsplus')
    async def slotsplus_command(self, ctx: commands.Context):
        slots_1 = random.randrange(0,5)
        slots_2 = random.randrange(0,5)
        slots_3 = random.randrange(0,5)
        slots_images = ['amikoscream', 'kurwaTen', 'rivhop', 'INSANECAT', 'CokeShakey']
    
        if check_database(ctx.author.name):
            if check_balance(ctx.author.name) >= POINTS_SLOTSCOST_PLUS:
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


# ===========================================================================


def read_database():
    with open(filename, "r") as file:
        temp = json.load(file)
    return temp

def write_database(data):
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)

def check_database(name):
    data = read_database()
    for dict in data:
        if dict["username"] == name:
            return True
    return False

def check_balance(name):
    data = read_database()
    for dict in data:
        if dict["username"] == name:
            return int(dict["points"])

def check_lasthello(name):
    data = read_database()
    for dict in data:
        if dict["username"] == name:
            return dict["last_hello_date"]

def check_leaderboard():
    data = read_database()
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


def create_profile(name):
    user_data = {}
    data = read_database()

    user_data["username"] = name
    user_data["points"] = STARTING_POINTS
    user_data["work_xp"] = 0
    user_data["last_hello_date"] = create_datenow_math()

    data.append(user_data)
    write_database(data)

def create_datenow_math():
    date = datetime.datetime.now().year
    date += datetime.datetime.now().month * 0.01
    date += datetime.datetime.now().day * 0.0001
    return date

def update_lasthello_date(name):
    data = read_database()
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
    write_database(new_data)

def add_attribute(name, ammount, attribute_name):
    data = read_database()
    new_data = []

    match attribute_name:
        case "points":
            for dict in data:
                if dict["username"] == name:
                    temp_data = {}
                    temp_data["username"] = dict["username"]
                    temp_data["points"] = dict["points"] + ammount
                    temp_data["work_xp"] = dict["work_xp"]
                    temp_data["last_hello_date"] = dict["last_hello_date"]
                    
                    new_data.append(temp_data)
                else:
                    new_data.append(dict)
            write_database(new_data)
        case "work_xp":
            for dict in data:
                if dict["username"] == name:
                    temp_data = {}
                    temp_data["username"] = dict["username"]
                    temp_data["points"] = dict["points"]
                    temp_data["work_xp"] = dict["work_xp"] + ammount
                    temp_data["last_hello_date"] = dict["last_hello_date"]
                    
                    new_data.append(temp_data)
                else:
                    new_data.append(dict)
            write_database(new_data)


# ===========================================================================


filename = 'points.json'

bot = Bot()
bot.run()
