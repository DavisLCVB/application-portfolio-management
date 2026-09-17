// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'APM · Arquitectura TI',
      description: 'Documentación y presentaciones de avance del portafolio de aplicaciones.',
      defaultLocale: 'root',
      locales: { root: { label: 'Español', lang: 'es' } },
      logo: { src: './src/assets/logo.svg' },
      sidebar: [
        { label: 'Inicio', slug: 'index' },
        {
          label: 'Arquitectura del sistema',
          items: [
            { label: 'Visión general', slug: 'arquitectura' },
            { label: 'Catálogos', slug: 'arquitectura/catalogos' },
            { label: 'IA agéntica', slug: 'arquitectura/ia-agentes' },
            { label: 'Roadmap', slug: 'arquitectura/roadmap' },
          ],
        },
        { label: 'Documentos PDF', link: '/documentos/' },
        { label: 'Guías', items: [{ autogenerate: { directory: 'guias' } }] },
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
                document.querySelectorAll('.sl-markdown-content img').forEach((img) => {
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
