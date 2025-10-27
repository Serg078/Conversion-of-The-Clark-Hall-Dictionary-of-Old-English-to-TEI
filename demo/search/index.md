# Search the dictionary by entry

This page provides a simple way to search within the RDFa annotations of the dictionary

:::form

```json params
{
	"endpoints": [
		"https://clark-hall-tei-rdfa.netlify.app/clark_hall_tei_rdfa.xml"
	],
	"parameters": [
		{
			"variable": "word",
			"type": "string",
			"label": "Dictionary entry",
			"placeholder": "bliss"
		}
	]
}
```

```sparql
PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?definition
WHERE {
	?s a ontolex:LexicalEntry ;
	   ontolex:canonicalForm/ontolex:writtenRep "${word}"@ang ;
	   ontolex:sense+/rdfs:label ?definition .
} LIMIT 50
```

:::form