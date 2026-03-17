# MoviemetaDb UI

A minimal React UI for the MoviemetaDb API.

## Run locally

```bash
cd ui
npm install
npm run dev
```

The app will run on `http://localhost:5173` by default.

### Configuring API base URL

You can override the API base URL by setting `VITE_API_BASE` in your environment:

```bash
VITE_API_BASE=http://localhost:8000 npm run dev
```

### Authentication

If the API requires a bearer token, set it in the input field at the top of the app.
