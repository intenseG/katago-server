import pandas as pd
from django.db.models import Manager
from django_pandas.io import read_frame

from katago_server.games.managers.ranking_estimation_game_pd_queryset import RankingEstimationGamePdQuerySet


class RankingEstimationGamePdManager(Manager):
    def get_queryset(self):
        return RankingEstimationGamePdQuerySet(self.model, using=self._db)

    def get_detailed_tournament_results_dataframe(self):
        tournament_results = read_frame(self.get_queryset().get_total_games_count_as_white())
        tournament_results = pd.merge(
            tournament_results,
            read_frame(self.get_queryset().get_total_games_count_as_black()),
            how="outer",
            on=["reference_network", "opponent_network"],
        )
        tournament_results = pd.merge(
            tournament_results,
            read_frame(self.get_queryset().get_total_wins_count_as_white()),
            how="outer",
            on=["reference_network", "opponent_network"],
        )
        tournament_results = pd.merge(
            tournament_results,
            read_frame(self.get_queryset().get_total_wins_count_as_black()),
            how="outer",
            on=["reference_network", "opponent_network"],
        )
        tournament_results = pd.merge(
            tournament_results,
            read_frame(self.get_queryset().get_total_draw_or_no_result()),
            how="outer",
            on=["reference_network", "opponent_network"],
        )
        tournament_results.fillna(0, inplace=True)
        return tournament_results