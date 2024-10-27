#!/usr/bin/env python3

import os

from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)


def pair_in_out_files(in_files, out_files):
    in_base_names = {os.path.splitext(f)[0]: f for f in in_files}
    out_base_names = {os.path.splitext(f)[0]: f for f in out_files}
    if in_base_names.keys() != out_base_names.keys():
        raise ValueError('Input & output doesn\'t match!')
    pairs = []
    for name in in_base_names.keys() & out_base_names.keys():
        pairs.append((in_base_names[name], out_base_names[name]))
    return list(sorted(pairs))


def create_testdata(tioj, problem_id, problem_dir):
    inputs = tioj.get_inputs(f'/problems/{problem_id}/testdata/new')

    data = {}
    data['authenticity_token'] = inputs.find(
        'authenticity_token')[0].attrs['value']
    data['commit'] = inputs.find('commit')[0].attrs['value']
    data['testdatum[time_limit]'] = 10000  # 10 seconds
    data['testdatum[vss_limit]'] = 2 * 1024 * 1024  # 2GiB
    data['testdatum[rss_limit]'] = ''
    data['testdatum[output_limit]'] = 2 * 1024 * 1024  # 2GiB

    in_files = os.listdir(problem_dir / 'in')
    out_files = os.listdir(problem_dir / 'out')
    file_pairs = pair_in_out_files(in_files, out_files)
    for (in_file, out_file) in file_pairs:
        data['testdatum[problem_id]'] = problem_id
        files = {}
        files['testdatum[test_input]'] = open(
            problem_dir / 'in' / in_file, 'rb')
        files['testdatum[test_output]'] = open(
            problem_dir / 'out' / out_file, 'rb')
        rel = tioj.post(
            f'/problems/{problem_id}/testdata', data=data, files=files)
        logger.debug(rel.text)
        assert rel.status_code == 200


def destroy_testdata(tioj, problem_id):
    inputs = tioj.get_inputs(f'/problems/{problem_id}/testdata/batch_edit')

    data = {}
    data['authenticity_token'] = inputs.find(
        'authenticity_token')[0].attrs['value']
    data['commit'] = inputs.find('commit')[0].attrs['value']

    td_delete_regex = r"td\[\d+\]\[form_delete\]"
    td_same_as_above_regex = r"td\[\d+\]\[form_same_as_above\]"
    for td_delete in inputs.find(td_delete_regex):
        data[td_delete.attrs['name']] = 1
    for td_same_as_above in inputs.find(td_same_as_above_regex):
        data[td_same_as_above.attrs['name']] = 0
    rel = tioj.post(f'/problems/{problem_id}/testdata/batch_edit', data=data)
    logger.debug(rel.text)
    assert rel.status_code == 200


def main():
    from library_checker_problems.generate import find_problem_dir, Problem
    import toml

    from common import UserTIOJ, prepare_colorlog
    import config

    prepare_colorlog()

    tomlpath = Path(__file__).parent / 'problems.toml'
    problems = toml.load(tomlpath)['problems']

    for index, problem in enumerate(problems):
        logger.info('problem {}:\t{}'.format(
            problem['tioj_problem_id'], problem['name']))

    def confirm(question, valid_options):
        while True:
            confirm = input(question)
            if confirm.strip().lower() in valid_options:
                return confirm
            print("\nInvalid option. Please enter a valid option.")
    if confirm('Update the testdata of the above problems? [y/n]: ',
               ['y', 'n']) != 'y':
        logger.warning(
            'Edit problems.toml if you want to update different problem set')
        return

    rootdir: Path = Path(__file__).parent / 'library_checker_problems'
    tioj = UserTIOJ(config)

    for index, problem_dict in enumerate(problems):
        problem_name: str = problem_dict['name']
        tioj_problem_id: int = problem_dict['tioj_problem_id']

        logger.info('Calling library-checker\'s generating process for {} (problem {})'
                    .format(problem_name, tioj_problem_id))
        problem_dir = find_problem_dir(rootdir, problem_name)
        if problem_dir is None:
            raise ValueError('Cannot find problem: {}'.format(problem_name))
        problem = Problem(rootdir, problem_dir)
        problem.generate(Problem.Mode.DEFAULT)
        logger.debug('Checker is {}'.format(problem.checker))

        logger.info('Uploading testdata to TIOJ for {} (problem {})'
                    .format(problem_name, tioj_problem_id))
        destroy_testdata(tioj, tioj_problem_id)
        create_testdata(tioj, tioj_problem_id, problem_dir)

        # problem.generate(Problem.Mode.CLEAN)

        logger.info('Finished {} (problem {})'
                    .format(problem_name, tioj_problem_id))


if __name__ == '__main__':
    main()
