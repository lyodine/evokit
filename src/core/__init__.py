""" Export modules from core.
"""
from core.controller import Controller
from core.evaluator import Evaluator
from core.population import Genome
from core.variator import Variator
from core.population import Population
from core.selector import Elitist
from core.selector import SimpleSelector

# TODO: The modules Variator, Evaluator, Genome, etc. are abstract interfaces.
#   A Java programmer might consider naming them, for example, AbstractVariator or AbstractEvaluator.
#   I do not see this convention in Python however. What is your opinion on this?