
import random

questions = [
  {
    "question": "What is the capital of France?",
    "answers": [
      "London",
      "Paris",
      "Berlin"
    ],
    "correct": 1
  },
  {
    "question": "What is the largest planet in our solar system?",
    "answers": [
      "Jupiter",
      "Earth",
      "Mars"
    ],
    "correct": 0
  },
  {
    "question": "What year did the first iPhone launch?",
    "answers": [
      "2007",
      "2005",
      "2003"
    ],
    "correct": 0
  },
  {
    "question": "What is the tallest mountain in the world?",
    "answers": [
      "Mount Everest",
      "K2",
      "Kangchenjunga"
    ],
    "correct": 0
  },
  {
    "question": "What is the name of the largest ocean on Earth?",
    "answers": [
      "Pacific Ocean",
      "Atlantic Ocean",
      "Indian Ocean"
    ],
    "correct": 0
  },
  {
    "question": "Who painted the Mona Lisa?",
    "answers": [
      "Leonardo da Vinci",
      "Michelangelo",
      "Sandro Botticelli"
    ],
    "correct": 0
  },
  {
    "question": "What is the currency of Japan?",
    "answers": [
      "Yen",
      "Yuan",
      "Won"
    ],
    "correct": 0
  },
  {
    "question": "In which city are the Olympic Games held in 2024?",
    "answers": [
      "Paris",
      "Tokyo",
      "London"
    ],
    "correct": 0
  },
  {
    "question": "What is the chemical symbol for water?",
    "answers": [
      "H2O",
      "CO2",
      "N2"
    ],
    "correct": 0
  },
  {
    "question": "How many sides does a hexagon have?",
    "answers": [
      "6",
      "8",
      "10"
    ],
    "correct": 0
  },
  {
    "question": "What is the largest living organism on Earth?",
    "answers": [
      "Honey fungus",
      "Giant sequoia",
      "Blue whale"
    ],
    "correct": 0
  },
  {
    "question": "What is the capital of Australia?",
    "answers": [
      "Melbourne",
      "Sydney",
      "Canberra"
    ],
    "correct": 2
  },
  {
    "question": "What is the name of the first book in the Harry Potter series?",
    "answers": [
      "Harry Potter and the Chamber of Secrets",
      "Harry Potter and the Philosopher's Stone",
      "Harry Potter and the Prisoner of Azkaban"
    ],
    "correct": 1
  },
  {
    "question": "What is the language spoken in Brazil?",
    "answers": [
      "Spanish",
      "Portuguese",
      "French"
    ],
    "correct": 1
  },
  {
    "question": "What is the highest mountain in North America?",
    "answers": [
      "Mount Denali",
      "Mount Elbert",
      "Mount Rainier"
    ],
    "correct": 0
  },
  {
    "question": "What is the largest desert in the world?",
    "answers": [
      "Sahara Desert",
      "Gobi Desert",
      "Australian Desert"
    ],
    "correct": 0
  },
  {
    "question": "What is the name of the world's longest river?",
    "answers": [
      "Nile River",
      "Amazon River",
      "Yangtze River"
    ],
    "correct": 0
  },
  {
    "question": "What is the chemical symbol for gold?",
    "answers": [
      "Au",
      "Ag",
      "Cu"
    ],
    "correct": 0
  },
  {
    "question": "What is the capital of Germany?",
    "answers": [
      "Berlin",
      "Munich",
      "Hamburg"
    ],
    "correct": 0
  },
  {
    "question": "What is the smallest country in the world?",
    "answers": [
      "Vatican City",
      "Monaco",
      "Nauru"
    ],
    "correct": 0
  },
  {
    "question": "What is the largest living land animal?",
    "answers": [
      "African bush elephant",
      "Giraffe",
      "Hippopotamus"
    ],
    "correct": 0
  },
  {
    "question": "What is the name of the largest moon of Saturn?",
    "answers": [
      "Titan",
      "Rhea",
      "Iapetus"
    ],
    "correct": 0
  }
]

class Question:
    pass

def random_question():

    choice = random.choice(questions)

    q = Question()
    q.question = choice["question"]


    q.answers = [v for v in choice["answers"]]
    q.correct = q.answers[choice["correct"]]
    random.shuffle(q.answers)

    return q

