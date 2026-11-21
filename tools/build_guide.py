"""docs/guide.html + docs/sources.html → Hexcrawl-Forge-Guide.pdf (headless Chrome)."""
import os, subprocess, shutil
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
subprocess.run(['python3', os.path.join(D, 'tools', 'sources_report.py')], check=True)
g = open(os.path.join(D, 'docs', 'guide.html')).read().replace('<!--SOURCES-->', open(os.path.join(D, 'docs', 'sources.html')).read())
tmp = os.path.join(D, 'docs', '_guide_full.html'); open(tmp, 'w').write(g)
chrome = next(shutil.which(c) for c in ('google-chrome-stable', 'chromium', 'google-chrome') if shutil.which(c))
subprocess.run([chrome, '--headless', '--disable-gpu', '--no-pdf-header-footer', '--print-to-pdf=' + os.path.join(D, 'Hexcrawl-Forge-Guide.pdf'), 'file://' + tmp], check=True, capture_output=True)
os.remove(tmp)
