"""
Test script to verify the summary rendering fix
"""

import re

def test_markdown_cleaning():
    """Test the improved markdown cleaning logic"""

    # Sample text with markdown formatting (similar to what comes from PDF extraction)
    sample_text = """
## Extracted Content

### Introduction
This is **bold text** and this is *italic text*. Here's some `inline code`.

- First bullet point
- Second bullet point
* Third point with asterisk

1. Numbered list item
2. Another numbered item

> This is a blockquote
> With multiple lines

```python
def example():
    return "code block"
```

Here's a [link text](http://example.com) in the content.

#### Subsection Header
More content here with ### headers and **formatting**.
"""

    print("ORIGINAL TEXT:")
    print("-" * 50)
    print(sample_text)
    print("-" * 50)

    # Apply the same cleaning logic from our fix
    clean_content = sample_text

    # Remove markdown headers (# ## ### etc)
    clean_content = re.sub(r'^#+\s+', '', clean_content, flags=re.MULTILINE)

    # Remove bold/italic markers
    clean_content = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_content)
    clean_content = re.sub(r'\*(.*?)\*', r'\1', clean_content)

    # Remove code blocks
    clean_content = re.sub(r'```[\s\S]*?```', '', clean_content)

    # Remove inline code
    clean_content = re.sub(r'`([^`]+)`', r'\1', clean_content)

    # Remove bullet points and list markers
    clean_content = re.sub(r'^[\-\*\+]\s+', '', clean_content, flags=re.MULTILINE)
    clean_content = re.sub(r'^\d+\.\s+', '', clean_content, flags=re.MULTILINE)

    # Remove blockquotes
    clean_content = re.sub(r'^>\s+', '', clean_content, flags=re.MULTILINE)

    # Remove links but keep link text
    clean_content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_content)

    # Remove excessive whitespace and newlines
    clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
    clean_content = re.sub(r'[ \t]+', ' ', clean_content)
    clean_content = clean_content.strip()

    print("\nCLEANED TEXT:")
    print("-" * 50)
    print(clean_content)
    print("-" * 50)

    # Extract sentences for summary
    sentences = clean_content.split('.')
    summary_text = ''
    for sentence in sentences:
        if len(summary_text) < 400 and len(sentence.strip()) > 20:
            summary_text += sentence.strip() + '. '
            if len(summary_text) > 300:
                break

    print("\nGENERATED SUMMARY:")
    print("-" * 50)
    print(summary_text.strip() if summary_text else clean_content[:400])
    print("-" * 50)

if __name__ == "__main__":
    test_markdown_cleaning()
    print("\n✅ Test completed successfully!")