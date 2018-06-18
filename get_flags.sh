#!/usr/bin/env bash

cat team.json | /usr/local/bin/jq -r 'to_entries|map(.key|ascii_downcase)|join("\n")' | while read flag
do
	wget --output-document ${flag}_large.png https://api.fifa.com/api/v1/picture/flags-fwc2018-5/${flag}
	wget --output-document ${flag}.png https://api.fifa.com/api/v1/picture/flags-fwc2018-4/${flag}
done