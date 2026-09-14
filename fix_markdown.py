import re

with open('index.html', 'r') as f:
    content = f.read()

old = "assistantDiv.textContent = fullText;"
new = "assistantDiv.innerHTML = marked.parse(fullText);"

content = content.replace(old, new)

old = "<title>Anthropic Job Agent</title>"
new = '<title>Anthropic Job Agent</title>\n<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>'

content = content.replace(old, new)

with open('index.html', 'w') as f:
    f.write(content)

print("Done!")
