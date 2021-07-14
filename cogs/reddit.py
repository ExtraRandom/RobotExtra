from discord.ext import commands
from cogs.utils import perms, IO, time_formatting as timefmt
from cogs.utils import ez_utils
import asyncpraw
# import discord

# https://asyncpraw.readthedocs.io/en/latest/getting_started/quick_start.html


class Reddit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://www.reddit.com"

        reddit_login = IO.read_settings_as_json()
        reddit_data = reddit_login['reddit']

        username = reddit_data['username']
        password = reddit_data['password']
        client_id = reddit_data['client_id']
        client_secret = reddit_data['client_secret']
        user_agent = reddit_data['user_agent']
        self.post_title = reddit_data['post_title']
        self.post_url = reddit_data['post_url']

        if username is None or password is None or client_id is None or client_secret is None or user_agent is None or \
                self.post_title is None or self.post_url is None:
            cmds = Reddit.get_commands(self)
            for cmd in cmds:
                cmd.update(enabled=False)
        else:
            self.reddit = asyncpraw.Reddit(
                username=username,
                password=password,
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )

    @commands.command(enabled=False, hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def rtest(self, ctx):
        """reddit test post"""
        await ctx.send("submitting test post")

        sr = await self.reddit.subreddit("test")
        tp = await sr.submit("api test", selftext="testing testing 1 2 3")
        await tp.load()

        await ctx.send("https://www.reddit.com{}".format(tp.permalink))

    @commands.command(name="pds", hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def post_discord_server(self, ctx):
        """Post server ad on r/discordservers"""
        sub = "discordservers"
        await self.post_advert(self.reddit, ctx, sub, self.post_title, self.post_url)

    @commands.command(name="pdas", hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def post_discord_app_server(self, ctx):
        """Post server ad on r/DiscordAppServers"""
        sub = "DiscordAppServers"
        await self.post_advert(self.reddit, ctx, sub, self.post_title, self.post_url)

    @commands.command(name="findold", hidden=True)
    @perms.is_dev()
    @perms.is_in_somewhere_nice()
    async def find_old(self, ctx):
        """Find previous reddit posts"""
        me = await self.reddit.user.me()
        async for post in me.new():
            title = post.title
            age = timefmt.time_ago(post.created_utc, force_into_utc=True)

            sr = post.subreddit
            url = self.base_url + post.permalink

            await ctx.send(embed=ez_utils.quick_embed(
                title=title, description="Posted on r/{}".format(sr),
                fields=[("Post Age", age), ("URL", url)]
            ))

    @staticmethod
    async def post_advert(reddit, ctx, sub: str, post_title: str, post_url: str):
        deleted_old = False
        text = "Searching for previous post..."
        msg = await ctx.send(text)

        me = await reddit.user.me()
        async for post in me.new():
            if post.subreddit == sub:
                await post.delete()
                deleted_old = True
                break

        if deleted_old:
            text += " Found and deleted"
        else:
            text += " No previous post found"

        await msg.edit(content=text)

        text += "\nPosting new advert on r/{}".format(sub)
        await msg.edit(content=text)

        r_sub = await reddit.subreddit(sub)

        n_post = await r_sub.submit(
            title=post_title,
            url=post_url)
        await n_post.load()

        text += "\nNew Advert posted\nLink:\n<https://www.reddit.com{}>".format(n_post.permalink)
        await msg.edit(content=text)


def setup(bot):
    bot.add_cog(Reddit(bot))
