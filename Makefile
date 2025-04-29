install:
	cp fk-files $(DESTDIR)/usr/bin/fk-files

uninstall:
	rm -f $(DESTDIR)/usr/bin/fk-files
	rm -f $(DESTDIR)/usr/share/applications/fk-files.desktop
