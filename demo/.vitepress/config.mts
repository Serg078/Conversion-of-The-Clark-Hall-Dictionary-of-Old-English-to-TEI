import { defineConfig } from 'vitepress'
import { SparqlPlugin } from 'vitepress-plugin-sparql'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "Clark Hall Dictionary",
  description: "This is a web interface for the TEI+RDFa edition of the Clark Hall Old English Dictinary",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'Read', link: '/read' },
      { text: 'Search', link: '/search/' }
    ],

    sidebar: [
      {
        text: 'Search',
        items: [
          { text: 'Entry', link: '/search/' },
          { text: 'Grammar', link: '/search/morph.md' },
          //{ text: 'Latin translation', link: '/search/latin.md' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://anonymous.4open.science/r/Conversion-of-The-Clark-Hall-Dictionary-of-Old-English-to-TEI-234C/README.md' }
    ]
  },
  vite: {
    plugins: [SparqlPlugin()]
  }
})
