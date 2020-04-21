import os
import multiprocessing as mp
import signal
import bs4
import newspaper


class TimeoutException(Exception):
    pass


def sig_handler_alarm(signum, frame):
    raise TimeoutException()


signal.signal(signal.SIGALRM, sig_handler_alarm)


def scare_url(url, timeout):
    if timeout:
        signal.alarm(timeout)
    try:
        article = newspaper.Article(url, fetch_images=False)
        article.download()
        html = article.html
        text, count = find_and_filter_tag("p", soup)
        return text
    except:
        return None
    finally:
        signal.alarm(0)


def get_fpaths(dpath):
    fpaths = []
    for name in os.listdir(dpath):
        path = os.path.join(dpath, name)
        if os.path.isdir(path):
            fpaths += get_fpaths(path)
        else:
            fpaths.append(path)
    return fpaths


def _worker_loop(work_queue, result_queue, timeouts):
    while True:
        fpath = work_queue.get()
        if not fpath:
            break
        with open(fpath, 'r') as fp:
            for line in fp:
                url = line.strip()
                if not url:
                    continue
                doc = None
                for timeout in timeouts:
                    try:
                        doc = scrape_url(url, timeout)
                        break
                    except TimeoutError:
                        continue
                if doc:
                    result_queue.put('\n\n'.join(doc))
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


def process(dpath_in, dpath_out, num_workers, splits, timeouts):

    if not os.path.exists(dpath_out):
        os.makedirs(dpath_out)

    fpaths = get_fpaths(dpath_in)

    num_workers = min(len(fpaths), num_workers)

    work_queue, result_queue = mp.Queue(), mp.Queue(num_workers * 10)
    processes = []
    for _ in range(max(1, num_workers)):
        p = mp.Process(target=_worker_loop, args=(work_queue, result_queue, timeouts))
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
    parser = argparse.ArgumentParser('Download and process WEBTEXT data')

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

    parser.add_argument('-c', '--chunk', type=int, default=None,
                        help='Create arbitrary number of files containing `chunk` articles each.')

    parser.add_argument('-', '--timeout', type=int, nargs='*', default=[5, 5, 10],
                        help='Timeouts (in seconds) to try before moving on to next url when downloading.')

    parser.add_argument(
        '--num-workers',
        type=int,
        metavar='WORKERS',
        help='Number of worker processes. Default: %(default)s.',
        default=mp.cpu_count()
    )

    args = parser.parse_args()

    assert not args.splits or bool(args.splits) != bool(args.chunk), \
        '`--splits` and `--chunk` are mutually exclusive!'

    if args.chunk:
        def yield_splits(chunk):
            i = 1
            while True:
                yield chunk, 'split{}.txt'.format(i)
                i += 1
        splits = yield_splits(args.chunk)
    else:
        splits = [(split, 'split{}.txt'.format(i + 1)) for i, split in enumerate(args.splits)]
        splits.append((-1, 'remainder.txt'))

    process(
        dpath_in=args.input,
        dpath_out=args.output,
        num_workers=args.num_workers,
        splits=splits,
        timeouts=args.timeouts
    )

if __name__ == '__main__':
    main()
