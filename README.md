# Making a simple mail watcher working on K8s

To make such a watcher, there are two important parts :

1. Coding the watcher in Python and testing it locally
2. Making its docker image automatically when you update the watcher's code on GitHub
3. Scheduling a cronjob using Flux-CD to run it on GCP's cluster with K8s at fixed hours

I'll assume you know Python, Git and GitHub, are familiar with GCP's service accounts and have access to a working GCP cluster.

## Coding the watcher

Here is an example of a program that looks for a mail in a mailbox and saves it attachment in a directory :

```python
import datetime
import os
from mailutility import MailMonitor
import logging
from transparentpath import Path
Path.set_global_fs("gcs", bucket=os.environ["BUCKET"])

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    thedate = datetime.datetime.now().date()
    mail = MailMonitor(os.environ["MAIL_AUTOMAT"], token=os.environ["PASSWD_AUTOMAT"])
    save_path = Path(os.environ["ATTACHMENT_PATH"])
    if not save_path.exists():
        save_path.mkdir()

    logger.info(f"Fetching mail on {thedate.strftime('%Y-%m-%d')}...")
    mail.fetch_one_mail(
        save_dir=save_path,
        date=thedate,
        subject=os.environ["SUBJECT"],
        sender=os.environ["SENDER"],
        modes={"start": "exact", "end": "exact"},
        state="ALL",
    )
    logger.info(f"Attachment saved in {save_path}")
```

A possible set of environment variables could be:

* **MAIL_AUTOMAT**=automat@mycorporation.com, *the address receiving the mail*
* **PASSWD_AUTOMAT**=something, *the password of the previous address*
* **BUCKET**=some_bucket, *the bucket where the attachment will be saved*
* **ATTACHMENT_PATH**=some_dir, *the directory in the bucket where the attachment will be saved*
* **GOOGLE_APPLICATION_CREDENTIALS**=path_to_json_cred, *only for local test*
* **SUBJECT**=My subject contains, *Chain of character that must be present in the mail's subjet to be seen by this watcher*
* **SENDER**=bob.bib@bub.com, *mail address of the sender*

If you run your code locally, you can put them in a *.env* file, and load them using *load_dotenv*, available in the *python-dotenv* package.

This code will look in the inbox of *automat@mycorporation.com* for a mail containing *My subject contains* in the subject sent *today* by *bob.bib@bub.com*. If no mail is found, the program finishes like that, but if a mail is found the program will save its attachment in *gs://some_bucket/some_dir/attachment_name*, where *attachment_name* depends on the mail content.

## Making the docker image automatically when you update the watcher's code on GitHub

Your package needs to respect the following architecture :

```bash
.
├── Dockerfile
├── main.py
├── README.md
├── requirements.txt
├── .github
│   └── workflows
│       └── push.yaml
└── .gitignore
```

In our example, our Dockerfile would be

```
FROM python:3.9-slim
COPY ./ /watcher
WORKDIR /watcher
RUN pip install -U pip && pip install -r requirements.txt
```

The GitHub workflow file *push.yaml* can look like that :

```
on:
  push:
    branches:
      - master

name: push
jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - name: checkout repo
        uses: actions/checkout@v2
        with:
          token: ${{ secrets.ORG_TOKEN_CICD }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9

      - name: Set up Cloud SDK for GCR access
        uses: google-github-actions/setup-gcloud@master
        with:
          project_id: ${{ secrets.ORG_PROD_PROJECT}}
          service_account_key: ${{ secrets.ORG_PYPI_PROD_CRED }}
          export_default_credentials: true

      - name: Use gcloud as a Docker credential helper
        run: |
          gcloud auth configure-docker
          docker build -t eu.gcr.io/${{ secrets.ORG_PROD_PROJECT }}/mail_watcher_example:latest -f Dockerfile .
          docker push eu.gcr.io/${{ secrets.ORG_PROD_PROJECT }}/mail_watcher_example:latest

```

Where you need to have configured, in your profile's or your organization profile's settings, the following secrets : 
* **ORG_TOKEN_CICD** : GitHub token allowing access to your repository (only necessary if the repository is private)
* **ORG_PROD_PROJECT**: the identifier of the GCP project your docker image must be sent to
* **ORG_PYPI_PROD_CRED** : the content of the json credentials file corresponding to any service account having write access to Google Cloud Registry

## Making the cronjob

Making the
