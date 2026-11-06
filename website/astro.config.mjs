// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { existsSync, readFileSync } from 'node:fs';

// prepare-pdfs.mjs writes this catalog before Astro starts; hide the section while it is empty.
const pdfCatalog = new URL('./src/generated/pdfs.json', import.meta.url);
const hasPdfs = existsSync(pdfCatalog) && JSON.parse(readFileSync(pdfCatalog, 'utf8')).length > 0;

export default defineConfig({
  integrations: [
    starlight({
      title: 'APM · Arquitectura TI',
      description: 'Documentación y presentaciones de avance del portafolio de aplicaciones.',
      defaultLocale: 'root',
      locales: { root: { label: 'Español', lang: 'es' } },
      logo: { src: './src/assets/logo.svg' },
      sidebar: [
        { label: 'Inicio', link: '/' },
        { label: 'Demo MVP', link: 'https://apm-mvp-5dcohejqua-uc.a.run.app', badge: 'en vivo' },
        {
          label: 'Arquitectura del sistema',
          items: [
            { label: 'Visión general', slug: 'arquitectura' },
            { label: 'Catálogos', slug: 'arquitectura/catalogos' },
            { label: 'Modelo de datos', slug: 'arquitectura/modelo-datos' },
            { label: 'Gobierno de datos', slug: 'arquitectura/gobierno-datos' },
            { label: 'IA agéntica', slug: 'arquitectura/ia-agentes' },
            { label: 'Arquitectura de solución', slug: 'arquitectura/arquitectura-solucion' },
            { label: 'Interfaz (UI/UX)', slug: 'arquitectura/interfaz' },
            { label: 'Roadmap', slug: 'arquitectura/roadmap' },
            { label: 'Soluciones similares', slug: 'arquitectura/soluciones-similares' },
          ],
        },
        ...(hasPdfs ? [{ label: 'Documentos PDF', link: '/documentos/' }] : []),
        { label: 'Presentaciones', link: '/presentaciones/' },
        {
          label: 'Guías',
          items: [
            { label: 'Guía técnica del MVP', slug: 'guias/guia-tecnica-mvp' },
            { label: 'Editar y regenerar diagramas', slug: 'guias/diagramas' },
            { label: 'Publicar documentación', slug: 'guias/publicacion' },
          ],
        },
      ],
      customCss: ['./src/styles/custom.css'],
      head: [
        {
          tag: 'script',
          attrs: { type: 'module' },
          content: `
            // Lightbox: clic sobre cualquier imagen de contenido para ampliarla.
            (() => {
              const overlay = document.createElement('div');
              overlay.className = 'apm-zoom';
              overlay.setAttribute('role', 'dialog');
              overlay.setAttribute('aria-modal', 'true');
              overlay.setAttribute('aria-label', 'Imagen ampliada');
              const overlayImg = document.createElement('img');
              overlay.appendChild(overlayImg);
              const close = () => overlay.classList.remove('apm-zoom--open');
              overlay.addEventListener('click', close);
              document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape') close();
              });
              document.body.appendChild(overlay);
              const open = (src, alt) => {
                overlayImg.src = src;
                overlayImg.alt = alt || '';
                overlay.classList.add('apm-zoom--open');
              };
              document.addEventListener('DOMContentLoaded', () => {
                document.querySelectorAll('.sl-markdown-content img:not(.not-content img)').forEach((img) => {
                  img.addEventListener('click', (event) => {
                    event.preventDefault();
                    open(img.currentSrc || img.src, img.alt);
                  });
                });
              });
            })();
          `,
        },
      ],
    }),
  ],
});
