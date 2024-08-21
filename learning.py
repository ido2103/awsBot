import discord
from discord.ext import commands
import json
import random
import asyncio
from googlesearch import search

class Buttons(discord.ui.View):
    def __init__(self, bot, answer, question, percentage, votes):
        super().__init__(timeout=300)
        self.bot = bot
        self.answer = answer
        self.question = question
        self.create_buttons(len(answer))
        self.percentage = percentage
        self.votes = votes

    def create_buttons(self, num_answers):
        # Create buttons based on the number of answers
        options = ["A", "B", "C", "D", "E", "F"]
        for i in range(num_answers + 3):
            button = discord.ui.Button(label=options[i], style=discord.ButtonStyle.green)
            button.callback = self.create_callback(options[i])
            self.add_item(button)

        # Add the delete button
        delete_button = discord.ui.Button(label="❌", style=discord.ButtonStyle.red)
        delete_button.callback = self.x_func
        self.add_item(delete_button)

        info_button = discord.ui.Button(label="💬", style=discord.ButtonStyle.blurple)
        info_button.callback = self.help_func
        self.add_item(info_button)

         # Add the Report Question button
        report_button = discord.ui.Button(label="Report Question", style=discord.ButtonStyle.red)
        report_button.callback = self.report_question
        self.add_item(report_button)  # Add the report button


    def create_callback(self, option):
        async def callback(interaction: discord.Interaction):
            await self.check_answer(interaction, option)

        return callback

    async def report_question(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(1274454677890531338)
        if channel:
            await channel.send(f"Question reported: {self.question.split('(')[0]}")
            await interaction.response.send_message("Question has been reported.", ephemeral=True)
        else:
            await interaction.response.send_message("Report channel not found.", ephemeral=True)

    async def check_answer(self, interaction: discord.Interaction, selected: str):
        if selected in self.answer:
            final_message = f'{selected} is Correct, according to '
            if self.votes != 'PDF':
                final_message += f'{self.percentage}% of voters ({self.votes} people.)'
            else:
                final_message += 'the PDF'
            await interaction.response.send_message(final_message, ephemeral=True)
            self.add_stats(interaction.user, True)
        else:
            await interaction.response.send_message(f"{selected} is Wrong!", ephemeral=True)
            self.add_stats(interaction.user, False)

    def add_stats(self, user, is_correct):
        with open("stats.json", "r+") as stats_file:
            stats = json.load(stats_file)
            user_stats = next((item for item in stats if item["user"] == user.name), None)
            if user_stats is None:
                user_stats = {"user": user.name, "correct": 0, "incorrect": 0}
                stats.append(user_stats)
            if is_correct:
                user_stats["correct"] += 1
            else:
                user_stats["incorrect"] += 1
            stats_file.seek(0)
            json.dump(stats, stats_file, indent=4)

    async def x_func(self, interaction: discord.Interaction):
        await interaction.response.send_message("Deleting the question in 3 seconds.", ephemeral=True)
        await asyncio.sleep(3)
        await interaction.message.delete()

    async def help_func(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)  # Acknowledge the interaction immediately
        try:
            for result in search(f"Examtopic SAA-C03 {self.question}", stop=1):
                await interaction.followup.send(result, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)


class TestButtons(discord.ui.View):
    def __init__(self, answer, question_id, results, max_selections):
        super().__init__(timeout=7200)
        self.answer = answer
        self.question_id = question_id
        self.results = results
        self.max_selections = max_selections
        self.selected_options = []
        self.create_buttons()

    def create_buttons(self):
        options = ["A", "B", "C", "D", "E", "F"]
        for option in options[:len(self.answer) + 3]:  # Ensure we don't exceed the number of options available
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.green)
            button.callback = self.create_callback(option)
            self.add_item(button)

    def create_callback(self, option):
        async def callback(interaction: discord.Interaction):
            await self.record_answer(interaction, option)
        return callback

    async def record_answer(self, interaction: discord.Interaction, selected: str):
        if selected in self.selected_options:
            self.selected_options.remove(selected)
        else:
            if len(self.selected_options) < self.max_selections:
                self.selected_options.append(selected)
            else:
                await interaction.response.send_message(f"You can only select {self.max_selections} options.", ephemeral=True)
                return

        self.results[interaction.user.name][self.question_id] = self.selected_options

        for item in self.children:
            if isinstance(item, discord.ui.Button):
                if item.label in self.selected_options:
                    item.style = discord.ButtonStyle.blurple
                else:
                    item.style = discord.ButtonStyle.green

        await interaction.response.edit_message(view=self)

    async def on_error(self, interaction: discord.Interaction, item, error: Exception) -> None:
        await interaction.response.send_message(str(error))


async def send_statistics(ctx, user, questions, results):
    num_correct = 0
    total_score = 0
    correct_questions = []
    incorrect_questions = []

    for i, question_data in enumerate(questions):
        question_text = question_data["question"]
        correct_answer = question_data["answer"]
        user_answers = results[user.name].get(i, [])

        # Extract only the question number
        question_number = question_text.split(")", 1)[0] + ")"
        question_number = question_number.split()[1]  # Only keep the question number (e.g., "Question 1)")

        # Calculate points based on the number of correct answers matched by the user
        correct_count = sum(1 for ans in user_answers if ans in correct_answer)
        total_score += correct_count * 2  # 2 points per correct answer

        if correct_count == len(correct_answer):
            num_correct += 1
            correct_questions.append(f"Question {question_number}")
        else:
            incorrect_questions.append(f"Question {question_number}")

    stats_embed = discord.Embed(colour=discord.Colour.green(), title="Test Results")
    stats_embed.add_field(name="Correct Questions", value=num_correct, inline=False)
    stats_embed.add_field(name="Total Score", value=f"{total_score} / {len(questions) * 2 * len(correct_answer)}",
                          inline=False)

    try:
        await user.send(embed=stats_embed)
    except discord.Forbidden:
        await ctx.send(embed=stats_embed)

    detailed_embed = discord.Embed(colour=discord.Colour.blue(), title="Detailed Results")

    # Joining the question numbers into strings and ensuring they don't exceed 1024 characters
    correct_str = "\n".join(correct_questions)[:1024]
    incorrect_str = "\n".join(incorrect_questions)[:1024]

    if correct_questions:
        detailed_embed.add_field(name="Questions Correct", value=correct_str, inline=False)
    if incorrect_questions:
        detailed_embed.add_field(name="Questions Incorrect", value=incorrect_str, inline=False)

    try:
        await user.send(embed=detailed_embed)
    except discord.Forbidden:
        await ctx.send(embed=detailed_embed)


class DeleteTestChannelView(discord.ui.View):
    def __init__(self, cog, channel_id):
        super().__init__()
        self.cog = cog
        self.channel_id = channel_id

    @discord.ui.button(label="Delete Test Channel", style=discord.ButtonStyle.danger)
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator:
            await self.cog.delete_test_channel(interaction, self.channel_id)
        else:
            await interaction.response.send_message("You don't have permission to delete this channel.", ephemeral=True)


class Learning(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_channel_id = 1266059945971810404
        self.admin_embed_messages = {}
        self.active_tests = set()  # Store users with active tests

    @commands.command(aliases=["q"])
    async def question(self, ctx, *args):
        """Used to get a random question from the pool.
        Can be used with a question number to get a specific question.
        Can also be used with subject keywords to filter questions.
        Example: `!q`, `!q 216`, `!q eks`."""
        async def get_embed():
            with open("questions_scraped_answers.json", "r") as file:
                questions = json.load(file)
                filtered_questions = []

                if args:
                    try:
                        number = int(args[0])
                        if number > len(questions):
                            await ctx.send(f"There's only {len(questions)} available questions.")
                            raise IndexError
                        chosen_question = questions[number-1]
                    except ValueError:
                        subjects = [arg.lower() for arg in args]
                        for question in questions:
                            if any(subject in question["question"].lower().split('aa.')[0] for subject in subjects):
                                filtered_questions.append(question)
                                print(question["question"].lower().split('A.')[0])
                        if not filtered_questions:
                            filtered_questions = questions
                        chosen_question = random.choice(filtered_questions)
                else:
                    chosen_question = random.choice(questions)

                question = chosen_question["question"]
                answer = chosen_question["answer"]
                percentage = chosen_question["percentage"]
                votes = chosen_question["num-votes"]
            splitted = question.split(")", 1)
            title = splitted[0] + ")"
            body = splitted[1]
            a_body = body.split("A.")
            b_body = body.split("B.")
            c_body = body.split("C.")
            d_body = body.split("D.")
            a_body_final = b_body[0].split("A.")
            b_body_final = c_body[0].split("B.")
            c_body_final = d_body[0].split("C.")
            list_of_finals = [{"name": "A.", "value": a_body_final[1]}, {"name": "B.", "value": b_body_final[1]},
                            {"name": "C.", "value": c_body_final[1]}]
            if "E." in body:
                e_body = body.split('E.')
                d_body_final = e_body[0].split("D.")
                list_of_finals.append({"name": "D.", "value": d_body_final[1]})
                list_of_finals.append({"name": "E.", "value": e_body[1]})
                if "F." in body:
                    f_body = body.split('F.')
                    e_body_final = f_body[0].split("F.")
                    list_of_finals.append({"name": "F.", "value": f_body[1]})
            else:
                list_of_finals.append({"name": "D.", "value": d_body[1]})
            question = a_body[0]
            embed = discord.Embed(colour=1, title=title, description=question)
            for field in list_of_finals:
                embed.add_field(name=field["name"], value=field["value"], inline=False)
            return embed, answer, title, percentage, votes
        embed, answer, title, percentage, votes = await get_embed()
        buttons = Buttons(self.bot, answer, title, percentage, votes)
        message = await ctx.send(embed=embed, view=buttons)
        await asyncio.sleep(300)
        try:
            await message.delete()
        except Exception: pass

    async def run_timer(self, channel, duration_seconds):
        timer_message = await channel.send("Time remaining: 2:00:00")
        
        for remaining in range(duration_seconds - 1, -1, -1):
            minutes, seconds = divmod(remaining, 60)
            hours, minutes = divmod(minutes, 60)
            await asyncio.sleep(1)
            await timer_message.edit(content=f"Time remaining: {hours:02d}:{minutes:02d}:{seconds:02d}")

    async def delete_test_channel(self, interaction: discord.Interaction, channel_id: int):
        await interaction.response.defer(ephemeral=True)
        
        channel = self.bot.get_channel(channel_id)
        
        if channel:
            user = channel.guild.get_member_named(channel.name.split('-')[0])
            
            if user and user.id in self.active_tests:
                self.active_tests.remove(user.id)

            try:
                await channel.delete()
                
            except Exception as e:
                await interaction.followup.send(f"Error deleting channel: {e}", ephemeral=True)
                return

            if channel_id in self.admin_embed_messages:
                try:
                    await self.admin_embed_messages[channel_id].delete()
                    del self.admin_embed_messages[channel_id]
                except Exception:
                    pass

            await interaction.followup.send(f"Test channel {channel.name} has been deleted.", ephemeral=True)
        else:
            await interaction.followup.send("Channel not found.", ephemeral=True)

    @commands.command()
    async def test(self, ctx, *args):
        """Used to start a test.
        Can be used with subject keywords to filter questions.
        Example: `!test eks ecs`."""
        guild = ctx.guild
        user = ctx.author
        amount_of_questions = 65

        if user.id in self.active_tests:
            active_test_channel = discord.utils.get(guild.channels, name=f"{user.name}-test")
            if active_test_channel:
                await ctx.send(f"You already have an active test. Please complete or end it before starting a new one.\n"
                               f"You can return to your active test here: {active_test_channel.jump_url}")
            else:
                await ctx.send("You already have an active test. Please complete or end it before starting a new one.")
            return

        self.active_tests.add(user.id)

        # Send initial message
        initial_message = await ctx.send("Creating the test. It might take a few minutes. "
                                         "If nothing happens in 5 minutes contact the developer.")

        # Find or create the 'Tests' category
        tests_category = discord.utils.get(guild.categories, name='Tests')
        if not tests_category:
            tests_category = await guild.create_category('Tests')

        # Create the test channel under the 'Tests' category
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=False)
        }
        channel = await guild.create_text_channel(
            f"{user.name}-test",
            category=tests_category,
            overwrites=overwrites
        )
        
        # Create an embed for the admin channel
        admin_embed = discord.Embed(
            title="New Test Started",
            color=discord.Color.blue()
        )
        admin_embed.add_field(name="User", value=f"{user.mention} | {user.name}", inline=False)
        admin_embed.add_field(name="Arguments", value=" ".join(args) if args else "None", inline=False)
        admin_embed.add_field(name="Test Channel", value=f"{channel.mention} (ID: {channel.id})", inline=False)
        admin_embed.set_footer(text=f"Test started at {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        # Create the DeleteTestChannelView
        view = DeleteTestChannelView(self, channel.id)

        # Send the embed with the button to the admin channel
        admin_channel = self.bot.get_channel(self.admin_channel_id)
        if admin_channel:
            admin_embed_message = await admin_channel.send(embed=admin_embed, view=view)
            self.admin_embed_messages[channel.id] = admin_embed_message

        # Load questions and filter based on subjects
        with open("questions_scraped_answers.json", "r") as file:
            questions = json.load(file)
            filtered_questions = []

            if args:
                if args[0].isnumeric():
                    amount_of_questions = int(args[0])
                    args = list(args)
                subjects = [arg.lower() for arg in args]
                for question in questions:
                    if any(subject in question["question"].lower() for subject in subjects):
                        filtered_questions.append(question)

            # If not enough filtered questions, fill the rest with random questions
            if len(filtered_questions) < amount_of_questions:
                remaining_questions = [q for q in questions if q not in filtered_questions]
                filtered_questions += random.sample(remaining_questions, amount_of_questions - len(filtered_questions))

            selected_questions = random.sample(filtered_questions, amount_of_questions)
        results = {user.name: {}}

        # Send all questions at the beginning
        for i, chosen_question in enumerate(selected_questions):
            try:
                question = chosen_question["question"]
                answer = chosen_question["answer"]
                splitted = question.split(")", 1)
                title = "Question " + str(i+1)
                body = splitted[1]
                a_body = body.split("A.")
                b_body = body.split("B.")
                c_body = body.split("C.")
                d_body = body.split("D.")
                a_body_final = b_body[0].split("A.")
                b_body_final = c_body[0].split("B.")
                c_body_final = d_body[0].split("C.")
                list_of_finals = [{"name": "A.", "value": a_body_final[1]}, {"name": "B.", "value": b_body_final[1]},
                                {"name": "C.", "value": c_body_final[1]}]
                if "E." in body:
                    e_body = body.split('E.')
                    d_body_final = e_body[0].split("D.")
                    list_of_finals.append({"name": "D.", "value": d_body_final[1]})
                    list_of_finals.append({"name": "E.", "value": e_body[1]})
                    if "F." in body:
                        f_body = body.split('F.')
                        e_body_final = f_body[0].split("F.")
                        list_of_finals.append({"name": "F.", "value": f_body[1]})
                else:
                    list_of_finals.append({"name": "D.", "value": d_body[1]})
                question = a_body[0]
                embed = discord.Embed(colour=1, title=title, description=question)
                for field in list_of_finals:
                    embed.add_field(name=field["name"], value=field["value"], inline=False)

                # Determine max selections based on question text
                max_selections = 1
                if "(Choose two.)" in question:
                    max_selections = 2
                elif "(Choose three.)" in question:
                    max_selections = 3

                buttons = TestButtons(answer, i, results, max_selections)
                await channel.send(embed=embed, view=buttons)
            except Exception as e:
                raise e

        # Update the permissions to allow the user to see and interact with the channel
        await channel.set_permissions(user, read_messages=True, send_messages=True)

        # Send the initial message in the test channel
        await channel.send(f"Hello {user.mention}, your test has begun. You have 120 minutes to complete it. \n"
                           f"Please write 'done' when you're done.\n"
                           f"You can return to this test using this link: {channel.jump_url}")

        # If you want to send a DM to the user with the link as well, you can add:
        await initial_message.edit(content=f"Test created successfully. You can access your test here: {channel.jump_url}\n"
                                           f"If you can't see the channel, please wait a few moments and try again.")

        # Start the timer
        timer_task = asyncio.create_task(self.run_timer(channel, 7200))

        # Wait for 120 minutes or until the user types "done"
        def check_done(m):
            return m.content.lower() == "done" and m.channel == channel and m.author == user

        try:
            await asyncio.wait_for(self.bot.wait_for('message', check=check_done), timeout=7200)
        except asyncio.TimeoutError:
            pass
        finally:
            # Remove user from active tests when the test ends
            self.active_tests.remove(user.id)

            # Cancel the timer task
            timer_task.cancel()

            await send_statistics(ctx, user, selected_questions, results)
            await channel.delete()
            if channel.id in self.admin_embed_messages:
                await self.admin_embed_messages[channel.id].delete()
                del self.admin_embed_messages[channel.id]


async def setup(bot):
    await bot.add_cog(Learning(bot))
