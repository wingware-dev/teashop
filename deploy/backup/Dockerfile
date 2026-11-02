# restic plus the PostgreSQL 17 client tools (matching the db service), for
# encrypted off-site backups and restore tests.
FROM postgres:18-alpine
RUN apk add --no-cache restic curl bash
COPY backup.sh restore-test.sh /usr/local/bin/
ENTRYPOINT []
CMD ["backup.sh"]
