import random

from ...config import animals


def getRandomAnimal():
    return random.choice(animals)
