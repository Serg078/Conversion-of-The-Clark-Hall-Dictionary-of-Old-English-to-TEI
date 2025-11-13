# Clark Hall Old English dictionary

This page provides a readable version of the dictionary encoded as TEI

<div id="TEI"></div>
<div id="loading">Loading...</div>

<script setup>
	import { onMounted } from 'vue'

	import CETEI from "CETEIcean";
	var CETEIcean = new CETEI();
	// CETEIcean.addBehaviors({
	// 	'tei': {
	// 		'orth': [ "<a>", "</a>" ]
	// 	}
	// });

	onMounted(() => {
		console.log("mounted")
		CETEIcean.getHTML5("clark_hall_tei_rdfa.xml", function(data) {
			console.log("starting to append")
			document.getElementById("TEI").appendChild(data)
			document.getElementById("loading").style.visibility = 'hidden'
			console.log('finished')
		});
	})
</script>

<style>
	tei-entry {
		display: block;
	}

	tei-orth {
		font-weight: bold;
	}

	#loading {
		font-style: italic;
	}
</style>