from math import exp, log, sqrt
import logging

import numpy as np
import pandas

from src.apps.trainings.services.pandas_utils import PandasUtilsService

pandas_utils = PandasUtilsService()

logger = logging.getLogger(__name__)

class BayesEloInconsistentDataError(Exception):
    pass

class BayesianRatingService:
    """
    BayesianRatingService takes a list of network, an anchor network and the result of rating games and update the rating
    """

    _simplified_tournament_results = None
    _networks_actual_score = None

    def __init__(
        self,
        network_ratings: pandas.DataFrame,
        network_anchor_id,
        detailed_tournament_results: pandas.DataFrame,
        virtual_draw_strength
    ):
        self._network_ratings = network_ratings
        self._network_anchor_id = network_anchor_id
        self._detailed_tournament_results = detailed_tournament_results
        self._virtual_draw_strength = virtual_draw_strength

    def update_ratings_iteratively(self, number_of_iterations):
        # Skip if we don't have enough networks to have ratings
        if len(self._network_ratings) <= 1:
            return self._network_ratings

        # pandas_utils.print_data_frame(self._network_ratings)
        # logger.warning("starting bayeselo iteration")

        self._assert_detailed_tournament_results_consistency()
        self._add_virtual_draws()
        self._simplify_tournament_into_win_loss()
        self._assert_simplified_tournament_results_consistency()
        self._sort_inplace_network_ratings_by_uncertainty()
        self._calculate_networks_actual_score()

        for iteration_index in range(number_of_iterations):
            for network_id in reversed(self._network_ratings.index):
                network_log_gamma = self._network_ratings.loc[network_id,"log_gamma"]
                self._update_specific_network_log_gamma(network_id, network_log_gamma)
            self._reset_anchor_log_gamma()

        for network in self._network_ratings.itertuples():
            network_id = network[0]
            network_log_gamma = network.log_gamma
            self._update_specific_network_log_gamma_uncertainty(network_id, network_log_gamma)

        return self._network_ratings

    def _assert_detailed_tournament_results_consistency(self):
        # Something is wrong if the total number of wins and draws summed across everything is inconsistent with the number of games
        game_count_times_two_via_results = (
            2 * np.sum(self._detailed_tournament_results["total_wins_white"]) +
            2 * np.sum(self._detailed_tournament_results["total_wins_black"]) +
            np.sum(self._detailed_tournament_results["total_draw_or_no_result_white"]) +
            np.sum(self._detailed_tournament_results["total_draw_or_no_result_black"])
        )
        game_count_times_two_via_games = (
            np.sum(self._detailed_tournament_results["total_games_white"]) +
            np.sum(self._detailed_tournament_results["total_games_black"])
        )
        if game_count_times_two_via_results != game_count_times_two_via_games:
            raise BayesEloInconsistentDataError("Inconsistent rating games results in Elo calculation: wins != games summed across networks")

    def _assert_simplified_tournament_results_consistency(self):
        if np.min(self._simplified_tournament_results["nb_games"] - self._simplified_tournament_results["nb_wins"]) <= 0:
            raise BayesEloInconsistentDataError("Inconsistent rating games results in Elo calculation: simplified wins >= games for some network")

    def _get_games_played_by_specific_network(self, network_id):
        """
        Utility function to get the table of the number of games played by a network

        :param network_id:
        :return:
        """
        games_played_by_specific_network_filter = self._tournament_results_only_total["reference_network"] == network_id
        return self._tournament_results_only_total[games_played_by_specific_network_filter]

    def _add_virtual_draws(self):
        """
         Whenever a NEW player is added to the above, it is necessary to add a Bayesian prior to obtain good results
         and keep the math from blowing up.
         A reasonable prior is to add some number of "virtual draws" between the new player and the immediately previous neural net version.
        """
        virtual_draws_src = []
        network_ids = list(self._network_ratings.index)

        for network in self._network_ratings.itertuples():
            network_id = network[0]
            parent_network_id = network.parent_network__pk

            # Everything blows up if for some reason (eg first network, or deleted network)
            # the parent_network_id does not reference an actual network, so let's check that
            if parent_network_id in network_ids:
                draw1 = {
                    "reference_network": network_id,
                    "opponent_network": parent_network_id,
                    "total_bayesian_virtual_draws": self._virtual_draw_strength,
                }
                draw2 = {
                    "reference_network": parent_network_id,
                    "opponent_network": network_id,
                    "total_bayesian_virtual_draws": self._virtual_draw_strength,
                }
                virtual_draws_src.append(draw1)
                virtual_draws_src.append(draw2)
            # It's possible to get a divide by zero if we have no parent network
            # If we don't know a parent network and it's not the anchor, then add a very weak prior that the network is equal to every network except itself
            elif network_id != self._network_anchor_id:
                num_other_networks = len(self._network_ratings) - 1
                if num_other_networks > 0:
                    for other_network in self._network_ratings.itertuples():
                        other_network_id = other_network[0]
                        if other_network_id != network_id:
                            draw1 = {
                                "reference_network": network_id,
                                "opponent_network": other_network_id,
                                "total_bayesian_virtual_draws": 0.01 / num_other_networks,
                            }
                            draw2 = {
                                "reference_network": other_network_id,
                                "opponent_network": network_id,
                                "total_bayesian_virtual_draws": 0.01 / num_other_networks,
                            }
                            virtual_draws_src.append(draw1)
                            virtual_draws_src.append(draw2)

        virtual_draw = pandas.DataFrame(virtual_draws_src,columns=["reference_network","opponent_network","total_bayesian_virtual_draws"])
        # logger.warning(virtual_draw.to_string())

        tournament_results = pandas.merge(self._detailed_tournament_results, virtual_draw, how="outer", on=["reference_network", "opponent_network"],)
        # panda_utils.print_data_frame(tournament_results)
        tournament_results.fillna(0, inplace=True)
        self._detailed_tournament_results = tournament_results

    def _simplify_tournament_into_win_loss(self):
        """
        For the rest of the algorithm, we do not need the full detail.
        We indeed consider that win as black or as white is similar.
        """
        tournament_results = pandas.DataFrame()

        tournament_results["reference_network"] = self._detailed_tournament_results["reference_network"]
        tournament_results["opponent_network"] = self._detailed_tournament_results["opponent_network"]

        # First compute the total number of games, without forgetting bayesian prior draws
        tournament_results["nb_games"] = 0.0
        tournament_results["nb_games"] += self._detailed_tournament_results["total_games_white"]
        tournament_results["nb_games"] += self._detailed_tournament_results["total_games_black"]
        tournament_results["nb_games"] += self._detailed_tournament_results["total_bayesian_virtual_draws"]

        # Then the wins
        tournament_results["nb_wins"] = 0.0
        tournament_results["nb_wins"] += self._detailed_tournament_results["total_wins_white"]
        tournament_results["nb_wins"] += self._detailed_tournament_results["total_wins_black"]
        tournament_results["nb_wins"] += 0.5 * self._detailed_tournament_results["total_draw_or_no_result_white"]
        tournament_results["nb_wins"] += 0.5 * self._detailed_tournament_results["total_draw_or_no_result_black"]
        tournament_results["nb_wins"] += 0.5 * self._detailed_tournament_results["total_bayesian_virtual_draws"]

        # And save it for later usage
        self._simplified_tournament_results = tournament_results

        tournament_results_only_total = pandas.DataFrame()
        tournament_results_only_total["reference_network"] = self._simplified_tournament_results["reference_network"]
        tournament_results_only_total["opponent_network"] = self._simplified_tournament_results["opponent_network"]
        tournament_results_only_total["nb_games"] = self._simplified_tournament_results["nb_games"]
        self._tournament_results_only_total = tournament_results_only_total

    def _sort_inplace_network_ratings_by_uncertainty(self):
        self._network_ratings.sort_values("log_gamma_uncertainty", ascending=False, inplace=True)

    def _calculate_networks_actual_score(self):
        """
        Calculate the total number of wins for each reference network.
        """
        aggregated_tournament_results = self._simplified_tournament_results.groupby(["reference_network"]).sum()

        networks_actual_score = pandas.DataFrame(index=aggregated_tournament_results.index)
        networks_actual_score["actual_score"] = aggregated_tournament_results["nb_wins"]

        for network_id in self._network_ratings.index:
            if network_id not in networks_actual_score.index:
                networks_actual_score.loc[network_id] = {"actual_score": 0.0}

        self._networks_actual_score = networks_actual_score

    def _update_specific_network_log_gamma(self, network_id, network_previous_log_gamma):
        expected_score = self._calculate_specific_network_expected_score(network_id, network_previous_log_gamma)
        actual_score = self._networks_actual_score.loc[network_id, "actual_score"]
        # Set log_gamma(Pi) := log_gamma(Pi) + log(actual_number_of_win(Pi) / expected_number_win(Pi))
        log_gamma_diff = log(actual_score / expected_score)
        self._network_ratings.loc[network_id, "log_gamma"] += log_gamma_diff

    def _calculate_specific_network_expected_score(self, network_id, network_log_gamma):
        """
        For every game Gj that Pi participated in, compute:
            probability_win(Pi,Gj) = 1 / (1 + exp(log_gamma(opponent of Pi in game Gj) - log_gamma(Pi)))
        Then compute:
            expected_score(Pi) = sum_{all games Gj that Pi participated in} ProbWin(Pi,Gj)

        :param network_id: The network specified
        :param network_log_gamma:
        """
        games_played = self._get_games_played_by_specific_network(network_id)
        pandas_utils.print_data_frame(games_played)

        expected_score = 0.0
        for game in games_played.itertuples():
            opponent_network = game.opponent_network
            opponent_network_log_gamma = self._network_ratings.loc[opponent_network, "log_gamma"]
            log_gamma_diff = opponent_network_log_gamma - network_log_gamma
            win_probability = 1 / (1 + exp(log_gamma_diff))
            expected_score += win_probability * game.nb_games

        return expected_score

    def _reset_anchor_log_gamma(self):
        """
        With all that, anchor player log_gamma will have changed but it is supposed to stay at 0.
        So subtract the anchor player's log_gamma value from every player's log_gamma, including the anchor player's own log_gamma,
        so that the anchor player is back at log_gamma 0.
        """
        self._network_ratings["log_gamma"] -= self._network_ratings.loc[self._network_anchor_id, "log_gamma"]

    def _update_specific_network_log_gamma_uncertainty(self, network_id, network_log_gamma):
        precision = self._calculate_specific_network_precision(network_id, network_log_gamma)
        uncertainty = sqrt(1.0 / precision)
        # Cap the amount of uncertainty, so that if we nearly divide by 0, we don't end up with a totally ridiculous number
        # for user display and game matching and other such purposes.
        uncertainty = min(uncertainty,10.0)
        self._network_ratings.loc[network_id, "log_gamma_uncertainty"] = uncertainty

    def _calculate_specific_network_precision(self, network_id, network_log_gamma):
        """
        Compute the second derivative of the log probability with respect to the particular gamma that we are trying to measure uncertainty of.

        :param network_id:
        :param network_log_gamma:
        :return:
        """
        games_played = self._get_games_played_by_specific_network(network_id)

        total_precision = 0.0
        for game in games_played.itertuples():
            opponent_network = game.opponent_network
            opponent_network_log_gamma = self._network_ratings.loc[opponent_network, "log_gamma"]
            log_gamma_diff = opponent_network_log_gamma - network_log_gamma
            this_game_stdev = exp(log_gamma_diff / 2) + exp(-log_gamma_diff / 2)
            this_game_precision = 1.0 / (this_game_stdev * this_game_stdev)
            total_precision += game.nb_games * this_game_precision
            # logger.warning(repr(game) + " " + str(this_game_precision) + " " + str(game.nb_games))

        return total_precision

