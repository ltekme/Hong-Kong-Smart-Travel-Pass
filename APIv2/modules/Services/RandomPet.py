import random

from APIv2.config import animals


def getRandomAnimal():
    return random.choice(animals)
