#!/usr/bin/env python3
"""Fix Nginx config to add no-cache for index.html"""

with open('/etc/nginx/sites-enabled/easy-social', 'r') as f:
    content = f.read()

# Find and replace the broken SPA section
start = content.find('# SPA fallback')
end = content.find('# Cache static')

if start == -1 or end == -1:
    print(f'ERROR: markers not found (SPA={start}, Cache={end})')
    exit(1)

new_section = """# SPA fallback - all other routes go to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # No-cache for index.html
    location = /index.html {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        expires 0;
    }

    """

content = content[:start] + new_section + content[end:]

with open('/etc/nginx/sites-enabled/easy-social', 'w') as f:
    f.write(content)

print('PATCHED OK')
