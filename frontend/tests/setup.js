import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, resolve } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const html = readFileSync(resolve(__dirname, '../index.html'), 'utf8');
// Strip out the module script tag to avoid double loading; keep the rest of the markup.
const cleanHtml = html.replace(/<script type="module" src="src\/app\.js"><\/script>/, '');
document.body.innerHTML = cleanHtml;

// Provide minimal window.matchMedia mock if needed
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {}
  })
});

// Mock fetch globally
let fetchCalls = [];
let fetchResponse = null;

global.fetch = async (url, options) => {
  fetchCalls.push({ url, options });
  if (fetchResponse) {
    const res = fetchResponse;
    fetchResponse = null;
    return res;
  }
  return {
    ok: true,
    status: 200,
    json: async () => ({})
  };
};

global.getFetchCalls = () => fetchCalls;
global.clearFetchCalls = () => { fetchCalls = []; };
global.setFetchResponse = (res) => { fetchResponse = res; };
