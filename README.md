# yt_summarizer

This is a sample project that creates a transcription and summarizes youtube text.

## Create Conda Env:

```
conda env export | grep -v "^prefix:" > environment.yml
```

## Load Conda Env:

```
conda env create -f environment.yml
```

## Run the api server:

```
uvicorn main:app --host 0.0.0.0 --port 8000
```
