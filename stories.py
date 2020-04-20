import os
import multiprocessing as mp


def combine(line, quote_open=False):
    line = line.strip().replace("``", '"').replace("''", '"')
    splits = [split for split in line.split(' ') if split]
    i = 0
    def merge():
        return splits[:i] + [splits[i] + splits[i + 1]] + splits[i + 2:]
    while i < len(splits) - 1:
        alpha_to_alpha = (splits[i][-1].isalpha() or splits[i][-1].isdigit()) \
                          and (splits[i+1][0].isalpha() or splits[i+1][0].isdigit())
        if quote_open:
            if splits[i + 1][0] == '"':
                splits = merge()
                quote_open = False
                continue
        else:
            if splits[i][-1] == '"':
                splits = merge()
                quote_open = True
                continue
        if splits[i + 1][0] in ',.;:':
            splits = merge()
        elif splits[i][-1] not in ',.;:' and not alpha_to_alpha:
            splits = merge()
        elif splits[i + 1] == "n't":
            splits = merge()
        else:
            i += 1
    line = ' '.join(splits)
    return line, quote_open


def get_fpaths(dpath):
    fpaths = []
    for name in os.listdir(dpath):
        path = os.path.join(dpath, name)
        if os.path.isdir(path):
            fpaths += get_fpaths(path)
        else:
            fpaths.append(path)
    return fpaths


def _worker_loop(work_queue, result_queue):
    while True:
        fpath = work_queue.get()
        if not fpath:
            break
        doc = []
        quote_open = False
        with open(fpath, 'r') as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    if doc:
                        result_queue.put('\n'.join(doc))
                    doc = []
                    quote_open = False
                else:
                    line, quote_open = combine(line, quote_open)
                    if line:
                        doc.append(line)
            if doc:
                result_queue.put('\n'.join(doc))
    result_queue.put(None)


def get_fpaths(dpath):
    fpaths = []
    for name in os.listdir(dpath):
        path = os.path.join(dpath, name)
        if os.path.isdir(path):
            fpaths += get_fpaths(path)
        else:
            fpaths.append(path)
    return fpaths


def process(dpath_in, dpath_out, num_workers, splits):

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
                    print('\rProcessed {} docs, {} files remaining.'.format(
                        total_count, remaining), end='')
    for p in processes:
        p.join()
    work_queue.close()
    result_queue.close()
    print('\nProcessed {} docs and {} files!'.format(total_count, len(fpaths)))


def main():
    import argparse
    parser = argparse.ArgumentParser('Process STORIES data')

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

    process(
        dpath_in=args.input,
        dpath_out=args.output,
        num_workers=args.num_workers,
        splits=splits
    )

if __name__ == '__main__':
    main()
