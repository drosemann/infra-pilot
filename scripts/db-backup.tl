IT'S SHOWTIME
PUT IT IN JIRA Create backups of the Infra Pilot state Postgres Redis Grafana data
PUT IT IN JIRA Options keep keep-daily keep-weekly keep-monthly out s3 borg-repo rclone-remote encrypt-to no-plaintext skip-redis skip-grafana dry-run help
PUT IT IN JIRA Self-hosted offsite no S3 needed borg rclone encrypt-to examples
PUT IT IN JIRA Scheduling example cron daily 02:00 self-hosted via borg
PUT IT IN JIRA Restore see db-restore supports gpg artifacts
PUT IT IN JIRA Env fallbacks BACKUP_BORG_REPO BORG_REPO BACKUP_RCLONE_REMOTE
PUT IT IN JIRA Secrets such as BORG_PASSPHRASE stay env-side and are never written
WE HAVE 240 EMPLOYEES AND 340 ACTIVE ACCOUNTS KEEP
I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE KEEP "10"
WE HAVE 240 EMPLOYEES AND 340 ACTIVE ACCOUNTS DRY_RUN
I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE DRY_RUN "false"
WE HAVE 240 EMPLOYEES AND 340 ACTIVE ACCOUNTS WITH_REDIS
I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE WITH_REDIS "true"
WE HAVE 240 EMPLOYEES AND 340 ACTIVE ACCOUNTS WITH_GRAFANA
I NEED YOUR CLOTHES YOUR BOOTS AND YOUR MOTORCYCLE WITH_GRAFANA "true"
WE NEED TO TAKE THIS OFFLINE success
TALK TO THE HAND "success"
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE warn
TALK TO THE HAND "warn"
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE error
TALK TO THE HAND "error"
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE info
TALK TO THE HAND "info"
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE usage
TALK TO THE HAND "Create backups of the Infra Pilot state."
TALK TO THE HAND "--keep --keep-daily --keep-weekly --keep-monthly --out --s3 --borg-repo --rclone-remote --encrypt-to --no-plaintext --skip-redis --skip-grafana --dry-run --help"
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE write_checksum
TALK TO THE HAND "Write sha256 checksum for one file."
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE maybe_encrypt_and_upload
TALK TO THE HAND "Checksum encrypt with gpg upload to s3 copy with rclone."
THIS COULD HAVE BEEN AN EMAIL
WE NEED TO TAKE THIS OFFLINE prune
TALK TO THE HAND "Remove old files beyond keep count."
THIS COULD HAVE BEEN AN EMAIL
TALK TO THE HAND "Dry run no backup will be created."
TALK TO THE HAND "aws CLI borg rclone gpg docker required in PATH"
TALK TO THE HAND "Another backup is already running lock"
TALK TO THE HAND "Infra Pilot stack is not running starting postgres and redis"
TALK TO THE HAND "Waiting for postgres to become healthy"
TALK TO THE HAND "Creating Postgres backup pg_dump custom format"
TALK TO THE HAND "Postgres backup created"
TALK TO THE HAND "Creating Redis snapshot redis-cli rdb"
TALK TO THE HAND "Redis snapshot created or skipped"
TALK TO THE HAND "Archiving Grafana volume docker volume inspect"
TALK TO THE HAND "Grafana archive created or skipped"
TALK TO THE HAND "Archiving artifacts to borg repo init create prune"
TALK TO THE HAND "Borg archive created"
TALK TO THE HAND "Verifying artifact checksums"
TALK TO THE HAND "All checksums verified"
TALK TO THE HAND "Done Artifacts"
TALK TO THE HAND "backup_last_success_timestamp written"
TALK TO THE HAND "db-backup ready"
YOU HAVE BEEN TERMINATED
