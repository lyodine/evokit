""" Export modules from core.
"""
from core.globals import LogLevel, report
from core.controller import Controller
from core.evaluator import Evaluator
from core.population import Genome
from core.population import Population
from core.population import GenomePool

# TODO: The modules Variator, Evaluator, Genome, etc. are abstract interfaces.
#   A Java programmer might consider naming them, for example, AbstractVariator or AbstractEvaluator.
#   I do not see this convention in Python however. What is your opinion on this?