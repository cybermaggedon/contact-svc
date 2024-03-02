
import random

class Question:
    pass

class QuestionBank:

    def __init__(self, q):
        self.q = q

    def random_question(self):

        choice = random.choice(self.q)

        q = Question()
        q.question = choice["question"]

        q.answers = [v for v in choice["answers"]]
        q.correct = q.answers[choice["correct"]]
        random.shuffle(q.answers)

        return q

