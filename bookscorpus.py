import os


def combine(line, quote_open=False):
    line = line.strip().replace("``", '"').replace("''", '"')
    splits = [split for split in line.split(' ') if split:]
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


def line_iter(*fnames):
    assert all(os.path.exists(fname) for fname in fnames), \
        'Input file does not exist'
    for fname in fnames:
        with open(fname, 'r') as fp:
            is_new = True
            for line in fp:
                yield line, is_new
                is_new = False


def main():
    import argparse
    parser = argparse.ArgumentParser('Preprocess bookscorpus and split into sets')
    parser.add_argument('-i', '--input', type=str, metavar='FILE', nargs='*', required=True,
                        help='Ordered input files')
    parser.add_argument('-o', '--output', type=str, metavar='DIR', required=True,
                        help='Output directory')
    parser.add_argument('-s', '--splits', type=int, nargs='*', default=[],
                        help='Number of lines of each split.')
    args = parser.parse_args()
    
    lines = line_iter(*args.input)

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    count = 0

    splits = [(split, 'split{}.txt'.format(i + 1)) for i, split in enumerate(args.splits)]
    splits.append((-1, 'remainder.txt'))
    quote_open = False
    for split_size, split_fname in splits:
        with open(os.path.join(args.output, split_fname), 'w') as fp:
            i = 0
            while split_size < 0 or i < split_size:
                try:
                    line, is_new_file = next(lines)
                except StopIteration:
                    print('Processed all {} lines'.format(count + 1))
                    return
                if is_new_file:
                    open_quote = False
                line, open_quote = combine(line, open_quote)
                if line:
                    fp.write(line + '\n')
                i += 1
                count += 1
                if count % 100000 == 0:
                    print('\rProcessed {} lines'.format(count), end='')


if __name__ == '__main__':
    main()
