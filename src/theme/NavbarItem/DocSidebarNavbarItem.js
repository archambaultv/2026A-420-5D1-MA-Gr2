/**
 * Remplace @theme/NavbarItem/DocSidebarNavbarItem (les entrées de type
 * `docSidebar` de la barre de navigation : Échéancier, Notes de cours,
 * Évaluations).
 *
 * Comportement d'origine : le lien pointe toujours vers la *première* page de
 * la section. On perd donc sa place chaque fois qu'on change de section.
 *
 * Ici, la dernière page visitée de chaque section est retenue dans le stockage
 * local du navigateur, et le lien y retourne. Docusaurus n'offre rien de tel;
 * en revanche il fournit les deux pièces utilisées ci-dessous : `useStorageSlot`
 * (accès au stockage qui ne casse rien s'il est indisponible) et la liste des
 * documents du site, qui sert à vérifier que la page mémorisée existe toujours.
 *
 * Ce fichier est une version modifiée du composant de Docusaurus 3.10
 * (MIT, Facebook, Inc.). À revalider lors d'une mise à jour majeure.
 */

import React, {useEffect, useMemo} from 'react';
import {
  useActiveDocContext,
  useDocsVersionCandidates,
  useLayoutDocsSidebar,
} from '@docusaurus/plugin-content-docs/client';
import {useStorageSlot} from '@docusaurus/theme-common';
import DefaultNavbarItem from '@theme/NavbarItem/DefaultNavbarItem';

// Une clé par section, et par instance du plugin docs au cas où il y en aurait
// plusieurs un jour. Docusaurus y ajoute lui-même son préfixe.
function storageKey(docsPluginId, sidebarId) {
  return `docusaurus.lastVisitedDoc.${docsPluginId ?? 'default'}.${sidebarId}`;
}

export default function DocSidebarNavbarItem({
  sidebarId,
  label,
  docsPluginId,
  ...props
}) {
  const {activeDoc} = useActiveDocContext(docsPluginId);
  const sidebarLink = useLayoutDocsSidebar(sidebarId, docsPluginId).link;

  const isActive = activeDoc?.sidebar === sidebarId;
  const activePath = activeDoc?.path;

  const [lastVisited, storage] = useStorageSlot(
    storageKey(docsPluginId, sidebarId),
  );

  // On mémorise la page courante tant qu'on est dans cette section.
  useEffect(() => {
    if (isActive && activePath) {
      storage.set(activePath);
    }
  }, [isActive, activePath, storage]);

  // Les pages qui existent réellement dans cette section. Sans cette
  // vérification, une page mémorisée puis renommée ou supprimée enverrait
  // vers une 404.
  const versions = useDocsVersionCandidates(docsPluginId);
  const sectionPaths = useMemo(
    () =>
      new Set(
        versions
          .flatMap((version) => version.docs)
          .filter((doc) => doc.sidebar === sidebarId)
          .map((doc) => doc.path),
      ),
    [versions, sidebarId],
  );

  if (!sidebarLink) {
    throw new Error(
      `DocSidebarNavbarItem: Sidebar with ID "${sidebarId}" doesn't have anything to be linked to.`,
    );
  }

  // `lastVisited` vaut null au rendu serveur et pendant l'hydratation : le lien
  // pointe alors vers la première page, comme le composant d'origine.
  const to = sectionPaths.has(lastVisited) ? lastVisited : sidebarLink.path;

  return (
    <DefaultNavbarItem
      exact
      {...props}
      isActive={() => isActive}
      label={label ?? sidebarLink.label}
      to={to}
    />
  );
}
