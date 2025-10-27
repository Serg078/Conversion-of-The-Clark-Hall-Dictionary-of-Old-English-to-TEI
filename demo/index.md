---
# https://vitepress.dev/reference/default-theme-home-page
layout: home

hero:
  name: "Clark Hall Dictionary"
  text: "This is a web interface for the TEI+RDFa edition of the Clark Hall Old English Dictinary"
  tagline: 
  actions:
    - theme: brand
      text: Browse the TEI
      link: /read
    - theme: alt
      text: Search the RDF
      link: /search

features:
  - title: Converted to TEI Lex-0
    details: Using a tailor-made context-free grammar, the dictionary was converted to TEI
  - title: Enriched with RDFa annotations
    details: Each entry, form and sense were annotated with RDFa
  - title: Web interface with CETEicean and VitePress-SPARQL
    details: This web interface is a static website made using VitePress, CETEicean to display TEI, and vitepress-plugin-sparql to to query RDF within TEI attributes
---

