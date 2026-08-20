// @ts-check
// `@type` JSDoc annotations allow editor autocompletion and type checking
// (when paired with `@ts-check`).
// There are various equivalent ways to declare your Docusaurus config.
// See: https://docusaurus.io/docs/api/docusaurus-config

import {themes as prismThemes} from 'prism-react-renderer';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: '2026A-420-5D1-MA-Gr2',
  tagline: 'Projet 3',
  // Version carrée et simplifiée du logo : le cadre large de 5D1.svg est
  // illisible à 16-32px. Sert aussi de logo dans la barre de navigation.
  favicon: 'img/logo-square.svg',

  // Future flags, see https://docusaurus.io/docs/api/docusaurus-config#future
  future: {
    v4: true, // Improve compatibility with the upcoming Docusaurus v4
  },

  // Set the production url of your site here
  url: 'https://archambaultv.github.io',
  // Set the /<baseUrl>/ pathname under which your site is served
  // For GitHub pages deployment, it is often '/<projectName>/'
  baseUrl: '/2026A-420-5D1-MA-Gr2/',

  // GitHub pages deployment config.
  // If you aren't using GitHub pages, you don't need these.
  organizationName: 'archambaultv', // Usually your GitHub org/user name.
  projectName: '2026A-420-5D1-MA-Gr2', // Usually your repo name.

  onBrokenLinks: 'throw',
  markdown : {
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  // Even if you don't use internationalization, you can use this field to set
  // useful metadata like html lang. For example, if your site is Chinese, you
  // may want to replace "en" with "zh-Hans".
  i18n: {
    defaultLocale: 'fr',
    locales: ['fr'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: './sidebars.js',
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/archambaultv/2026A-420-5D1-MA-Gr2/tree/main/',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      docs:{
        sidebar: {
          hideable: true,
          autoCollapseCategories: true,
        }
      },
      // Carte de partage (aperçu dans MIO, Teams, Discord...). Doit être en PNG/JPG :
      // les réseaux sociaux ne rendent pas les SVG. Version rasterisée de la police
      // Patrick Hand (SIL OFL 1.1) — c'est la police à réutiliser pour la régénérer.
      image: 'img/social-card.png',
      colorMode: {
        respectPrefersColorScheme: true,
      },
      navbar: {
        title: 'Projet 3',
        logo: {
          // Version carrée : le logo large est réduit à la hauteur de la barre
          // de navigation, où le code du cours devient minuscule.
          alt: 'Projet 3',
          src: 'img/logo-square.svg',
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'scheduleSidebar',
            position: 'left',
            label: 'Échéancier',
          },
          {
            type: 'docSidebar',
            sidebarId: 'evaluations',
            position: 'left',
            label: 'Évaluations',
          },
          {href: 'https://archambaultv.github.io/git', label: 'Tutoriel Git', position: 'right'},
          {
            href: 'https://github.com/archambaultv/2026A-420-5D1-MA-Gr2',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        copyright: `Cette œuvre est placée sous licence <a href="https://creativecommons.org/licenses/by/4.0/deed.fr" target="_blank" rel="noopener noreferrer">Creative Commons Attribution 4.0 International</a>. Construit avec <a href="https://docusaurus.io/" target="_blank" rel="noopener noreferrer">Docusaurus</a>.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
  // plugins: [
  //   [require.resolve('docusaurus-lunr-search'), {
  //     languages: ['fr'],
  //   }]
  // ]
};

export default config;
