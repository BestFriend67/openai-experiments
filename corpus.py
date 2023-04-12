import os
import numpy as np
import openai
import pandas as pd
import pickle
import tiktoken
import re


COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"




def ask_prompt(prompt):
    templated_prompt = f"""Answer the question as truthfully as possible, and if you're unsure of the answer, say "Sorry, I don't know".

    Q: {prompt}
    A:
    """

    resp = openai.Completion.create(
        prompt=templated_prompt,
        temperature=0,
        max_tokens=300,
        model=COMPLETIONS_MODEL
    )["choices"][0]["text"].strip(" \n")
    return resp


def add_embeddings():
    writing_directories = (
        '/Users/will/irrational_hugo/content',
        '/Users/will/infra-eng/content',
        '/Users/will/staff-eng//src/markdown/',
    )
    filepaths = get_filepaths(writing_directories)

    # df = df.append({'Name': 'John', 'Age': 25, 'City': 'New York'}, ignore_index=True)

    rows = []
    for filepath in filepaths:
        try:
            headers, sections = clean_entry(filepath)
            for sect_title, sect_content in sections:
                row = {
                    'file': headers['filename'],
                    'header': sect_title,
                    'content': sect_content,
                }
                rows.append(row)
        except Exception as e:
            print(filepath, e)

    df = pd.DataFrame(rows, columns=['file', 'header', 'content'])
    print(df.head())


def clean_entry(filepath):
    """
    Parse a Markdown file with metadata headers wrapped in ---, e.g. a Hugo blog post.
    Return a 2-tuple of headers dictionary, with additional filepath key,
    and a list of header-contents 2-tuples.
    """
    raw = open(filepath).read()
    headings = {
        'filepath': filepath,
        'filename': filepath.split('/')[-1],
    }
    seen_break = 0
    if raw.startswith('---'):
        raw_header, body = raw.split('---', 2)[1:]
        for raw_line in raw_header.split('\n'):
            line = raw_line.strip()
            if ':' in line:
                key, val = line.split(':', 1)
                headings[key] = val.strip(" \"'")
    else:
        body = raw

    title = headings['title'] if 'title' in headings else headings['filename']
    body = f"# {title}\n{body}"

    sections = re.findall("[#]{1,4} .*\n", body)
    split_txt = '##### !!'
    for section in sections:
        body = body.replace(section, split_txt)
    contents = [x.strip() for x in body.split(split_txt)]
    headers = [x.strip('# \n') for x in sections]
    combined = zip(headers, contents)
    # strip out very short content sections
    combined = [(x,y) for x,y in combined if len(y.strip()) > 40]
    return headings, combined


def get_filepaths(directories):
    fps = []
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if not file_path.endswith('~'):
                    fps.append(file_path)
    return fps


if __name__ == "__main__":
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        key_file = os.path.join(os.path.expanduser("~"), ".openai-api-key.txt")
        api_key = open(key_file).read().strip()

    openai.api_key = api_key

    add_embeddings()

    #resp = ask_prompt("What are 10 things I should do on a sunny day in San Francisco?")
    #print(resp)
