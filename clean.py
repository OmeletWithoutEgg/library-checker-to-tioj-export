#!/usr/bin/env python3

from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)


def main():
    from library_checker_problems.generate import find_problem_dir, Problem
    import toml

    from common import prepare_colorlog

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
    if confirm('Clean all the testdata of the above problems? [y/n]: ',
               ['y', 'n']) != 'y':
        logger.warning(
            'Edit problems.toml if you want to update different problem set')
        return

    rootdir: Path = Path(__file__).parent / 'library_checker_problems'
    for index, problem_dict in enumerate(problems):
        problem_name: str = problem_dict['name']
        tioj_problem_id: int = problem_dict['tioj_problem_id']
        logger.info('Calling library-checker\'s cleaning process for {} (problem {})'
                    .format(problem_name, tioj_problem_id))
        problem_dir = find_problem_dir(rootdir, problem_name)
        if problem_dir is None:
            raise ValueError('Cannot find problem: {}'.format(problem_name))
        problem = Problem(rootdir, problem_dir)
        problem.generate(Problem.Mode.CLEAN)
        logger.debug('Checker is {}'.format(problem.checker))


if __name__ == '__main__':
    main()
