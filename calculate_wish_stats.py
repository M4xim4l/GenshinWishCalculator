import argparse
import numpy as np
import os
from tqdm import trange
import seaborn as sns
import matplotlib.pyplot as plt
from prettytable import PrettyTable
import pathlib

#https://gist.github.com/dbzm/68256c86c60d70072576
def to_markdown_table(pt):
    """
    Print a pretty table as a markdown table

    :param py:obj:`prettytable.PrettyTable` pt: a pretty table object.  Any customization
      beyond int and float style may have unexpected effects

    :rtype: str
    :returns: A string that adheres to git markdown table rules
    """
    _junc = pt.junction_char
    if _junc != "|":
        pt.junction_char = "|"
    markdown = [row[1:-1] for row in pt.get_string().split("\n")[1:-1]]
    pt.junction_char = _junc
    return "\n".join(markdown)

#constants from
#https://www.hoyolab.com/article/497840
p_base_four_star = 0.051
p_base_five_star = 0.006

five_star_pity_start = 74
five_star_pity_slope = 0.06

four_star_pity_start = 9
four_star_pity_slope = 0.51

#odds of getting a banner character if non-guaranteed
p_five_star_banner = 0.5
p_four_star_banner = 0.5

#odds of getting the desired four star
p_four_star_wanted = 1/3

def calculate_five_star_probability(last_five_star, t):
    d_last_five = t - last_five_star
    pity_factor = np.maximum(d_last_five - (five_star_pity_start - 2), 0)
    p_five_star = p_base_five_star + pity_factor * five_star_pity_slope
    return p_five_star

def calculate_four_star_probability(last_four_star, t):
    d_last_four = t - last_four_star
    pity_factor = np.maximum(d_last_four - (four_star_pity_start - 2), 0)
    p_four_star = p_base_four_star + pity_factor * four_star_pity_slope
    return p_four_star


loot_table = {
    'three': 1,
    'four_banner_wanted': 2,
    'four_banner_unwanted': 3,
    'four_offbanner': 4,
    'five_banner': 5,
    'five_offbanner': 6
}

def calculate_asymmetric_conf_interval(observations, data_means, confidence=0.95):
    chain_length = observations.shape[1]
    lower_bounds = np.zeros(chain_length)
    upper_bounds = np.zeros(chain_length)

    for t in range(chain_length):
        observations_t = observations[:, t]
        mean_t = data_means[t]

        uppers = np.arange(np.ceil(mean_t), np.ceil(np.max(observations_t)) + 1)
        lowers = np.arange(np.floor(np.min(observations_t)), np.floor(mean_t) + 1)

        requirements = np.ones((len(uppers), len(lowers)), dtype=bool)
        costs = np.expand_dims(uppers, 1) - np.expand_dims(lowers, 0)

        for i in range(requirements.shape[0]):
            ut = uppers[i]
            for j in range(requirements.shape[1]):
                lt = lowers[j]
                frac_included = np.sum((observations_t <= ut) & (observations_t >= lt)) / len(observations_t)
                requirements[i,j] = frac_included >= confidence

        costs[~requirements] = np.inf
        min_idx_up, min_idx_low = np.unravel_index(costs.argmin(), costs.shape)

        upper_bounds[t] = uppers[min_idx_up]
        lower_bounds[t] = lowers[min_idx_low]

    return upper_bounds, lower_bounds



def calculate_wish_stats(trials, chain_length, table_step):
    loot = np.zeros((trials, chain_length), dtype=int)

    last_five_star = -np.ones(trials, dtype=int)
    last_four_star = -np.ones(trials, dtype=int)

    four_star_banner_guarantee = np.zeros(trials, dtype=bool)
    five_star_banner_guarantee = np.zeros(trials, dtype=bool)

    print('Simulating...')
    for t in trange(chain_length):
        t_loot_distributed = np.zeros(trials, dtype=bool)

        #first distribute 5 stars
        t_rngs_num_stars = np.random.rand(trials)
        p_five_star = calculate_five_star_probability(last_five_star, t)

        got_five = t_rngs_num_stars < p_five_star
        five_is_banner = np.random.rand(np.sum(got_five)) < p_five_star_banner
        five_is_banner = five_is_banner | five_star_banner_guarantee[got_five]

        five_star_loot = loot_table['five_banner'] * five_is_banner + loot_table['five_offbanner'] * ~five_is_banner
        loot[got_five, t] = five_star_loot

        five_star_banner_guarantee[got_five] = ~five_is_banner
        t_loot_distributed[got_five] = True
        last_five_star[got_five] = t

        #next distribute 4 stars
        p_four_star = calculate_four_star_probability(last_four_star, t)

        got_four = (t_rngs_num_stars < (p_five_star + p_four_star)) & ~t_loot_distributed
        four_is_banner = np.random.rand(np.sum(got_four)) < p_four_star_banner
        four_is_banner = four_is_banner | four_star_banner_guarantee[got_four]
        four_is_banner_and_wanted = np.random.rand(np.sum(got_four)) < p_four_star_wanted

        four_star_loot = (four_is_banner & four_is_banner_and_wanted) * loot_table['four_banner_wanted']
        four_star_loot += (four_is_banner & ~four_is_banner_and_wanted) * loot_table['four_banner_unwanted']
        four_star_loot += ~four_is_banner * loot_table['four_offbanner']
        loot[got_four, t] = four_star_loot

        four_star_banner_guarantee[got_four] = ~four_is_banner
        t_loot_distributed[got_four] = True
        last_four_star[got_four] = t

        #losers get 3 stars
        loot[~t_loot_distributed, t] = loot_table['three']

    print('Simulation done')

    print('Evaluating Simulation...')
    max_num_copies = 7
    wanted_five_stars_up_to = np.minimum(np.cumsum(loot == loot_table['five_banner'], axis=1), max_num_copies)
    wanted_four_star_up_to = np.minimum(np.cumsum(loot == loot_table['four_banner_wanted'], axis=1), max_num_copies)

    exact_constellation_probabilities = {}
    at_least_constellation_probabilities = {}
    average_copies = {}

    for i, (data, name) in enumerate(zip([wanted_four_star_up_to, wanted_five_stars_up_to], ['4*', '5*'])):
        exact_ps_i = np.zeros((max_num_copies, chain_length), dtype=float)
        at_least_ps_i = np.zeros((max_num_copies, chain_length), dtype=float)

        for const in range(max_num_copies):
            exact_ps_i[const] = np.mean(data == const + 1, axis=0)
            at_least_ps_i[const] = np.mean(data >= const + 1, axis=0)

        avg_copies_i = np.mean(data, axis=0)

        exact_constellation_probabilities[name] = exact_ps_i
        at_least_constellation_probabilities[name] = at_least_ps_i
        average_copies[name] = avg_copies_i

    table_idcs = np.arange(table_step, chain_length + table_step, table_step, dtype=int) - 1
    table_idcs[-1] = chain_length - 1

    results_dir = 'results'
    pathlib.Path(results_dir).mkdir(parents=True, exist_ok=True)

    print('Generating tables...')
    for name in ['4*', '5*']:
        for data_dict, table_name in zip([exact_constellation_probabilities, at_least_constellation_probabilities],
                                         ['Probability of getting exactly constellation X',
                                          'Probability of getting at least constellation X']):
            data = data_dict[name]

            table_column_names = ['Pulls', ] + [f'C{n}' for n in range(max_num_copies)]
            table = PrettyTable(table_column_names, float_format='.4')

            for table_idx in table_idcs:
                row = [table_idx + 1, ] + data[:, table_idx].tolist()
                table.add_row(row)

            table_filename = f'{name}_{table_name}.txt'.replace(' ', '_').replace('*', '').lower()
            table_filepath = os.path.join(results_dir, table_filename)
            with open(table_filepath, 'w') as f:
                f.write(f'{name} - {table_name}\n')
                f.write(str(table))

            #only used for readme.md
            print(f'{name} - {table_name}')
            print(to_markdown_table(table))
            print('\n\n')


    print('Generating plot...')


    scale_factor = 4
    fig, axs = plt.subplots(2, 3, figsize=(3 * 3 * scale_factor, 3 * scale_factor))
    for i, name in enumerate(['4*', '5*']):
        ax = axs[i, 0]
        color_map = plt.get_cmap('Set1')
        x = np.arange(chain_length)
        for const in range(max_num_copies):
            y = exact_constellation_probabilities[name][const,:]
            ax.plot(x, y, color=color_map(const / max_num_copies), label=f'C{const}')
        ax.grid()
        ax.legend()
        ax.set_title(f'{name} - Probability of getting exactly constellation X ')
        ax.set_xlabel('Pulls')
        ax.set_ylabel('Probability')

        ax = axs[i, 1]
        color_map = plt.get_cmap('Set1')
        for const in range(max_num_copies):
            y = at_least_constellation_probabilities[name][const,:]
            ax.plot(x, y, color=color_map(const / max_num_copies), label=f'C{const}')
        ax.grid()
        ax.legend()
        ax.set_title(f'{name} - Probability of getting at least constellation X ')
        ax.set_xlabel('Pulls')
        ax.set_ylabel('Probability')

        ax = axs[i, 2]

        x = np.arange(chain_length)
        y = average_copies[name]
        ax.plot(x, y)
        ax.grid()
        ax.set_title(f'{name} - Average Copies after N pulls')
        ax.set_xlabel('Pulls')
        ax.set_ylabel('Copies')

    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, 'simulation_results.png'))

def parse_args():
    parser = argparse.ArgumentParser(description='Parse arguments', prefix_chars='-')
    parser.add_argument('--trials', default=1_500_000, type=int,
                    help='Number of trials to simulate')
    parser.add_argument('--chain_length', default=1080, type=int,
                    help='Number of draws per trial')
    parser.add_argument('--table_step', default=50, type=int,
                    help='Number of draws per trial')
    parser.add_argument('--seed', default=0, type=int,
                    help='RNG seed')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    trials = args.trials
    chain_length = args.chain_length
    table_step = args.table_step
    seed = args.seed
    np.random.seed(seed)
    calculate_wish_stats(trials, chain_length, table_step)

