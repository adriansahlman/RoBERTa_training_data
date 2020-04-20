# RoBERTa Training-Data
This repository contains instructions and utilities for gathering the data used to train the RoBERTa models (according to the [paper](https://arxiv.org/abs/1907.11692)).

All links and instructions can be found in this README.

The code and documentation of this repository is of low quality. It is more like a documentation of how I gathered the data in a quick and dirty way in case I need to redo it in the future.

NOTE: This is a work in progress and I will add/finish documentation for all datasets in the future.

The final text-files will have the following format:

3 empty lines = doc break    
2 empty lines = section break    
1 empty line = paragraph break    
1 sentence per line


### BookCorpus
This dataset is no longer available and the website that hosts the books have implemented some kind of measure to prevent scraping.
A copy of the dataset (already preprocessed) exists. Download it [here](https://drive.google.com/uc?id=16KCjV9z_FHm8LgZw05RSuk4EsAWPOP_z&export=download).

WARNING: This data is all lower cased as well as missing paragraph, section and document breaks.

Unpack the downloaded data.

Use `bookscorpus.py` to preprocess and split data. Lets use 4 000 000 lines as validation data and the rest as training data.

NOTE: Preprocessing attempts to remove the tokenization already in place.

Example:
```bash
python bookscorpus.py -i /path/to/bookscorpus/books_large_p1.txt /path/to/bookscorpus/books_large_p2.txt -o /path/to/destination_dir --splits 4000000 -1
```
This creates `split1.txt` with 4M lines and puts the remaining lines of the input data in `split2.txt`.

```bash
mv /path/to/destination_dir/split1.txt path/to/valid/bookscorpus.valid.txt
mv /path/to/destination_dir/split2.txt path/to/train/bookscorpus.train.txt
```

Preprocessing creates files with the following format:    
1 sentence per line

### Wikipedia
Get the latest [wikipedia dump](https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2)

Clone the repository [wikiextractor](https://github.com/attardi/wikiextractor)

```bash
python WikiExtractor.py /path/to/enwiki-latest-pages-articles.xml.bz2 -o /path/to/extracted --sections --filter_disambig_pages --min_text_length 200 --bytes 1G
```
`--bytes 1G` makes for less amount of files created as each file can be up to 1 GB.

Preprocess and concat wikipedia text into single file using `wikipedia.py`
Specify split in same way as `bookscorpus.py`, only difference is that it is articles, not lines.

In the wikipedia dump from april 2020 I found 4899923 articles after filtering.

Example:
```bash
# Preprocess and split into 2 files with 300,000 articles in the first and the remaining in the second.
python wikipedia.py -i /path/to/wikipedia/extracted/ -o /path/to/destination/ --splits 300000 -1
```

Preprocessing creates files with the following format:    
3 empty lines = doc break
2 empty lines = section break
1 empty line = paragraph break
1 sentence per line

### CC-NEWS
install aws cli https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-install.html

clone the repository [news-please](https://github.com/fhamborg/news-please)

`pip install -r requirements.txt`    
For me this package was not properly installed so I had to do it manually:    
`pip install hurry.filesize`    

Change `newsplease/examples/commoncrawl.py` to have a config that is somewhat similar to this:
```python
############ YOUR CONFIG ############
# download dir for warc files
my_local_download_dir_warc = './cc_download_warc/'
# download dir for articles
my_local_download_dir_article = './cc_download_articles/'
# hosts (if None or empty list, any host is OK)
my_filter_valid_hosts = []  # example: ['elrancaguino.cl']
# start date (if None, any date is OK as start date), as datetime
my_filter_start_date = datetime.datetime(2016, 1, 1)
# end date (if None, any date is OK as end date), as datetime
my_filter_end_date = datetime.datetime(2016, 12, 31)
# if date filtering is strict and news-please could not detect the date of an article, the article will be discarded
my_filter_strict_date = True
# if True, the script checks whether a file has been downloaded already and uses that file instead of downloading
# again. Note that there is no check whether the file has been downloaded completely or is valid!
my_reuse_previously_downloaded_files = True
# continue after error
my_continue_after_error = True
# show the progress of downloading the WARC files
my_show_download_progress = True
# log_level
my_log_level = logging.INFO
# json export style
my_json_export_style = 0  # 0 (minimize), 1 (pretty)
# number of extraction processes
my_number_of_extraction_processes = 28
# if True, the WARC file will be deleted after all articles have been extracted from it
my_delete_warc_after_extraction = True
# if True, will continue extraction from the latest fully downloaded but not fully extracted WARC files and then
# crawling new WARC files. This assumes that the filter criteria have not been changed since the previous run!
my_continue_process = False
############ END YOUR CONFIG #########
```

Run the script (this takes multiple days to complete).
```
python -m newsplease.examples.commoncrawl
```

### WEBTEXT
I have not looked at this dataset yet but I will probably be using [openwebtext](https://github.com/jcpeterson/openwebtext).

### STORIES
Install gsutil
```
curl https://sdk.cloud.google.com | bash
```
restart shell

Download data
```
gsutil cp -R gs://commonsense-reasoning/reproduce/stories_corpus/* /path/to/destination/
```
The data contains:
947,260 docs
404,265,586 lines

Process and split using `stories.py` (same command line args as for `wikipedia.py`).
```
# Create two splits, one with 47 000 documents and one with the rest
python stories.py -i /path/to/stories_corpus/ -o /path/to/processed/ -s 47000 -1
```

Preprocessing creates files with the following format:    
3 empty lines = doc break
1 sentence per line
