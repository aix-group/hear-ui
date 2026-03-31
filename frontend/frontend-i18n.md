# Frontend: i18n und Seitenverwaltung / i18n & Page Management

> **English version below** — Deutsche Version zuerst.

Dieses Dokument beschreibt, wie Internationalisierung (i18n) im Frontend genutzt und neue Seiten oder bestehende Seiten im Frontend bearbeitet werden.

## Internationalisierung (i18n)

Das Frontend verwendet `vue-i18n` für die Internationalisierung. Übersetzungen sind in JSON-Dateien organisiert und nach Sprachen getrennt.

### 1. Übersetzungsdateien finden

Die Übersetzungsdateien befinden sich typischerweise unter `frontend/src/locales/`.

- `en.json`: Englische Übersetzungen
- `de.json`: Deutsche Übersetzungen

Jede Datei enthält Schlüssel-Wert-Paare, wobei der Schlüssel der Referenz-String im Code und der Wert die übersetzte Phrase ist.

### 2. Eine neue Übersetzung hinzufügen oder eine bestehende bearbeiten

1.  **Lokalisierung der Schlüssel**: Öffnen Sie die entsprechende `.json`-Datei für die Sprache, die Sie hinzufügen oder bearbeiten möchten (z.B. `de.json` für Deutsch).
2.  **Hinzufügen/Bearbeiten des Eintrags**:
    *   Wenn Sie eine neue Phrase hinzufügen, wählen Sie einen semantischen Schlüssel, der den Inhalt widerspiegelt (z.B. `welcome.title`, `button.submit`).
    *   Fügen Sie den Schlüssel und die entsprechende übersetzte Phrase hinzu:
        ```json
        {
          "welcome": {
            "title": "Willkommen bei HEAR"
          },
          "button": {
            "submit": "Absenden"
          }
        }
        ```
    *   Achten Sie darauf, dass der Schlüssel in allen Sprachdateien vorhanden ist, um Inkonsistenzen zu vermeiden.
3.  **Verwendung im Vue-Template**:
    Verwenden Sie `$t('your.key.name')` in Ihren Vue-Templates:
    ```vue
    <template>
      <h1>{{ $t('welcome.title') }}</h1>
      <button>{{ $t('button.submit') }}</button>
    </template>
    ```
4.  **Verwendung im JavaScript/TypeScript-Code**:
    Importieren Sie die `useI18n`-Funktion und verwenden Sie `t('your.key.name')`:
    ```typescript
    import { useI18n } from 'vue-i18n';

    export default {
      setup() {
        const { t } = useI18n();
        const message = t('welcome.title');
        return { message };
      }
    };
    ```

### 3. Platzhalter und dynamische Inhalte

Sie können Platzhalter in Übersetzungen verwenden, um dynamische Werte einzufügen:

**`de.json`**:
```json
{
  "greeting": "Hallo {name}, Sie haben {count} neue Nachrichten."
}
```

**Vue-Template**:
```vue
<template>
  <p>{{ $t('greeting', { name: 'Max', count: 5 }) }}</p>
</template>
```

## Seitenverwaltung im Frontend

Das Frontend ist eine Vue.js-Anwendung, die `Vue Router` für die Navigation und Seitenverwaltung verwendet.

### 1. Eine neue Seite hinzufügen

1.  **Vue-Komponente erstellen**: Erstellen Sie eine neue `.vue`-Datei für Ihre Seite unter `frontend/src/routes/` oder einem geeigneten Unterordner.
    Beispiel: `frontend/src/routes/AboutPage.vue`
    ```vue
    <template>
      <div class="about-page">
        <h1>{{ $t('about.title') }}</h1>
        <p>{{ $t('about.content') }}</p>
      </div>
    </template>

    <script setup lang="ts">
    import { useI18n } from 'vue-i18n';

    const { t } = useI18n();
    </script>

    <style scoped>
    /* Scoped styles for the AboutPage */
    </style>
    ```

2.  **Route konfigurieren**: Öffnen Sie die Router-Konfigurationsdatei, typischerweise `frontend/src/router/index.ts`.
    Importieren Sie Ihre neue Komponente und fügen Sie eine neue Route zum `routes`-Array hinzu:
    ```typescript
    import { createRouter, createWebHistory } from 'vue-router';
    import HomePage from '../routes/HomePage.vue';
    import AboutPage from '../routes/AboutPage.vue'; // Importiere deine neue Seite

    const routes = [
      {
        path: '/',
        name: 'Home',
        component: HomePage,
      },
      {
        path: '/about', // Der URL-Pfad für deine Seite
        name: 'About',  // Ein eindeutiger Name für die Route
        component: AboutPage, // Die importierte Vue-Komponente
      },
      // ... weitere Routen
    ];

    const router = createRouter({
      history: createWebHistory(),
      routes,
    });

    export default router;
    ```
    *Hinweis*: Die tatsächliche Struktur kann je nach Projekt leicht variieren. Suchen Sie nach dem `createRouter`-Aufruf.

3.  **Navigation hinzufügen (optional)**: Wenn Sie möchten, dass Benutzer zu Ihrer neuen Seite navigieren können, fügen Sie einen `router-link` in Ihrer Navigationskomponente (z.B. Header, Navbar) hinzu:
    ```vue
    <template>
      <nav>
        <router-link to="/">{{ $t('nav.home') }}</router-link>
        <router-link to="/about">{{ $t('nav.about') }}</router-link>
      </nav>
    </template>
    ```

4.  **Übersetzungen für den Seitentitel und Inhalte hinzufügen**: Vergessen Sie nicht, die entsprechenden i18n-Schlüssel für Ihren Seitentitel und andere Texte in den Übersetzungsdateien zu hinterlegen (siehe Abschnitt "Internationalisierung (i18n)" oben).

### 2. Eine bestehende Seite bearbeiten

1.  **Komponente lokalisieren**: Navigieren Sie zu der `.vue`-Datei der Seite, die Sie bearbeiten möchten (z.B. unter `frontend/src/routes/` oder `frontend/src/components/`).
2.  **Inhalt bearbeiten**: Modifizieren Sie das Template, Skript oder die Stile der Komponente nach Bedarf. Verwenden Sie dabei immer i18n-Schlüssel für alle textuellen Inhalte.
3.  **Übersetzungen aktualisieren**: Wenn Sie neue Texte hinzufügen oder bestehende ändern, stellen Sie sicher, dass die entsprechenden Einträge in den `frontend/src/locales/*.json`-Dateien aktualisiert werden.

Durch die Einhaltung dieser Richtlinien wird die Konsistenz und Wartbarkeit des Frontends gewährleistet.

---

# English Version

This document describes how internationalisation (i18n) is used in the frontend and how to add or edit pages.

## Internationalisation (i18n)

The frontend uses `i18next` (via `i18next-vue`) for internationalisation. Translations are stored in JSON files, one per language.

### 1. Locating translation files

Translation files are located under `frontend/src/locales/`.

- `en.json` — English translations
- `de.json` — German translations

Each file contains key-value pairs where the key is a reference string used in code and the value is the translated phrase.

### 2. Adding or editing a translation

1. **Open the JSON file** for the language you want to modify (e.g. `de.json` for German).
2. **Add / edit the entry** using a semantic key that reflects the content (e.g. `welcome.title`, `button.submit`):
    ```json
    {
      "welcome": {
        "title": "Welcome to HEAR"
      },
      "button": {
        "submit": "Submit"
      }
    }
    ```
   Make sure the key exists in **all** language files to avoid missing translations.
3. **Use in Vue templates** with `$t('your.key.name')`:
    ```vue
    <template>
      <h1>{{ $t('welcome.title') }}</h1>
      <button>{{ $t('button.submit') }}</button>
    </template>
    ```
4. **Use in TypeScript** with the i18next instance:
    ```typescript
    import i18next from 'i18next'

    const message = i18next.t('welcome.title')
    ```

### 3. Placeholders and dynamic content

Use placeholders to insert dynamic values into translations:

**`en.json`**:
```json
{
  "greeting": "Hello {name}, you have {count} new messages."
}
```

**Vue template**:
```vue
<template>
  <p>{{ $t('greeting', { name: 'Max', count: 5 }) }}</p>
</template>
```

## Page management

The frontend is a Vue.js application using `Vue Router` for navigation.

### 1. Adding a new page

1. **Create a Vue component** under `frontend/src/routes/` (or a suitable subfolder).
   Example: `frontend/src/routes/AboutPage.vue`
    ```vue
    <template>
      <div class="about-page">
        <h1>{{ $t('about.title') }}</h1>
        <p>{{ $t('about.content') }}</p>
      </div>
    </template>

    <script setup lang="ts">
    </script>

    <style scoped>
    /* Scoped styles for the AboutPage */
    </style>
    ```

2. **Configure the route** in `frontend/src/router/index.ts`.
   Import your component (prefer lazy loading) and add a route entry:
    ```typescript
    const AboutPage = () => import('@/routes/AboutPage.vue')

    // inside routes array:
    {
      path: '/about',
      name: 'About',
      component: AboutPage,
    }
    ```

3. **Add navigation** (optional): add a `router-link` in the navigation drawer or header:
    ```vue
    <router-link to="/about">{{ $t('nav.about') }}</router-link>
    ```

4. **Add translations** for the new page's title and content in all `frontend/src/locales/*.json` files.

### 2. Editing an existing page

1. **Locate the component** — page components live in `frontend/src/routes/`, reusable components in `frontend/src/components/`.
2. **Edit the template, script, or styles** as needed. Always use i18n keys for user-facing text.
3. **Update translations** — ensure the corresponding entries in the `frontend/src/locales/*.json` files are kept in sync.