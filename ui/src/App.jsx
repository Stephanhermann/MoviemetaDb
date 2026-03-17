import { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function buildHeaders(apiKey) {
  const headers = { 'Content-Type': 'application/json' };
  if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
  return headers;
}

export default function App() {
  const [movies, setMovies] = useState([]);
  const [title, setTitle] = useState('');
  const [year, setYear] = useState('');
  const [rating, setRating] = useState('');
  const [apiKey, setApiKey] = useState(localStorage.getItem('MOVIEMETADB_API_KEY') || '');
  const [error, setError] = useState(null);

  const headers = useMemo(() => buildHeaders(apiKey), [apiKey]);

  const fetchMovies = async () => {
    setError(null);
    try {
      const resp = await fetch(`${API_BASE}/movies`, { headers });
      if (!resp.ok) throw new Error(await resp.text());
      setMovies(await resp.json());
    } catch (err) {
      setError(String(err));
    }
  };

  useEffect(() => {
    fetchMovies();
  }, [apiKey]);

  const addMovie = async () => {
    setError(null);
    try {
      const body = JSON.stringify({ title, year: Number(year), rating: Number(rating) });
      const resp = await fetch(`${API_BASE}/movies`, { method: 'POST', headers, body });
      if (!resp.ok) throw new Error(await resp.text());
      setTitle('');
      setYear('');
      setRating('');
      await fetchMovies();
    } catch (err) {
      setError(String(err));
    }
  };

  const saveApiKey = () => {
    localStorage.setItem('MOVIEMETADB_API_KEY', apiKey);
    fetchMovies();
  };

  return (
    <div className="app">
      <header>
        <h1>MoviemetaDb</h1>
        <p>A simple UI for the MoviemetaDb API.</p>
      </header>
      <section className="auth">
        <label>
          API key (optional):
          <input value={apiKey} onChange={(e) => setApiKey(e.target.value)} placeholder="Bearer token" />
        </label>
        <button onClick={saveApiKey}>Save key</button>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="form">
        <div>
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Year
            <input value={year} onChange={(e) => setYear(e.target.value)} />
          </label>
        </div>
        <div>
          <label>
            Rating
            <input value={rating} onChange={(e) => setRating(e.target.value)} />
          </label>
        </div>
        <button onClick={addMovie}>Add movie</button>
      </section>

      <section className="list">
        <h2>Movies</h2>
        {movies.length === 0 ? (
          <p>No movies yet.</p>
        ) : (
          <ul>
            {movies.map((m) => (
              <li key={`${m.title}-${m.year}`}>
                <strong>{m.title}</strong> ({m.year}) — rating: {m.rating}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
