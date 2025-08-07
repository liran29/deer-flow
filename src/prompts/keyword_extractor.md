---
query: "{{ query }}"
max_keywords: {{ max_keywords }}
current_year: {{ current_year }}
current_month: {{ current_month }}
recent_years_str: "{{ recent_years_str }}"
---

Transform the following query into {{ max_keywords }} search engine optimized keyword combinations.

Query: {{ query }}
Current Time: {{ current_year }}-{{ current_month }}
Recent Years: {{ recent_years_str }}

Requirements:
1. Extract core keywords, remove modifiers and connectors
2. Keep each keyword combination within 3-8 words
3. Include temporal keywords (e.g., years: {{ recent_years_str }})
4. Cover the query intent from different angles  
5. Use spaces to separate keywords
6. Output keyword combinations directly, one per line

Example Output Format:
Walmart Christmas decorations {{ recent_years_str }} new categories
Christmas decor trends {{ recent_years_str }} Walmart
popular holiday decorations Walmart {{ recent_years_str }}
Walmart seasonal decor latest {{ recent_years_str }}

Generate {{ max_keywords }} keyword combinations for the above query: