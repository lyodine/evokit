""" Export modules from core.
"""
from core.controller import Controller
from core.evaluator import Evaluator
from core.population import Individual, Population
from core.selector import Elitist, SimpleSelector
from core.variator import Variator

# TODO: The modules Variator, Evaluator, Genome, etc. are abstract interfaces.
#   A Java programmer might consider naming them, for example, AbstractVariator or AbstractEvaluator.
#   I do not see this convention in Python however. What is your opinion on this?
