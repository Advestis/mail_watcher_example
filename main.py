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
