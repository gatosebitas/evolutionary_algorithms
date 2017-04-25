"""
    @Author: Manuel Lagunas
    @Personal_page: http://giga.cps.unizar.es/~mlagunas/
    @date: March - 2017
"""

import warnings
import numpy as np
import evolutionary.crossovers as crossovers
import evolutionary.initializations as initializations
import evolutionary.mutations as mutations
import evolutionary.replacements as replacements
import evolutionary.selections as selections
import evolutionary.optim_functions as functions
from evolutionary import Logger
from evolutionary import Population


class EAL(object):
    """

    """

    def __init__(self,
                 goal=10 ** -4,
                 n_dimensions=10,
                 n_population=100,
                 n_iterations=1000,
                 n_children=100,
                 xover_prob=0.8,
                 mutat_prob=0.1,
                 minimization=False,
                 initialization='uniform',
                 selection='wheel',
                 crossover='blend',
                 mutation='non_uniform',
                 replacement='elitist',
                 tournament_competitors=3,
                 tournament_winners=1,
                 replacement_elitism=0.5,
                 alpha_prob=0.9,
                 control_alpha=10 ** -2,
                 control_s=6,
                 grid_intervals=20
                 ):
        """

        :param n_dimensions:
        :param n_population:
        :param n_iterations:
        :param n_children:
        :param xover_prob:
        :param mutat_prob:
        :param minimization:
        :param seed:
        :param logger:
        :param initialization:
        :param problem:
        :param selection:
        :param crossover:
        :param mutation:
        :param replacement:
        :param delta: Parameter used in GGA(Grid-based Genetic Algorithms)
        :param control_alpha: Parameter used in GGA(Grid-based Genetic Algorithms)
        :param control_s: Parameter used in GGA(Grid-based Genetic Algorithms)
        :param grid_intervals: Parameter used in GGA(Grid-based Genetic Algorithms)
        """
        self.goal = goal
        self.n_dimensions = n_dimensions
        self.n_population = n_population
        self.n_iterations = n_iterations
        self.n_children = n_children
        self.xover_prob = xover_prob
        self.mutat_prob = mutat_prob
        self.minimization = minimization
        self.initialization = initialization
        self.selection = selection
        self.crossover = crossover
        self.mutation = mutation
        self.replacement = replacement
        self.tournament_competitors = tournament_competitors
        self.tournament_winners = tournament_winners
        self.replacement_elitism = replacement_elitism
        self.alpha_prob = alpha_prob
        self.control_alpha = control_alpha
        self.control_s = control_s
        self.grid_intervals = grid_intervals

        np.set_printoptions(formatter={'float': lambda x: "{0:0.4f}".format(x)}, linewidth=np.nan)

    def fit(self, problem=functions.Ackley,
            ea_type="ga", iter_log=-1, seeds=np.array(12345)):
        """

        :param ea_type:
        :param iter_log:
        :param seed:
        :return:
        """

        # Create the logger object to store the data during the evolutionary process
        seeds = np.array([seeds]) if not type(seeds) is np.ndarray else seeds

        # Initialize variables
        logger = [Logger(iter_log=iter_log) for i in range(len(seeds))]
        best = [None] * len(seeds)

        # Define the problem to solve and get its fitness function
        problem = problem(minimize=self.minimization)
        fitness_function = problem.evaluate

        # Set the dimensions of the problem
        if problem.dim and self.n_dimensions > problem.dim:
            warnings.warn("Changing the number of dimensions of the problem from "
                          + str(self.n_dimensions) + " to " + str(problem.dim))
        self.n_dimensions = self.n_dimensions if not problem.dim else problem.dim

        # Define the bounds to explore the problem
        upper = np.ones((self.n_population, self.n_dimensions)) * problem.upper
        lower = np.ones((self.n_population, self.n_dimensions)) * problem.lower  # Print the best value we have obtained

        # Print a description of the problem
        Logger(-1).print_description({"Problem to solve:": problem.name},
                                     {"Strategy followed:": ea_type,
                                      "Number of problem dimensions": self.n_dimensions,
                                      "Size of the population": self.n_population,
                                      "Max. number of iterations": self.n_iterations,
                                      "Crossover probability": self.xover_prob,
                                      "Mutation probability": self.mutat_prob})

        for i in range(len(seeds)):
            # Perform the evolutionary process
            logger[i], best[i] = _iterate(self, logger[i], upper, lower, fitness_function, ea_type, seeds[i])
            if len(best[i]) > 0:
                # Print the results
                logger[i].print_description({"Seed used:": seeds[i],
                                             "Iteration": i+1},
                                            best[i])
                # Plot the graph with all the results
                # logger.plot(np.array(['mean', 'worst', 'best']))


def _iterate(self, logger, upper, lower, fitness_function, ea_type, seed):
    """

    :param self:
    :param logger:
    :param upper:
    :param lower:
    :param fitness_function:
    :param ea_type:
    :param seed:
    :return:
    """

    # Set a random generator seed to reproduce the same experiments
    np.random.seed(seed)

    try:

        ########################################################################################################
        # Create the class Population and initialize its chromosomes
        ########################################################################################################
        if ea_type == "ga":
            if self.initialization == 'uniform':
                population = Population(
                    chromosomes=initializations.uniform(self.n_population, lower,
                                                        upper, self.n_dimensions))
            elif self.initialization == 'permutation':
                population = Population(
                    chromosomes=initializations.permutation(self.n_population, self.n_dimensions))
            else:
                raise ValueError("The specified initialization doesn't match. Stopping the algorithm")
        elif ea_type == "es":
            if self.initialization == 'uniform':
                population = Population(
                    chromosomes=initializations.uniform(self.n_population, lower,
                                                        upper, self.n_dimensions),
                    sigma=np.random.uniform() * (np.mean(upper) - np.mean(lower)) / 10)
            elif self.initialization == 'permutation':
                raise ValueError("The permutation initialization is not allowed yet with an evolutionary strategy")
            else:
                raise ValueError("The specified initialization doesn't match. Stopping the algorithm")
        elif ea_type == "gga":
            population = Population()
            upper_s, lower_s = population.gga_initialization(upper, lower, self.n_population, self.grid_intervals)
            children_alpha, children_s = None, None
        else:
            raise ValueError(
                "The defined Strategy type doesn't match with a Genetic Algoritghm (ga), Evolution Strategy (es) nor Grid-based Genetic Algorithm (GGA)")

        # Initialize vars for the evolutionary process
        iteration = 0
        best_fitness = np.inf  # if self.minimization else -np.inf

        # Iterate simulating the evolutionary process
        while (iteration < self.n_iterations) and (self.goal < best_fitness):
            # if self.minimization else -self.goal > best_fitness):

            # Apply the function in each row to get the array of fitness
            fitness = fitness_function(population.chromosomes)

            ############################################################################################################
            # [LOGS] Log the values
            ############################################################################################################
            best_idx = np.argmin(fitness) if self.minimization else np.argmax(fitness)

            logger.log({'mean': np.abs(np.mean(fitness)),
                        'worst': np.abs(np.max(fitness)) if self.minimization else np.abs(np.min(fitness)),
                        'best': np.abs(np.min(fitness)) if self.minimization else  np.abs(np.max(fitness)),
                        'best_chromosome': population.chromosomes[best_idx]})
            if ea_type == 'gga':
                logger.log({'best_s': population.s[best_idx],
                            'best_alpha': population.alpha[best_idx]},
                           count_it=False)

            # Get the best chromosome and its features
            if iteration >= 1:
                idx_best = np.argmin(logger.get_log('best'))
            else:
                idx_best = 0

            best_chromosome = logger.get_log('best_chromosome')[idx_best] if iteration > 0 else logger.get_log(
                'best_chromosome')
            best_fitness = logger.get_log('best')[idx_best]

            if ea_type == 'gga':
                best_s = logger.get_log('best_s')[idx_best] if iteration > 0 else logger.get_log('best_s')
                best_alpha = logger.get_log('best_alpha')[idx_best] if iteration > 0 else logger.get_log('best_alpha')

            ########################################################################################################
            # [SELECTION] Select a subgroup of parents
            ########################################################################################################
            if self.selection == 'wheel':
                idx = selections.wheel(fitness, M=self.n_children, minimize=self.minimization)
            elif self.selection == 'tournament':
                idx = selections.tournament(fitness, N=self.tournament_competitors,
                                            M=self.tournament_winners,
                                            iterations=int(self.n_children / self.tournament_winners),
                                            minimize=self.minimization)
            else:
                raise ValueError("The specified selection doesn't match. Not applying the selection operation")
            parents = population.chromosomes[idx]

            # If the Algorithm is a Grid/based genetic algorithm create the s and alpha vars
            if ea_type == "gga":
                parents_s = population.s[idx]
                parents_alpha = population.alpha[idx]

            ########################################################################################################
            # [CROSSOVER] Use recombination to generate new children
            ########################################################################################################
            if not self.crossover:
                warnings.warn("Warning: Crossover won't be applied")

            elif self.crossover == 'blend':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation +
                        " mutation is supported only by genetic algorithms (ga)")
                else:
                    children = crossovers.blend(np.copy(parents), self.xover_prob, upper[idx], lower[idx])
            elif self.crossover == 'one-point':
                if ea_type != "ga" and ea_type != "gga":
                    raise ValueError(
                        "The " + self.mutation +
                        " mutation is supported only by genetic algorithms (ga)")
                else:
                    if ea_type == "ga":
                        children = crossovers.one_point(np.copy(parents), self.xover_prob)
                    elif ea_type == "gga":
                        # With probability xover_prob do the crossover. If we have to do the crossover we do it in both
                        # s and alpha parameters
                        children_s, children_alpha = crossovers.one_point_gga(np.copy(parents_s),
                                                                              np.copy(parents_alpha),
                                                                              self.xover_prob)
            elif self.crossover == 'one-point-permutation':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation + " mutation is supported only by genetic algorithms (ga)")
                else:
                    children = crossovers.one_point_permutation(np.copy(parents), self.xover_prob)
            elif self.crossover == 'two-point':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation + " mutation is supported only by genetic algorithms (ga)")
                else:
                    children = crossovers.two_point(parents, self.xover_prob)
            else:
                raise ValueError("The specified crossover doesn't match. Not applying the crossover operation")

            ########################################################################################################
            # [MUTATION] Mutate the generated children
            ########################################################################################################
            if not self.mutation:
                warnings.warn("Warning: Mutation won't be applied")
            elif self.mutation == 'non-uniform':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation + " mutation is only supported by genetic algorithms (ga)")
                else:
                    children = mutations.non_uniform(children, self.mutat_prob, upper[idx], lower[idx], iteration,
                                                     self.n_iterations)
            elif self.mutation == 'uniform':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation + " mutation is only supported by genetic algorithms (ga)")
                else:
                    children = mutations.uniform(children, self.mutat_prob, upper[idx], lower[idx])
            elif self.mutation == 'swap':
                if ea_type != "ga":
                    raise ValueError(
                        "The " + self.mutation + " mutation is only supported by genetic algorithms (ga)")
                else:
                    children = mutations.pos_swap(children, self.mutat_prob)
            elif self.mutation == 'gaussian':
                if ea_type != "es":
                    raise ValueError(
                        "The " + self.mutation + " mutation is only supported by evolutionary strategies (es)")
                else:
                    children, population.sigma = mutations.gaussian(parents, self.mutat_prob, lower, upper,
                                                                    population.sigma)
            elif self.mutation == 'gga-mutation':
                if ea_type != "gga":
                    raise ValueError(
                        "The " + self.mutation + "mutation is only supported by the Grid Based Genetic Algorithms (gga)")
                else:
                    children_s, children_alpha = mutations.gga(children_s, children_alpha, population.delta[idx],
                                                               self.control_alpha, self.control_s, self.mutat_prob,
                                                               self.alpha_prob, upper_s[idx], lower_s[idx])
            else:
                raise ValueError("The specified mutation doesn't match. Not applying the mutation operation")

            # If the strategy is a gga calculate the value of the childrens. The delta values remain as in the parents
            if ea_type == "gga":
                children = population.gga_chromosome(children_s, population.delta[idx], children_alpha)

            ########################################################################################################
            # [REPLACE] Replace the current chromosomes of parents and childrens to
            ########################################################################################################
            if self.replacement == 'elitist':
                population.chromosomes = replacements.elitist(population.chromosomes, fitness, children,
                                                              fitness_function(children), self.n_population,
                                                              elitism=self.replacement_elitism,
                                                              minimize=self.minimization)
            elif self.replacement == 'worst_parents':
                population.chromosomes = replacements.worst_parents(parents, fitness, children, self.minimization)
            elif self.replacement == 'generational':
                population.chromosomes = children
                if ea_type == "gga":
                    population.s = children_s
                    population.alpha = children_alpha
            else:
                raise ValueError("The specified replacement doesn't match. Not applying the replacement operation")

            # Increase the number of iterations by 1
            iteration += 1

        # Return the logger object with the new data and the best chromosome
        if ea_type == 'gga':
            return logger, {'Best chromosome': best_chromosome,
                            'Fitness': best_fitness,
                            'S value': best_s,
                            'Alpha value': best_alpha}
        else:
            return logger, {'Best chromosome': best_chromosome,
                            'Fitness': best_fitness}

    except ValueError as err:
        print(err.args)
        return None
