# Search the dictionary by morphological properties

This page provides a way to search within the RDFa annotations of the dictionary filtering by morphological information. Values for morphological categories should be from the [LexInfo](https://lexinfo.net) ontology, e.g. "noun", "singular", "past", etc. Caution: execution could be slow.

:::form

```json params
{
	"endpoints": [
		"https://clark-hall-tei-rdfa.netlify.app/clark_hall_tei_rdfa.xml",
		"https://lexinfo.net/ontology/2.0/lexinfo.owl"
	],
	"parameters": [
		{
			"variable": "pos",
			"type": "string",
			"label": "Part of speech",
			"placeholder": "noun"
		},
		{
			"variable": "gender",
			"type": "string",
			"label": "Gender",
			"placeholder": "masculine"
		},
		{
			"variable": "number",
			"type": "string",
			"label": "Number",
			"placeholder": "singular"
		}
	]
}
```

```sparql
PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX lexinfo: <http://www.lexinfo.net/ontology/2.0/lexinfo#>

SELECT DISTINCT ?form ?definition ?pos ?gender ?number
WHERE {
	?s a ontolex:LexicalEntry .

	   OPTIONAL { ?s ontolex:canonicalForm/ontolex:writtenRep ?form . }
	   OPTIONAL { ?s ontolex:sense/rdfs:label ?definition . }

	   OPTIONAL { ?s lexinfo:partOfSpeech/rdfs:label ?pos . }
	   OPTIONAL { ?s lexinfo:gender/rdfs:label ?gender . }
	   OPTIONAL { ?s lexinfo:number/rdfs:label ?number . }

	   FILTER("${pos}" = "" || (BOUND(?pos) && ?pos = "${pos}"))
	   FILTER("${number}" = "" || (BOUND(?number) && ?number = "${number}"))
	   FILTER("${gender}" = "" || (BOUND(?gender) && ?gender = "${gender}"))

} LIMIT 50
```

:::form