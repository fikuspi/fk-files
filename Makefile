install:
cp fk-files $(DESTDIR)/usr/bin/fk-files
chmod 777 /bin/fk-files
uninstall:
rm -f $(DESTDIR)/usr/bin/fk-files
