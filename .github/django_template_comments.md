## Django Template Comments

In Django templates, comments can be added using specific syntax that ensures they are not rendered in the final HTML output.

### 1. Single-Line Comments
Single-line comments are enclosed within `{# ... #}`.  
These comments will not appear in the rendered HTML.

**Example:**
```django
{# This is a single-line comment #}
<p>This paragraph will be rendered.</p>
```

### 2. Multi-Line Comments
For multi-line comments, use `{% comment %} ... {% endcomment %}`.  
This is useful for commenting out blocks of code or adding detailed notes.

**Example:**
```django
{% comment %}
<p>This block of code is commented out and won't appear in the output.</p>
{% endcomment %}
```

### Unsupported Comment Syntax
The following comment styles are **not supported** in Django templates:
- `<!-- comment -->` (HTML-style comments)  
- `/* comment */` (CSS-style comments)  
- `// comment` (JavaScript-style comments)  

⚠️ **Important:**  
`{# ... #}` and `{% comment %} ... {% endcomment %}` are the only valid ways to add comments in Django templates.  
Using unsupported styles like `<!-- -->` may still render the content inside them, especially if it contains Django template tags.
