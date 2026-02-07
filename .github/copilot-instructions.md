# Project Instructions



## Global Override Rules

These instructions will override any other instructions provided in the repository for GitHub Copilot.

- Do not write code before stating assumptions.
- Do not claim correctness you haven't verified.
- Do not handle only the happy path.
- Under what conditions does this work?
- What are the edge cases?
- What are the security implications?
- What are the maintainability implications?


## Priority Project Directions

- Do not use `<script></script>` tags in HTML templates. Instead, place JavaScript code in separate `.js` files within the `static/js/` directory and reference them appropriately in the HTML.
- Ensure that all new JavaScript code is added to the `static/js/` directory and that HTML templates reference these scripts without using inline JavaScript.
- When handling form data in Django views, always return structured JSON responses for errors to facilitate debugging on the client side, rather than returning generic HTTP error responses.
- When closing a `{% block <name> %}` you should always close the block with an endblock name matching the opened block that is being closed (e.g. `{% block content %}...{% endblock content %}`)