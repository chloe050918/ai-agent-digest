#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PYTHONWARNINGS=ignore

echo "\$ cat output/raw_messages.json   # 今天转发到飞书『AI资讯』群的内容"
python3 -c "
import json
for m in json.load(open('output/raw_messages.json')):
    print('  -', m['text'])
"
echo
sleep 1

echo "\$ python3 extract_content.py"
python3 extract_content.py
echo
sleep 1

echo "\$ python3 generate_script.py"
python3 generate_script.py
echo
sleep 1

echo "\$ cat output/summary.md"
cat output/summary.md
echo
sleep 2

echo "\$ python3 synthesize_audio.py"
python3 synthesize_audio.py
echo
sleep 1

echo "\$ ls -la output/episode.mp3"
ls -la output/episode.mp3
sleep 2
