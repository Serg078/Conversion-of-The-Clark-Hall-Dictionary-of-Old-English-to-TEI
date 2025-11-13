# Search the dictionary by English or Latin translation

This page shows a federated query that uses DBnary to search for Latin equivalents for the entries in Clark Hall.

:::form

```json params
{
	"endpoints": [
		"http://localhost:5173/clark_hall_tei_rdfa.xml"
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

SELECT DISTINCT ?form ?definition
WHERE {
	?s a ontolex:LexicalEntry ;
	   ontolex:canonicalForm/ontolex:writtenRep "${word}"@ang ;
	   ontolex:sense+/rdfs:label ?definition .
} LIMIT 50
```

:::form
