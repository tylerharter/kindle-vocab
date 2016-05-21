.PHONY=all
all : lambda.zip static/dict.json

static/dict.json : parse_wordnet.py
	python parse_wordnet.py > static/dict.json

lambda.zip : lambda/lambda_function.py
	rm -f lambda.zip
	zip -j -r lambda.zip lambda
	aws lambda update-function-code --function-name=kindle-vocab --zip-file=fileb://lambda.zip