install:
	pyinstaller --onefile --windowed --name fk-files main.py
	cp dist/fk-files $(DESTDIR)/usr/bin/fk-files
	mkdir -p $(DESTDIR)/usr/share/applications
	cp fk-files.desktop $(DESTDIR)/usr/share/applications/

uninstall:
	rm -f $(DESTDIR)/usr/bin/fk-files
	rm -f $(DESTDIR)/usr/share/applications/fk-files.desktop
