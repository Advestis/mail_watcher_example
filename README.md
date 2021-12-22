# Making a simple mail watcher working on K8s

To make such a watcher, there are two important parts :

1. Coding the watcher in Pythonn abd testing it locally
2. Scheduling a cronjob using Flux-CD to run it on GCP's cluster with K8s at fixed hours

## Making the watcher container

### Making the code

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

* **MAIL_AUTOMAT**=automat@advestis.com, *the address receiving the mail*
* **PASSWD_AUTOMAT**=<ask Philippe :)>, *the password of the previous address*
* **BUCKET**=some_bucket, *the bucket where the attachment will be saved*
* **ATTACHMENT_PATH**=some_dir, *the directory in the bucket where the attachment will be saved*
* **GOOGLE_APPLICATION_CREDENTIALS**=path_to_json_cred, *only for local test*
* **SUBJECT**=Trades systématiques du , *Chain of character that must be present in the mail's subjet to be seen by this watcher*
* **SENDER**=tony.boisseau@ecofi.fr, *mail address of the sender*

This code will look in the inbox of *automat@advestis.com* for a mail containing *Trades systématiques du * in the subject sent *today* by *tony.boisseau@ecofi.fr*. If no mail is found, the program finishes like that, but if a mail is found the program will save its attachment in *gs://some_bucket/some_dir/attachment_name*, where *attachment_name* depends on the mail content.

### Making the docker image

Your code needs to respect the following architecture :

watcher_name
 |_ mail.py (containing the previous code)
 |_ requirements.txt (for our simple example, mailutility and transparentpath are enough)
 |_ Dockerfile


## Making the cronjob

Making the
