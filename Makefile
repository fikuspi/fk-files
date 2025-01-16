install:
	mkdir -p $(DESTDIR)/usr/bin
	cp fk_files.py $(DESTDIR)/usr/bin/fk-files
	chmod +x $(DESTDIR)/usr/bin/fk-files
	mkdir -p $(DESTDIR)/usr/share/applications
	cp fk-files.desktop $(DESTDIR)/usr/share/applications/

uninstall:
	rm -f $(DESTDIR)/usr/bin/fk-files
	rm -f $(DESTDIR)/usr/share/applications/fk-files.desktop
