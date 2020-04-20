import os
import re
import multiprocessing as mp
from nltk import tokenize


# Matches HTML tag and their content
RE_1 = re.compile(r'<\s*a[^>]*>(.*?)<\s*/\s*a>')


def _worker_loop(work_queue, result_queue):
    while True:
        fpath = work_queue.get()
        if not fpath:
            break
        with open(fpath, 'r') as fp:
            for line in fp:
                line = line.strip()
                before = len(line)
                re.sub(RE_1, '', line)
                after = len(line)
                if not line and before != after:
                    continue
                if line.startswith('<doc'):
                    doc = []
                elif line.startswith('</doc>'):
                    result_queue.put(process_doc(doc))
                else:
                    doc.append(line)
    result_queue.put(None)


def process_doc(doc):
    # Remove title
    doc = doc[1:]
    while len(doc) > 0 and not doc[0]:
        doc = doc[1:]
    if not doc:
        return ''
    sections_paragraphs_lines = [[[]]]
    for line in doc:
        if not line:
            sections_paragraphs_lines[-1].append([])
            continue
        if line.startswith('Section::::'):
            sections_paragraphs_lines.append([[]])
            continue
        sections_paragraphs_lines[-1][-1] += tokenize.sent_tokenize(line)
    final = ''
    for section in sections_paragraphs_lines:
        final_section = ''
        for paragraph in section:
            if not paragraph:
                continue
            if final_section:
                final_section += '\n\n' + '\n'.join(paragraph)
            else:
                final_section = '\n'.join(paragraph)
        if not final_section:
            continue
        if final:
            final += '\n\n\n' + final_section
        else:
            final = final_section
    return final


def get_fpaths(dpath):
    fpaths = []
    for name in os.listdir(dpath):
        path = os.path.join(dpath, name)
        if os.path.isdir(path):
            fpaths += get_fpaths(path)
        else:
            fpaths.append(path)
    return fpaths


def process_wiki(dpath_in, dpath_out, num_workers, splits):

    if not os.path.exists(dpath_out):
        os.makedirs(dpath_out)

    fpaths = get_fpaths(dpath_in)

    num_workers = min(len(fpaths), num_workers)

    work_queue, result_queue = mp.Queue(), mp.Queue(num_workers * 10)
    processes = []
    for _ in range(max(1, num_workers)):
        p = mp.Process(target=_worker_loop, args=(work_queue, result_queue))
        p.start()
        processes.append(p)
    for fpath in fpaths:
        work_queue.put(fpath)
    for _ in range(len(processes)):
        work_queue.put(None)

    remaining = len(processes)
    total_count = 0
    for split_size, split_fname in splits:
        if not remaining:
            break
        with open(os.path.join(dpath_out, split_fname), 'w') as fp:
            count = 0
            first = True
            while remaining and (split_size < 0 or count < split_size):
                result = result_queue.get()
                if result is None:
                    remaining -= 1
                else:
                    count += 1
                    total_count += 1
                if result:
                    if first:
                        first = False
                    else:
                        result = '\n\n\n\n' + result
                    fp.write(result)
                if total_count % 10000 == 0:
                    print('\rProcessed {} articles, {} files remaining.'.format(
                        total_count, remaining), end='')
    for p in processes:
        p.join()
    work_queue.close()
    result_queue.close()
    print('\nProcessed {} articles and {} files!'.format(total_count, len(fpaths)))


def main():
    import argparse
    parser = argparse.ArgumentParser('Extract article texts from wiki dump')

    parser.add_argument(
        '--input', '-i',
        type=str,
        metavar='DIR',
        help='Path of previously extracted articles.',
        required=True
    )

    parser.add_argument('-o', '--output', type=str, metavar='DIR', required=True,
                        help='Output directory')

    parser.add_argument('-s', '--splits', type=int, nargs='*', default=[],
                        help='Number of articles of each split.')

    parser.add_argument(
        '--num-workers',
        type=int,
        metavar='WORKERS',
        help='Number of worker processes. Default: %(default)s.',
        default=mp.cpu_count()
    )

    args = parser.parse_args()

    splits = [(split, 'split{}.txt'.format(i + 1)) for i, split in enumerate(args.splits)]
    splits.append((-1, 'remainder.txt'))

    process_wiki(
        dpath_in=args.input,
        dpath_out=args.output,
        num_workers=args.num_workers,
        splits=splits
    )

if __name__ == '__main__':
    main()
