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
    }),
  ],
});
