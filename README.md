# Quiz Bot

A powerful, interactive Quiz Bot for Discord, designed to enhance study sessions and group learning. With features like dynamic question creation, threaded quiz sessions, customizable PDF exports, and a seamless user interface, this bot makes learning and quizzing engaging and organized.

## 🌟 Features

- **Interactive Quiz Creation**: Easily create quizzes with various question types (multiple choice, true/false, solutions).
- **Threaded Sessions**: Start quizzes in dedicated threads for organized and distraction-free interactions.
- **Custom Quiz Naming**: Assign a name to each quiz for easy identification and custom PDF exports.
- **PDF Export**: Generate a PDF of the quiz with questions, options, and answers for future reference or offline study.
- **Hints**: Provide hints to help participants during the quiz.
- **Grading System**: Calculates grades with letter scores and pass/fail results based on performance.

## 🛠 Setup and Installation

Follow these steps to set up the bot:

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/quiz-bot.git
   cd quiz-bot
   ```

2. **Install Dependencies**
   Ensure you have Python 3.8+ installed, then install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**
   Create a `.env` file in the root directory and add your bot token and OpenAI API key:
   ```plaintext
   DISCORD_BOT_TOKEN=your_discord_bot_token
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Run the Bot**
   ```bash
   python QuizBot.py
   ```

## 🚀 Usage

Once the bot is running, use the following commands in your Discord server:

- **Start a Quiz**: Type `!quiz` to initiate the quiz creation process. Follow the prompts to add questions.
- **Take Quiz to Threads**: Choose to create a dedicated thread for quiz creation by selecting the "Take this to Threads" option.
- **Add Questions**: Use interactive buttons to add different types of questions: multiple choice, true/false, or solution-based.
- **Close Thread**: Use `!closethread` within a thread to end and delete the quiz thread.
- **Print Quiz**: Once the quiz is completed, generate a PDF with all questions and answers by clicking the "Print Quiz as PDF" button.

### Example Commands

```plaintext
!quiz          # Start a new quiz
!quiz_help     # Display help for creating quizzes
!closethread   # Close and delete the current thread
```

## 📄 Example PDF Export

Each quiz can be exported as a PDF. The export will include the quiz name, each question with options (if applicable), correct answers, and hints. 

## 📚 Contributing

We welcome contributions to enhance Quiz Bot’s functionality and improve code quality. Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch (`feature/my-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/my-feature`).
5. Create a pull request.

## 🔒 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 📬 Contact

For any questions or suggestions, please feel free to reach out to [your.email@example.com](mailto:your.email@example.com).

## NOTE
This is not an official discord bot, just something I created to help out with school. However, if you are interested in this bot and believe it may help you in your group Discord studies, feel free to use it! Just know, you you won't be able to install this bot like any other 'official' bot on the market. You need to clone the github onto your own IDE (Ex. Pycharm) and simply run it locally!

---

Thank you for using Quiz Bot! We hope it enhances your learning experience.
