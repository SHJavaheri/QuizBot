import discord
from openai import OpenAI

from discord.ext import commands
import os
from dotenv import load_dotenv
from fpdf import FPDF
from quiz_manager import QuizManager
from openai import OpenAI
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
client = OpenAI()


# Initialize bot and QuizManager
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
quiz_manager = QuizManager()


# Hint generation function
def generate_hint(question_text):
    response = client.chat.completions.create(model="gpt-3.5-turbo",  # Updated to the latest available model
    messages=[
        {"role": "system", "content": "You are a helpful assistant that provides hints."},
        {"role": "user", "content": f"Provide a helpful hint for this question: {question_text}"}
    ],
    max_tokens=50,
    temperature=0.5)
    hint = response.choices[0].message.content.strip()
    return hint if hint else "No hint available."


class StartQuizView(discord.ui.View):
    """Initial view showing the 'Start Quiz' and 'Take this to Threads' buttons."""

    def __init__(self, bot, quiz_manager):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager

    @discord.ui.button(label="Start Quiz", style=discord.ButtonStyle.green, custom_id="start_quiz")
    async def start_quiz_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.quiz_manager.is_quiz_active():
            await interaction.response.send_message("A quiz is already active. Use 'End Quiz' to finalize it first.")
        else:
            self.quiz_manager.start_new_quiz()
            await interaction.response.send_message(
                "New quiz session started! Use 'Add Question' to add questions.",
                view=QuestionTypeView(self.bot, self.quiz_manager)
            )

    @discord.ui.button(label="Take this to Threads", style=discord.ButtonStyle.blurple, custom_id="take_to_threads")
    async def take_to_threads_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the interaction to prevent "interaction failed" message
        await interaction.response.defer()

        # Create a thread with the user's name
        thread = await interaction.channel.create_thread(
            name=f"{interaction.user.display_name}'s Quiz Thread",
            type=discord.ChannelType.public_thread,
            reason="Starting quiz in a thread"
        )
        await thread.send(
            f"{interaction.user.mention} Ready to create your quiz in this thread! Use the buttons to start.")

        # Redirect the quiz creation to the thread
        await thread.send("New quiz session started! Use 'Add Question' to add questions.",
                          view=QuestionTypeView(self.bot, self.quiz_manager))


class QuestionTypeView(discord.ui.View):
    """View to select the type of question (Multiple Choice, True/False, Solution, or End Quiz)."""

    def __init__(self, bot, quiz_manager):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager

    @discord.ui.button(label="Multiple Choice", style=discord.ButtonStyle.primary, custom_id="multiple_choice")
    async def multiple_choice_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_multiple_choice_question(interaction)  # Directly call the handler without an initial message

    @discord.ui.button(label="True/False", style=discord.ButtonStyle.primary, custom_id="true_false")
    async def true_false_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the interaction to keep it active for follow-up messages
        await interaction.response.defer()
        await self.handle_true_false_question(interaction)

    @discord.ui.button(label="Solution", style=discord.ButtonStyle.primary, custom_id="solution")
    async def solution_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Enter the question for Solution:")
        await self.handle_solution_question(interaction)

    @discord.ui.button(label="End Quiz", style=discord.ButtonStyle.red, custom_id="end_quiz")
    async def end_quiz_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.quiz_manager.end_quiz()
        await interaction.response.send_message(
            "Quiz finalized! You can now take the quiz or print it as a PDF.",
            view=EndQuizOptionsView(self.bot, self.quiz_manager)
        )

    async def handle_multiple_choice_question(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        # Step 1: Ask for question text
        await interaction.response.send_message("Enter the question text for Multiple Choice:")
        question_msg = await self.bot.wait_for("message", check=check)
        question_text = question_msg.content

        # Step 2: Ask for multiple-choice options
        await interaction.followup.send("Enter all options separated by commas (e.g., option1, option2, option3):")
        options_msg = await self.bot.wait_for("message", check=check)
        options = [opt.strip() for opt in options_msg.content.split(",")]

        if len(options) < 2:
            await interaction.followup.send("Please enter at least two options for a multiple-choice question.")
            return

        # Step 3: Generate a hint automatically
        hint_text = generate_hint(question_text)

        # Step 4: Display options as buttons to select the correct answer
        await interaction.followup.send(
            "Now select the correct answer from the options provided:",
            view=MultipleChoiceAnswerView(self.bot, self.quiz_manager, question_text, options, hint=hint_text)
        )


    async def handle_true_false_question(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        # Use follow-up to prompt for the question text without a primary response
        await interaction.followup.send("Enter the question text for True/False:")
        question_msg = await self.bot.wait_for("message", check=check)
        question_text = question_msg.content

        # Generate a hint automatically
        hint_text = generate_hint(question_text)

        # Display True/False buttons to select the correct answer
        await interaction.followup.send(
            "Select the correct answer for this True/False question:",
            view=TrueFalseAnswerView(self.bot, self.quiz_manager, question_text, hint=hint_text)
        )


    async def handle_solution_question(self, interaction: discord.Interaction):
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        question_msg = await self.bot.wait_for("message", check=check)
        question_text = question_msg.content

        await interaction.followup.send("What is the answer?")
        answer_msg = await self.bot.wait_for("message", check=check)
        answer_text = answer_msg.content

        # Generate hint automatically
        hint_text = generate_hint(question_text)

        # Add the question with generated hint to the quiz manager
        self.quiz_manager.add_question("solution", question_text, answer_text, hint=hint_text)
        await interaction.followup.send("Question added! Select the type of the next question or 'End Quiz' to finish.",
                                        view=QuestionTypeView(self.bot, self.quiz_manager))


# Hint view to show "Show Hint" button
class HintButtonView(discord.ui.View):
    """View to display a 'Show Hint' button that reveals a hint."""

    def __init__(self, hint):
        super().__init__()
        self.hint = hint

    @discord.ui.button(label="Show Hint", style=discord.ButtonStyle.secondary)
    async def show_hint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hint:
            await interaction.response.send_message(f"Hint: {self.hint}")
        else:
            await interaction.response.send_message("No hint available for this question.")
        self.stop()


class MultipleChoiceAnswerView(discord.ui.View):
    """View to display multiple-choice options as buttons for selecting the correct answer."""

    def __init__(self, bot, quiz_manager, question_text, options, correct_answer=None, hint=None):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager
        self.question_text = question_text
        self.options = options
        self.correct_answer = correct_answer
        self.hint = hint
        self.correct = False  # Track if answer is correct

        # Dynamically create buttons for each option with individual callbacks
        for option in options:
            button = discord.ui.Button(label=option, style=discord.ButtonStyle.primary)
            button.callback = self.create_callback(option)  # Set callback dynamically for each button
            self.add_item(button)

    def create_callback(self, selected_option):
        """Creates a callback for each option button to set the answer and verify correctness."""

        async def callback(interaction: discord.Interaction):
            # Set whether the selected option is correct
            self.correct = (selected_option == self.correct_answer)

            # If correct_answer is None, we are in creation mode, so save the question
            if self.correct_answer is None:
                self.quiz_manager.add_question("multiple_choice", self.question_text, selected_option, self.options,
                                               hint=self.hint)
                await interaction.response.send_message(
                    f"Selected '{selected_option}' as the correct answer. Question added!")
                await interaction.followup.send("Select the type of the next question or 'End Quiz' to finish.",
                                                view=QuestionTypeView(self.bot, self.quiz_manager))
            else:
                # If correct_answer is provided, we're in quiz-taking mode
                await interaction.response.defer()
            self.stop()

        return callback


class TrueFalseAnswerView(discord.ui.View):
    """View to display True/False options as buttons for selecting the correct answer."""
    def __init__(self, bot, quiz_manager, question_text, correct_answer=None, hint=None):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager
        self.question_text = question_text
        self.correct_answer = correct_answer
        self.hint = hint  # Store hint
        self.correct = False  # Track if the answer is correct

    @discord.ui.button(label="True", style=discord.ButtonStyle.success)
    async def true_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # During quiz-taking: Check if "True" is the correct answer
        self.correct = (self.correct_answer == "True")
        if self.correct_answer is None:
            # During question creation: Set "True" as the correct answer
            self.quiz_manager.add_question("true_false", self.question_text, "True", hint=self.hint)
            await interaction.response.send_message("Selected 'True' as the correct answer. Question added!")
            await interaction.followup.send("Select the type of the next question or 'End Quiz' to finish.", view=QuestionTypeView(self.bot, self.quiz_manager))
        else:
            # Response during quiz-taking
            await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="False", style=discord.ButtonStyle.danger)
    async def false_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # During quiz-taking: Check if "False" is the correct answer
        self.correct = (self.correct_answer == "False")
        if self.correct_answer is None:
            # During question creation: Set "False" as the correct answer
            self.quiz_manager.add_question("true_false", self.question_text, "False", hint=self.hint)
            await interaction.response.send_message("Selected 'False' as the correct answer. Question added!")
            await interaction.followup.send("Select the type of the next question or 'End Quiz' to finish.", view=QuestionTypeView(self.bot, self.quiz_manager))
        else:
            # Response during quiz-taking
            await interaction.response.defer()
        self.stop()




# Quiz interaction function, now with hints
async def start_quiz_interaction(interaction, bot):
    questions = quiz_manager.get_questions()
    correct_answers = 0

    for q in questions:
        # Create a combined view with both the question interaction and hint button
        if q['type'] == 'multiple_choice':
            view = MultipleChoiceAnswerView(bot, quiz_manager, q['question'], q['options'], q['answer'])
            view.add_item(HintButton(q.get('hint')))  # Add hint button to the multiple choice view
            await interaction.followup.send(
                f"**Question:** {q['question']}\n(Click 'Show Hint' if you need help)",
                view=view
            )
            await view.wait()
            if view.correct:
                correct_answers += 1
                await interaction.followup.send("Correct!")
            else:
                await interaction.followup.send(f"Incorrect! The correct answer was: {q['answer']}")

        elif q['type'] == 'true_false':
            view = TrueFalseAnswerView(bot, quiz_manager, q['question'], q['answer'])
            view.add_item(HintButton(q.get('hint')))  # Add hint button to the true/false view
            await interaction.followup.send(
                f"**Question:** {q['question']}\n(Click 'Show Hint' if you need help)",
                view=view
            )
            await view.wait()
            if view.correct:
                correct_answers += 1
                await interaction.followup.send("Correct!")
            else:
                await interaction.followup.send(f"Incorrect! The correct answer was: {q['answer']}")

        else:  # Solution questions where the answer is typed
            view = HintButtonView(q.get('hint'))  # Add hint button only
            await interaction.followup.send(
                f"**Question:** {q['question']}\nProvide your answer below.\n(Click 'Show Hint' if you need help)",
                view=view
            )
            answer_msg = await bot.wait_for("message", check=lambda m: m.author == interaction.user)
            if answer_msg.content.lower() == q['answer'].lower():
                correct_answers += 1
                await interaction.followup.send("Correct!")
            else:
                await interaction.followup.send(f"Incorrect! The correct answer was: {q['answer']}")

    # Calculate results
    total_questions = len(questions)
    percentage = (correct_answers / total_questions) * 100
    grade = "A+" if percentage >= 96 else "A" if percentage >= 87 else "A-" if percentage >= 80 else "B+" if percentage >= 77 else \
        "B" if percentage >= 72 else "B-" if percentage >= 70 else "C+" if percentage >= 67 else "C" if percentage >= 63 else \
            "C-" if percentage >= 60 else "D+" if percentage >= 57 else "D" if percentage >= 54 else "D-" if percentage >= 51 else "F"
    pass_fail = "Passed" if percentage >= 50 else "Failed"

    await interaction.followup.send(
        f"Quiz complete! Score: {correct_answers}/{total_questions} ({percentage:.2f}%)\nGrade: {grade}\nResult: {pass_fail}",
        view=PrintAfterQuizView(bot, quiz_manager)
    )

class HintButton(discord.ui.Button):
    def __init__(self, hint):
        super().__init__(label="Show Hint", style=discord.ButtonStyle.secondary)
        self.hint = hint

    async def callback(self, interaction: discord.Interaction):
        if self.hint:
            await interaction.response.send_message(f"Hint: {self.hint}", ephemeral=True)
        else:
            await interaction.response.send_message("No hint available for this question.", ephemeral=True)



class PrintAfterQuizView(discord.ui.View):
    """View to allow printing the quiz as a PDF after taking the quiz."""

    def __init__(self, bot, quiz_manager):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager

    @discord.ui.button(label="Print Quiz as PDF", style=discord.ButtonStyle.blurple, custom_id="print_pdf")
    async def print_pdf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        questions = self.quiz_manager.get_questions()
        for q in questions:
            pdf.cell(0, 10, f"Q: {q['question']}", ln=True)
            if q['type'] == "multiple_choice":
                options_text = ", ".join(q["options"])
                pdf.cell(0, 10, f"Options: {options_text}", ln=True)
            pdf.cell(0, 10, f"Answer: {q['answer']}", ln=True)
            pdf.cell(0, 10, "", ln=True)  # Add a blank line between questions

        pdf_output = "quiz_output.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as file:
            await interaction.response.send_message("Here is your quiz in PDF format:", file=discord.File(file, pdf_output))


class EndQuizOptionsView(discord.ui.View):
    """View to show options after quiz is finalized: Take Quiz or Print PDF."""

    def __init__(self, bot, quiz_manager):
        super().__init__()
        self.bot = bot
        self.quiz_manager = quiz_manager

    @discord.ui.button(label="Take Quiz", style=discord.ButtonStyle.green, custom_id="take_quiz")
    async def take_quiz_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()  # To avoid timeout on long processes
        questions = self.quiz_manager.get_questions()
        if not questions:
            await interaction.followup.send(
                "No questions available! Use 'Start Quiz' and 'Add Question' to create a quiz first.")
            return

        # Start the quiz interaction process
        await start_quiz_interaction(interaction, self.bot)

    @discord.ui.button(label="Print Quiz as PDF", style=discord.ButtonStyle.blurple, custom_id="print_pdf")
    async def print_pdf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        questions = self.quiz_manager.get_questions()
        for q in questions:
            pdf.cell(0, 10, f"Q: {q['question']}", ln=True)
            if q['type'] == "multiple_choice":
                options_text = ", ".join(q["options"])
                pdf.cell(0, 10, f"Options: {options_text}", ln=True)
            pdf.cell(0, 10, f"Answer: {q['answer']}", ln=True)
            pdf.cell(0, 10, "", ln=True)  # Add a blank line between questions

        pdf_output = "QuizBot.pdf"
        pdf.output(pdf_output)

        with open(pdf_output, "rb") as file:
            await interaction.response.send_message("Here is your quiz in PDF format:", file=discord.File(file, pdf_output))


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

    # Dictionary to map each server (guild) ID to a specific channel ID
    startup_channels = {
        785377434022314005: 1300861955623358494,  # Replace with actual server and channel IDs
        799860863732416532: 1300729764843356222
        # Add more servers and channels as needed
    }

    # Loop through each server and its specified channel
"""    for guild_id, channel_id in startup_channels.items():
        guild = bot.get_guild(guild_id)  # Fetch the guild
        if guild:
            channel = guild.get_channel(channel_id)  # Fetch the specific channel
            if channel:
                await channel.send("Ready to make a quiz for you! Just type `!quiz` to start!")
            else:
                print(f"Channel ID {channel_id} not found in guild {guild.name}")
        else:
            print(f"Guild ID {guild_id} not found")"""


@bot.command(name="quiz")
async def quiz(ctx):
    view = StartQuizView(bot, quiz_manager)
    await ctx.send("Welcome to the Quiz Bot! Use the buttons below to start the quiz:", view=view)


@bot.command(name="closethread")
async def close_thread(ctx):
    if isinstance(ctx.channel, discord.Thread):
        # Inform the user of closure before deleting the thread
        await ctx.send(f"{ctx.author.mention} Thread will be closed in 5 seconds.", delete_after=5)

        # Wait for 5 seconds before deleting the thread
        await asyncio.sleep(5)
        await ctx.channel.delete()
    else:
        await ctx.send("This command can only be used in a thread.", delete_after=5)


@bot.command(name="quizhelp")
async def help_command(ctx):
    # Ping the user and send instructions
    await ctx.send(f"{ctx.author.mention}\n How to make a quiz:\n"
                   "1. Type `!quiz`\n"
                   "2. Follow Prompts (Ex. Start Quiz, Multiple Choice, etc.)\n"
                   "3. Take Quiz!\n"
                   "4. Optionally Print the Entire Quiz as a PDF File!")

# Run the bot
bot.run(TOKEN)
