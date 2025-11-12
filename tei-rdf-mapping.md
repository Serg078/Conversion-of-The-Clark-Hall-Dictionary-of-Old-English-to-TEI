| Element       | XPath                     | OntoLex              |
|---------------|---------------------------|----------------------|
| Lexical entry | `//entry`                 | ontolex:LexicalEntry |
| Form          | `//entry/form`            | ontolex:Form         |
| Written Repr. | `//entry/form/orth`       | ontolex:writtenRep.  |
| Morph prop.   | `//entry/gramGrp/gram`    | lexinfo:*.           |
| Sense         | `//entry/sense`           | ontolex:Sense        |
| Sense label   | `//entry/sense/cit/quote` | rdfs:label           |