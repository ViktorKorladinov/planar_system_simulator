from typing import List

from solvers.cplex_medicine.models import GapStats, MoverGapStats, OverallGapStats


def calculate_gaps(df) -> GapStats:
    mover_stats: List[MoverGapStats] = []
    df = df.sort_values(['Mover', 'Start'])
    all_gaps = []
    for mover in df['Mover'].unique():
        mover_tasks = df[df['Mover'] == mover].copy()

        mover_tasks['Next_Start'] = mover_tasks['Start'].shift(-1)
        mover_tasks['Gap'] = mover_tasks['Next_Start'] - mover_tasks['Finish']
        mover_tasks = mover_tasks.dropna(subset=['Next_Start'])

        all_gaps.extend(mover_tasks['Gap'].tolist())

        mover_stats.append(MoverGapStats(
            id=mover,
            total_gaps=len(mover_tasks),
            total_gap_duration=int(mover_tasks['Gap'].sum()),
            average_gap=mover_tasks['Gap'].mean(),
            min_gap=int(mover_tasks['Gap'].min()),
            max_gap=int(mover_tasks['Gap'].max())
        ))
    overall_stats = OverallGapStats(
        total_gaps=sum(mover.total_gaps for mover in mover_stats),
        total_gap_duration=sum(mover.total_gap_duration for mover in mover_stats),
        average_gap=sum(all_gaps) / len(all_gaps),
        min_gap=int(min(all_gaps)),
        max_gap=int(max(all_gaps)),
        number_of_movers=len(df['Mover'].unique()),

    )
    return GapStats(movers=mover_stats, overall=overall_stats)
