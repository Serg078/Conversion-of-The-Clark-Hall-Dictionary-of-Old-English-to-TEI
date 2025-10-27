import{_ as n,C as o,c as r,o as i,j as t,G as s,a as l}from"./chunks/framework.B4KI33d0.js";const _=JSON.parse('{"title":"Search the dictionary","description":"","frontmatter":{},"headers":[],"relativePath":"search/index.md","filePath":"search/index.md"}'),c={name:"search/index.md"};function d(p,e,h,m,f,x){const a=o("SparqlForm");return i(),r("div",null,[e[0]||(e[0]=t("h1",{id:"search-the-dictionary",tabindex:"-1"},[l("Search the dictionary "),t("a",{class:"header-anchor",href:"#search-the-dictionary","aria-label":'Permalink to "Search the dictionary"'},"​")],-1)),e[1]||(e[1]=t("p",null,"This page provides various ways to search within the RDFa annotations of the dictionary",-1)),s(a,{config:{endpoints:["http://localhost:5173/clark_hall_tei_rdfa.xml"],parameters:[{variable:"word",type:"string",label:"Dictionary entry",placeholder:"bliss"}]},sparql:`
PREFIX ontolex: <http://www.w3.org/ns/lemon/ontolex#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?definition
WHERE {
	?s a ontolex:LexicalEntry ;
	   ontolex:canonicalForm/ontolex:writtenRep "\${word}"@ang ;
	   ontolex:sense+/rdfs:label ?definition .
} LIMIT 50
`,template:`<p><strong>Error</strong>: No template found.</p>
`})])}const y=n(c,[["render",d]]);export{_ as __pageData,y as default};
