#!/usr/bin/env python3

import re

from pathlib import Path
from logging import getLogger

logger = getLogger(__name__)


def edit_problem(tioj, problem_id, problem):
    inputs = tioj.get_inputs(f'/problems/{problem_id}/edit')
    data = problem.copy()
    data['authenticity_token'] = inputs.find(
        'authenticity_token')[0].attrs['value']
    data['commit'] = inputs.find('commit')[0].attrs['value']
    rel = tioj.patch(f'/problems/{problem_id}', data=data)
    assert rel.status_code == 200


def destroy_samples(tioj, problem_id):
    inputs = tioj.get_inputs(f'/problems/{problem_id}/edit')
    data = {}
    data['authenticity_token'] = inputs.find(
        'authenticity_token')[0].attrs['value']
    data['commit'] = inputs.find('commit')[0].attrs['value']
    id_regex = r'problem\[sample_testdata_attributes\]\[\d+\]\[id\]'
    destroy_regex = r'problem\[sample_testdata_attributes\]\[\d+\]\[_destroy\]'
    for input in inputs.find(id_regex):
        data[input.attrs['name']] = input.attrs['value']
    for input in inputs.find(destroy_regex):
        data[input.attrs['name']] = 1
    rel = tioj.patch(f'/problems/{problem_id}', data=data)
    assert rel.status_code == 200


def split_markdown(markdown_document):
    splits = re.split(r'(^#+ @\{.*?\}$)',
                      markdown_document, flags=re.MULTILINE)
    splits = splits[1:]
    paragraphs = dict(zip(splits[::2], splits[1::2]))
    ALL_HEADINGS = {
        "## @{keyword.statement}",
        "## @{keyword.constraints}",
        "## @{keyword.input}",
        "## @{keyword.output}",
        "## @{keyword.sample}"
    }
    for key in paragraphs:
        if key not in ALL_HEADINGS:
            raise ValueError(
                'This markdown document requires manual conversion.')
    return paragraphs


def param_to_str(value: int) -> str:
    # https://github.com/yosupo06/library-checker-frontend/blob/be91a1765f7f2798e95c9f5136460e089ea77771/src/utils/statement.parser.ts#L75

    if value == 0:
        return "0"

    # Check for multiples of 100,000
    if value % 100_000 == 0:
        k = 5
        while value % (10 ** (k + 1)) == 0:
            k += 1

        if value == 10 ** k:
            return f"10^{{{k}}}"
        else:
            return f"{value // (10 ** k)} \\times 10^{{{k}}}"

    # Check for powers of 2
    if value % (1 << 10) == 0:
        k = 10
        while value % (1 << (k + 1)) == 0:
            k += 1

        if value == 1 << k:
            return f"2^{{{k}}}"

    return str(value)


def parse_tags(problem, content: str):
    # The form of tag is "@{...}", and there are only four types of tags.
    # These are:
    #     - @{lang.en}, @{lang.ja}, @{lang.end}
    #     - @{example.$some_filename}: files are uploaded to the cloud in the form of `{in,out}/*`
    #     - @{param.$SOME_PARAM}: mappings are in info.toml
    #     - @{keyword.$some_field}: mappings are in statement.parser.ts, only used in headings
    # reference: https://github.com/yosupo06/library-checker-frontend/blob/be91a1765f7f2798e95c9f5136460e089ea77771/src/utils/statement.parser.ts

    # @{lang.*}
    def lang_handler(matchobj):
        groups = matchobj.groups()
        assert len(groups) == 4
        result = ''
        for i in range(0, len(groups), 2):
            if groups[i] == 'en':
                result += groups[i + 1]
        return result
    regex = r'^@\{lang\.(en|ja)\}$(.*?)^@\{lang\.(en|ja)\}$(.*?)^@\{lang\.end\}$'
    flags = re.MULTILINE | re.DOTALL
    content = re.sub(regex, lang_handler, content, flags=flags)

    # @{param.*}
    params = problem.config.get('params', {})

    def param_handler(matchobj):
        groups = matchobj.groups()
        assert len(groups) == 1
        key = groups[0]
        return param_to_str(params[key])
    regex = r'@\{param\.(.*?)\}'
    flags = re.MULTILINE | re.DOTALL
    content = re.sub(regex, param_handler, content, flags=flags)

    # The leftover @{} will be treat as errors
    regex = r'@\{.*\}'
    flags = re.MULTILINE | re.DOTALL
    if re.search(regex, content, flags=flags):
        raise ValueError('This markdown document requires manual conversion.')

    return content


def parse_samples(problem_dir: Path, content: str) -> [(Path, Path)]:
    # The location to find example file is {in,out}/{*example*}
    # reference: https://github.com/yosupo06/library-checker-judge/blob/master/storage/upload.go#L165
    regex = r'@\{example\.(.*?)\}'
    flags = re.MULTILINE | re.DOTALL
    matches = re.findall(regex, content, flags=flags)
    samples = []
    for example in matches:
        in_file = example + '.in'
        out_file = example + '.out'
        samples.append((problem_dir / 'in' / in_file,
                       problem_dir / 'out' / out_file))

    content = re.sub(regex, content, '', flags=flags)

    # The leftover @{} will be treat as errors
    regex = r'@\{.*\}'
    flags = re.MULTILINE | re.DOTALL
    if re.search(regex, content, flags=flags):
        raise ValueError('This markdown document requires manual conversion.')

    return samples


def unwrap_backtick(content: str) -> str:
    regex = r'\s*?(?:```|~~~)(.*?)(?:```|~~~)'
    flags = re.MULTILINE | re.DOTALL

    def handler(matchobj):
        groups = matchobj.groups()
        assert len(groups) == 1
        return groups[0]
    content = re.sub(regex, handler, content, flags=flags)
    return content


def fix_superscript(content: str) -> str:
    return content.replace('^', '^ ')


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
    if confirm('Update the statement of the above problems? [y/n]: ',
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
        problem_dir: Path = find_problem_dir(rootdir, problem_name)
        if problem_dir is None:
            raise ValueError('Cannot find problem: {}'.format(problem_name))
        problem = Problem(rootdir, problem_dir)
        problem.generate(Problem.Mode.DEFAULT)
        logger.debug('Checker is {}'.format(problem.checker))
        # TODO: handle checker
        # `problem[specjudge_type]` and `problem[sjcode]`

        with open(problem_dir / 'task.md', 'rb') as f:
            markdown_document = f.read().decode()
            paragraphs = split_markdown(markdown_document)

        HEADING_FIELD_MAPPING = {
            "## @{keyword.statement}": 'problem[description]',
            "## @{keyword.constraints}": 'problem[hint]',
            "## @{keyword.input}": 'problem[input]',
            "## @{keyword.output}": 'problem[output]',
        }

        data = {}
        for heading in paragraphs:
            content = paragraphs[heading]
            if heading == "## @{keyword.sample}":
                samples = parse_samples(problem_dir, content)
                continue
            s = parse_tags(problem, content)
            if heading == "## @{keyword.input}" or heading == "## @{keyword.output}":
                s = unwrap_backtick(s)
            s = fix_superscript(s)
            s = s.strip()
            data[HEADING_FIELD_MAPPING[heading]] = s

        problem_url = f'https://judge.yosupo.jp/problem/{problem_name}'
        data['problem[source]'] = f'''[library checker: {
            problem_name}]({problem_url})'''

        for index, (in_file, out_file) in enumerate(samples):
            with open(in_file, 'rb') as f:
                data[f'problem[sample_testdata_attributes][{
                    index}][input]'] = f.read().decode()
            with open(out_file, 'rb') as f:
                data[f'problem[sample_testdata_attributes][{
                    index}][output]'] = f.read().decode()

        data['problem[name]'] = config.tioj_problem_name(problem.config['title'])
        data['problem[tag_list]'] = config.tag_list

        # problem[name]
        # problem[description]
        # problem[input]
        # problem[output]
        # problem[sample_testdata_attributes][0][input]
        # problem[sample_testdata_attributes][0][output]
        # problem[hint]
        # problem[source]

        destroy_samples(tioj, tioj_problem_id)
        edit_problem(tioj, tioj_problem_id, data)


if __name__ == '__main__':
    main()
